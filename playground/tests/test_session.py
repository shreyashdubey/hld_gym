import unittest

from playground.config import VoiceConfig
from playground.session import Session


class TestSession(unittest.TestCase):
    def setUp(self):
        self.s = Session(VoiceConfig())

    def test_starts_as_the_interviewer(self):
        self.assertEqual(self.s.mode, "interview")

    def test_the_interviewer_context_has_no_answer_key(self):
        from playground import rep

        text = " ".join(m["content"] for m in self.s.system_messages())
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], text)

    def test_switching_admits_the_answer_key(self):
        from playground import rep

        self.s.switch_to_coach()
        text = " ".join(m["content"] for m in self.s.system_messages())
        for probe in rep.PROBES:
            self.assertIn(probe["a"], text)

    def test_switching_changes_the_voice(self):
        """The handoff has to be audible or it reads as the interviewer going
        soft rather than as a change of role."""
        before = self.s.tts_voice()
        self.s.switch_to_coach()
        self.assertNotEqual(before, self.s.tts_voice())

    def test_switching_twice_is_harmless(self):
        self.s.switch_to_coach()
        self.s.switch_to_coach()
        self.assertEqual(self.s.mode, "coach")

    def test_the_board_rides_along_in_both_modes(self):
        self.s.board.update({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        self.assertIn("Cache", " ".join(m["content"] for m in self.s.system_messages()))
        self.s.switch_to_coach()
        self.assertIn("Cache", " ".join(m["content"] for m in self.s.system_messages()))

    def test_the_coach_never_reverts_to_interviewer(self):
        self.s.switch_to_coach()
        self.assertEqual(self.s.mode, "coach")


class _FakeLLMContext:
    """Stands in for pipecat's LLMContext. Records what got pushed, without
    dragging pipecat's message-schema types into a unit test."""

    def __init__(self):
        self.messages = None

    def set_messages(self, messages):
        self.messages = messages


class TestSessionContextBinding(unittest.TestCase):
    """Task 11's server.py has two callers that must reach the model through
    exactly one path: the board-update handler and the end_round handler.
    Session owns the LLMContext and exposes push_context() as that one path,
    so neither caller has to know how the context gets assembled."""

    def setUp(self):
        self.s = Session(VoiceConfig())
        self.ctx = _FakeLLMContext()

    def test_push_context_before_a_context_is_bound_does_not_raise(self):
        self.s.push_context()  # no context bound yet -- must not crash

    def test_push_context_sends_system_messages_to_the_bound_context(self):
        self.s.context = self.ctx
        self.s.push_context()
        self.assertEqual(self.ctx.messages, self.s.system_messages())

    def test_push_context_after_switching_carries_the_answer_key_into_the_bound_context(self):
        from playground import rep

        self.s.context = self.ctx
        self.s.switch_to_coach()
        self.s.push_context()
        text = " ".join(m["content"] for m in self.ctx.messages)
        for probe in rep.PROBES:
            self.assertIn(probe["a"], text)

    def test_push_context_after_a_board_update_carries_the_board_into_the_bound_context(self):
        self.s.context = self.ctx
        self.s.board.update({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        self.s.push_context()
        text = " ".join(m["content"] for m in self.ctx.messages)
        self.assertIn("Cache", text)


if __name__ == "__main__":
    unittest.main()
