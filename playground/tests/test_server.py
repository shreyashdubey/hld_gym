import asyncio
import os
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from playground.config import VoiceConfig
from playground.server import (
    OfferRequest,
    _Session,
    _allowed_origins,
    _apply_board_message,
    _enforce_cap,
    _extract_board_graph,
    _sessions,
    offer,
)
from playground.session import Session


class TestHealth(unittest.TestCase):
    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-secret-do-not-leak"
        from playground.server import app

        self.client = TestClient(app)

    def test_health_reports_key_loaded(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True, "key_loaded": True})

    def test_health_never_echoes_the_key(self):
        r = self.client.get("/health")
        self.assertNotIn("sk-secret-do-not-leak", r.text)


class TestOffer(unittest.TestCase):
    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-secret-do-not-leak"
        from playground.server import app

        self.client = TestClient(app)

    def test_malformed_body_is_a_4xx_not_a_500(self):
        """A bare dict indexed with request["sdp"] turns a missing field into
        an unhandled KeyError -> 500. The Pydantic model must catch it first."""
        r = self.client.post("/api/offer", json={"type": "offer"})  # no "sdp"
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)

    def test_an_unrecognised_mode_is_a_4xx_not_a_silent_fallback(self):
        """A typo'd or stale ?mode= must not silently behave like dictation --
        that's a mute interviewer and no error. mode is typed Literal, so
        FastAPI/Pydantic reject it before the handler body (and the fake SDP
        below) is ever touched."""
        r = self.client.post("/api/offer?mode=bogus", json={"sdp": "x", "type": "offer"})
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)


class TestAllowedOrigins(unittest.TestCase):
    """CORS started as allow_origins="*" and was narrowed after this build's
    own verification showed why: a wildcard lets any page a visitor has open
    spend their OpenAI quota through a locally-running service, not just
    sell's. These two properties -- a safe default, and an override that
    actually overrides -- are what stop that regressing silently."""

    def test_defaults_to_the_two_localhost_dev_origins(self):
        self.assertEqual(
            _allowed_origins({}),
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        )

    def test_env_override_replaces_the_default_entirely(self):
        origins = _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "https://hld-gym.vercel.app"})
        self.assertEqual(origins, ["https://hld-gym.vercel.app"])

    def test_env_override_is_comma_separated_and_trims_whitespace(self):
        origins = _allowed_origins(
            {"PLAYGROUND_ALLOWED_ORIGINS": "https://a.example, https://b.example ,,"}
        )
        self.assertEqual(origins, ["https://a.example", "https://b.example"])

    def test_a_bare_wildcard_is_rejected_not_silently_widened(self):
        """"*" degrades the whole guard back to allow-everything -- garbage
        and stray whitespace/commas all fail safe to a smaller list, but this
        one value is the standard "allow everything" convention and the
        first thing anyone reaching for it would type, so it must raise
        rather than pass through to CORSMiddleware verbatim."""
        with self.assertRaises(ValueError):
            _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "*"})

    def test_a_wildcard_mixed_with_real_origins_is_also_rejected(self):
        with self.assertRaises(ValueError):
            _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "http://localhost:3000,*"})


