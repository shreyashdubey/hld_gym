"""Unit tests for the two function-call handlers build_playground_worker
wires up. Both are module-level (bound via functools.partial) precisely so
they can be driven directly against stubs here, instead of only being
exercised implicitly by constructing the whole pipeline."""

import asyncio
import os
import unittest
from types import SimpleNamespace

from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregator
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from playground.config import VoiceConfig
from playground.pipelines import _draw_diagram, _end_round, build_playground_worker
from playground.session import Session


def _flatten(processor):
    """Compound processors (Pipeline, PipelineWorker's own wrapping
    pipeline) expose their children via .processors; leaves return []. Walk
    the whole tree so a nested worker/pipeline structure doesn't hide what's
    actually wired up."""
    children = getattr(processor, "processors", None)
    if not children:
        return [processor]
    flat = []
    for child in children:
        flat.extend(_flatten(child))
    return flat


class _FakeContext:
    """Same double as test_session.py / test_server.py -- transform_messages
    built on set_messages, exactly like the real LLMContext. set_tools just
    records what it was given, so a test can check which tool push_context()
    installed without a real ToolsSchema/FunctionSchema round-trip."""

    def __init__(self):
        self.messages = []
        self.tools = None

    def set_messages(self, messages):
        self.messages = messages

    def transform_messages(self, transform):
        self.set_messages(transform(self.messages))

    def set_tools(self, tools):
        self.tools = tools


class _FakeTTS:
    def __init__(self):
        self.voice = None

    async def set_voice(self, voice):
        self.voice = voice


class _FakeConnection:
    def __init__(self):
        self.sent = []

    def send_app_message(self, message):
        self.sent.append(message)


def _params(arguments=None):
    """A stub matching the two FunctionCallParams attributes both handlers
    use: arguments and result_callback."""
    results = []

    async def result_callback(result):
        results.append(result)

    return SimpleNamespace(arguments=arguments or {}, result_callback=result_callback), results


class TestEndRound(unittest.TestCase):
    def setUp(self):
        self.session = Session(VoiceConfig())
        self.session.context = _FakeContext()
        self.tts = _FakeTTS()

    def test_switches_the_session_to_coach_mode(self):
        params, _ = _params()
        asyncio.run(_end_round(self.session, self.tts, params))
        self.assertEqual(self.session.mode, "coach")

    def test_re_voices_the_tts_service(self):
        """The handoff has to be audible -- a dropped set_voice() call means
        the coach sounds identical to the interviewer."""
        params, _ = _params()
        asyncio.run(_end_round(self.session, self.tts, params))
        self.assertEqual(self.tts.voice, self.session.config.coach_voice)
        self.assertNotEqual(self.tts.voice, self.session.config.interviewer_voice)

    def test_pushes_the_switched_context_so_the_answer_key_is_admitted(self):
        from playground import rep

        params, _ = _params()
        asyncio.run(_end_round(self.session, self.tts, params))
        text = " ".join(m["content"] for m in self.session.context.messages)
        for probe in rep.PROBES:
            self.assertIn(probe["a"], text)

    def test_reports_ok_through_the_result_callback(self):
        params, results = _params()
        asyncio.run(_end_round(self.session, self.tts, params))
        self.assertEqual(results, [{"ok": True}])

    def test_the_handover_installs_the_drawing_tool_and_drops_end_round(self):
        """An interviewer that can draw can show the candidate the structure
        the round exists to measure -- the same class of bug as the
        interviewer holding the answer key. push_context() (called by
        _end_round via switch_to_coach()) must narrow the tool list to
        draw_diagram alone, not just add it alongside end_round."""
        params, _ = _params()
        asyncio.run(_end_round(self.session, self.tts, params))
        names = {t.name for t in self.session.context.tools.standard_tools}
        self.assertEqual(names, {"draw_diagram"})


class TestDrawDiagram(unittest.TestCase):
    def test_sends_the_topology_wrapped_in_the_rtvi_envelope(self):
        connection = _FakeConnection()
        topology = {"nodes": [{"id": "a", "label": "Cache"}], "edges": []}
        params, results = _params(arguments=topology)

        asyncio.run(_draw_diagram(connection, params))

        self.assertEqual(len(connection.sent), 1)
        sent = connection.sent[0]
        self.assertEqual(sent["label"], "rtvi-ai")
        self.assertEqual(sent["type"], "server-message")
        self.assertEqual(sent["data"], {"type": "draw", "topology": topology})
        self.assertEqual(results, [{"drawn": True}])


class TestSingleVADSource(unittest.TestCase):
    """LLMUserAggregatorParams(vad_analyzer=...) would make the aggregator
    build its own VADController on top of the audio the pipeline's own
    _vad() VADProcessor stage already analyzes -- a second Silero instance,
    and a second billed OpenAI transcription per utterance (SegmentedSTTService
    runs run_stt() on every VADUserStoppedSpeakingFrame it sees, and two VAD
    sources means two such frames per utterance). That regression is
    invisible in the rest of the suite -- everything still passes, turn-taking
    still works, only the bill doubles -- so it needs its own guard."""

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"

    def test_the_aggregator_owns_no_vad_controller_of_its_own(self):
        worker, _ = build_playground_worker(SmallWebRTCConnection(), VoiceConfig())
        aggregators = [p for p in _flatten(worker.pipeline) if isinstance(p, LLMUserAggregator)]
        self.assertEqual(len(aggregators), 1, "expected exactly one LLMUserAggregator")
        self.assertIsNone(aggregators[0]._vad_controller)


class TestToolModeSplit(unittest.TestCase):
    """An interviewer that can draw can show the candidate the structure the
    round exists to measure -- the same class of bug as the interviewer
    holding the answer key. Session.tools() is the one place the tool list
    is decided (see playground/session.py); this exercises it through the
    real build_playground_worker + real LLMContext, both orderings: fresh
    build (interview mode) and after a live switch to coach."""

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"

    def test_a_freshly_built_worker_gives_the_interviewer_end_round_only(self):
        _, session = build_playground_worker(SmallWebRTCConnection(), VoiceConfig())
        names = {t.name for t in session.context.tools.standard_tools}
        self.assertEqual(names, {"end_round"})
        self.assertNotIn("draw_diagram", names)

    def test_switching_to_coach_installs_draw_diagram_and_drops_end_round(self):
        _, session = build_playground_worker(SmallWebRTCConnection(), VoiceConfig())
        session.switch_to_coach()
        session.push_context()
        names = {t.name for t in session.context.tools.standard_tools}
        self.assertEqual(names, {"draw_diagram"})
        self.assertNotIn("end_round", names)


if __name__ == "__main__":
    unittest.main()
