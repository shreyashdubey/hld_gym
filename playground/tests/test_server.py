import os
import unittest

from fastapi.testclient import TestClient

from playground.config import VoiceConfig
from playground.server import _apply_board_message, _extract_board_graph
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


if __name__ == "__main__":
    unittest.main()