class TestExtractBoardGraph(unittest.TestCase):
    """_extract_board_graph is the module-level pure parser board messages go
    through -- hoisted out specifically so it (and the shape it expects) can
    be pinned down without a live WebRTC connection."""

    def test_extracts_the_graph_from_a_well_formed_board_message(self):
        message = {
            "type": "client-message",
            "data": {"t": "board", "d": {"graph": {"nodes": [], "edges": []}}},
        }
        self.assertEqual(_extract_board_graph(message), {"nodes": [], "edges": []})

    def test_none_for_a_non_client_message(self):
        self.assertIsNone(_extract_board_graph({"type": "something-else"}))

    def test_none_for_a_client_message_of_a_different_type(self):
        message = {"type": "client-message", "data": {"t": "not-board", "d": {}}}
        self.assertIsNone(_extract_board_graph(message))

    def test_none_when_data_is_missing_or_not_a_dict(self):
        self.assertIsNone(_extract_board_graph({"type": "client-message"}))
        self.assertIsNone(_extract_board_graph({"type": "client-message", "data": "nope"}))

    def test_none_when_the_payload_is_missing_or_not_a_dict(self):
        self.assertIsNone(
            _extract_board_graph({"type": "client-message", "data": {"t": "board", "d": "nope"}})
        )
        self.assertIsNone(_extract_board_graph({"type": "client-message", "data": {"t": "board"}}))

    def test_none_when_the_graph_key_is_missing_or_not_a_dict(self):
        """The exact key is "graph", not e.g. "board" -- catches a handler
        that reads the wrong key from an otherwise well-formed envelope."""
        self.assertIsNone(
            _extract_board_graph({"type": "client-message", "data": {"t": "board", "d": {}}})
        )
        self.assertIsNone(
            _extract_board_graph(
                {"type": "client-message", "data": {"t": "board", "d": {"graph": "nope"}}}
            )
        )

    def test_none_for_a_completely_unstructured_message(self):
        self.assertIsNone(_extract_board_graph("not even a dict"))
        self.assertIsNone(_extract_board_graph(None))


class _FakeContext:
    """Stands in for pipecat's LLMContext -- see test_session.py's version,
    duplicated here rather than imported so this test module doesn't reach
    into another test module's internals."""

    def __init__(self):
        self.messages = []

    def set_messages(self, messages):
        self.messages = messages

    def transform_messages(self, transform):
        self.set_messages(transform(self.messages))


