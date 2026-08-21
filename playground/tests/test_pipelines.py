"""Unit tests for the two function-call handlers build_playground_worker
wires up. Both are module-level (bound via functools.partial) precisely so
they can be driven directly against stubs here, instead of only being
exercised implicitly by constructing the whole pipeline."""

import asyncio
import unittest
from types import SimpleNamespace

from playground.config import VoiceConfig
from playground.pipelines import _draw_diagram, _end_round
from playground.session import Session


class _FakeContext:
    """Same double as test_session.py / test_server.py -- transform_messages
    built on set_messages, exactly like the real LLMContext."""

    def __init__(self):
        self.messages = []

    def set_messages(self, messages):
        self.messages = messages

    def transform_messages(self, transform):
        self.set_messages(transform(self.messages))


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


if __name__ == "__main__":
    unittest.main()