class TestApplyBoardMessage(unittest.TestCase):
    """_apply_board_message is the second (and last) caller of
    Session.push_context() -- see test_session.py's TestSessionContextBinding
    for the first. Both must be independently provable, since a board update
    that never reaches the model fails silently: the client's UI still shows
    the drawing, only the interviewer stays blind to it."""

    def setUp(self):
        self.session = Session(VoiceConfig())
        self.session.context = _FakeContext()

    def _board_message(self, graph):
        return {"type": "client-message", "data": {"t": "board", "d": {"graph": graph}}}

    def test_a_well_formed_board_message_updates_the_board_and_pushes_context(self):
        graph = {"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0}
        _apply_board_message(self.session, self._board_message(graph))
        text = " ".join(m["content"] for m in self.session.context.messages)
        self.assertIn("Cache", text)

    def test_a_malformed_message_leaves_a_good_board_untouched(self):
        good = self._board_message({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        _apply_board_message(self.session, good)
        _apply_board_message(self.session, {"type": "client-message", "data": {"t": "board", "d": {}}})
        text = " ".join(m["content"] for m in self.session.board.messages())
        self.assertIn("Cache", text)

    def test_an_unrelated_message_does_not_touch_the_board_or_the_context(self):
        _apply_board_message(self.session, {"type": "server-message"})
        self.assertEqual(self.session.board.messages(), [])
        self.assertEqual(self.session.context.messages, [])


class _FakeConnection:
    """Stands in for SmallWebRTCConnection -- same house style as
    _FakeContext/_FakeTTS/_FakeConnection in test_pipelines.py. offer()
    constructs SmallWebRTCConnection() by name from its own module
    namespace, so patching playground.server.SmallWebRTCConnection to
    return this is enough to drive the connection-leak guard directly: no
    TestClient, no aiortc, no real SDP handshake."""

    def __init__(self):
        self.disconnect_calls = 0

    async def initialize(self, sdp, type):
        pass

    async def disconnect(self):
        self.disconnect_calls += 1

    def event_handler(self, name):
        def decorator(fn):
            return fn

        return decorator

    def add_event_handler(self, name, handler):
        pass

    def get_answer(self):
        return {"pc_id": "fake-pc-id"}


class TestConnectionLeakGuard(unittest.TestCase):
    """Both guards in offer() exist to stop a leaked peer connection
    holding an OpenAI audio stream open, which bills per minute. Prove it
    directly rather than trusting the diff -- this build has repeatedly
    shown untested code regresses silently."""

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-secret-do-not-leak"
        self.fake = _FakeConnection()
        self.request = OfferRequest(sdp="x", type="offer")

    def test_a_config_failure_after_initialize_closes_the_connection(self):
        """VoiceConfig.from_env() raises on a malformed PLAYGROUND_* env
        var or the dictation-threshold/distinct-voice invariants -- after
        the connection is already initialize()d. The guard must still tear
        it down."""
        with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
            with patch.object(VoiceConfig, "from_env", side_effect=ValueError("bad env")):
                with self.assertRaises(ValueError):
                    asyncio.run(offer(self.request))
        self.assertEqual(self.fake.disconnect_calls, 1)

    def test_a_cancellation_during_the_worker_build_closes_the_connection_and_propagates(self):
        """asyncio.CancelledError is a BaseException, not an Exception --
        loading SmartTurn plus Silero is exactly the slow window where a
        client giving up mid-request is most likely. The guard must still
        tear the connection down, and must not swallow the cancellation."""
        with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
            with patch(
                "playground.server.build_dictation_worker",
                side_effect=asyncio.CancelledError(),
            ):
                with self.assertRaises(asyncio.CancelledError):
                    asyncio.run(offer(self.request))
        self.assertEqual(self.fake.disconnect_calls, 1)


class _FakeCapRunner:
    def __init__(self):
        self.cancel_calls = []
        self.cancelled_at = None

    async def cancel(self, reason=None):
        self.cancel_calls.append(reason)
        self.cancelled_at = time.monotonic()


class _FakeCapWorker:
    def __init__(self):
        self.queued = []
        self.queued_at = None

    async def queue_frames(self, frames):
        self.queued.append(list(frames))
        if self.queued_at is None:
            self.queued_at = time.monotonic()


class _FakeCapConnection:
    def __init__(self, pc_id):
        self.pc_id = pc_id


class _FakeTTS:
    """Same double as test_pipelines.py's -- duplicated rather than
    imported so this test module doesn't reach into another one's
    internals."""

    def __init__(self):
        self.voice = None

    async def set_voice(self, voice):
        self.voice = voice


class TestEnforceCap(unittest.TestCase):
    """_enforce_cap is the scheduling half of the session cap -- Session's
    own start/remaining_secs/expired are pure and covered by test_cap.py,
    but the polling loop that calls them is where the real bug in this
    build lived (a flat sleep interval that could step clean over a short
    handover window). Session's clock is real time.monotonic() here, not a
    fake -- that bug is exactly the kind of scheduling defect a mocked clock
    would never exercise -- so these run for real, for about a second each,
    against a real short cap rather than the 12-minute default."""

    def _run(self, session):
        session.tts = _FakeTTS()
        session.start(now=time.monotonic())
        connection = _FakeCapConnection(f"pc-{id(session)}")
        runner = _FakeCapRunner()
        worker = _FakeCapWorker()
        _sessions[connection.pc_id] = _Session(connection=connection, runner=runner, task=None)
        asyncio.run(_enforce_cap(connection, worker, session))
        return worker, runner

    def test_the_handover_happens_before_the_cut(self):
        session = Session(VoiceConfig(session_cap_secs=1.0))
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(len(worker.queued), 1)
        self.assertEqual(runner.cancel_calls, ["connection ended"])
        self.assertLess(worker.queued_at, runner.cancelled_at)

    def test_a_very_short_cap_still_gets_a_handover_not_a_bare_cut(self):
        """The regression test for the bug this task found: a flat 1s poll
        ceiling could step clean over a handover window narrower than a
        second and reach expiry having never handed over at all."""
        session = Session(VoiceConfig(session_cap_secs=0.5))
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(len(worker.queued), 1)

    def test_a_session_already_in_coach_mode_gets_no_second_run_frame(self):
        """end_round switches a session to coach independently of the cap,
        and nothing ends the connection when it does -- reaching the
        handover mark already in coach mode is routine, not exotic. The cap
        must not force a second, unprompted completion with no user turn
        behind it: the coach interjecting out of nowhere mid-conversation."""
        session = Session(VoiceConfig(session_cap_secs=1.0))
        session.switch_to_coach()  # end_round already ran, before the cap fired
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(worker.queued, [])
        self.assertEqual(runner.cancel_calls, ["connection ended"])


if __name__ == "__main__":
    unittest.main()
