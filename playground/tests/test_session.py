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

    def test_the_interviewer_only_has_end_round(self):
        """An interviewer that can draw can show the candidate the structure
        the round exists to measure -- the same class of bug as the
        interviewer holding the answer key."""
        names = {t.name for t in self.s.tools().standard_tools}
        self.assertEqual(names, {"end_round"})

    def test_the_coach_only_has_draw_diagram(self):
        self.s.switch_to_coach()
        names = {t.name for t in self.s.tools().standard_tools}
        self.assertEqual(names, {"draw_diagram"})

    def test_the_board_rides_along_in_both_modes(self):
        self.s.board.update({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        self.assertIn("Cache", " ".join(m["content"] for m in self.s.system_messages()))
        self.s.switch_to_coach()
        self.assertIn("Cache", " ".join(m["content"] for m in self.s.system_messages()))

    def test_the_coach_never_reverts_to_interviewer(self):
        self.s.switch_to_coach()
        self.assertEqual(self.s.mode, "coach")

    def test_no_change_summary_message_on_the_first_board_update(self):
        """The first update has no previous graph to diff against --
        everything is new, nothing has "just" changed, and BoardContext
        already encodes that as an empty last_change_summary. No summary
        message should appear at all, not an empty one."""
        self.s.board.update({"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0})
        self.assertEqual(len(self.s.system_messages()), 2)  # persona + board, no summary yet

    def test_a_second_board_update_adds_the_change_summary_to_the_context(self):
        """The whole point of reading the board as a diffable graph rather
        than a screenshot: what changed is the signal a coach reacts to."""
        self.s.board.update({"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0})
        self.s.board.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
                "edges": [],
                "unreadable": 0,
            }
        )
        messages = self.s.system_messages()
        self.assertEqual(len(messages), 3)  # persona + board + change summary
        self.assertIn("added Cache", messages[-1]["content"])

    def test_the_change_summary_does_not_accumulate_across_pushes(self):
        """Every call to system_messages() must reflect the diff between the
        two most recent updates only -- not grow with each call, the way the
        board message itself never grows across 200 updates."""
        self.s.board.update({"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0})
        self.s.board.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
                "edges": [],
                "unreadable": 0,
            }
        )
        first_count = len(self.s.system_messages())
        second_count = len(self.s.system_messages())
        third_count = len(self.s.system_messages())
        self.assertEqual(first_count, second_count)
        self.assertEqual(second_count, third_count)


class _FakeLLMContext:
    """Stands in for pipecat's LLMContext -- just enough of the real API
    (transform_messages built on set_messages, exactly like the real
    LLMContext) to prove push_context() drives it correctly, without dragging
    pipecat's message-schema types into a unit test. set_tools records what
    it was given rather than validating it, same reasoning."""

    def __init__(self, messages=None):
        self.messages = messages or []
        self.tools = None

    def set_messages(self, messages):
        self.messages = messages

    def transform_messages(self, transform):
        self.set_messages(transform(self.messages))

    def set_tools(self, tools):
        self.tools = tools


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

    def test_push_context_preserves_the_conversation(self):
        """The critical property: set_messages() replaces everything, so
        push_context() must refresh the system messages in place rather than
        wipe the user/assistant turns sitting behind them. A board update
        mid-round -- which the client sends on every debounced graph change --
        must not give the interviewer amnesia, and the coach must still have
        what the candidate actually said to work from."""
        self.ctx.messages = [
            {"role": "system", "content": "stale persona"},
            {"role": "user", "content": "I'd cache the read path"},
            {"role": "assistant", "content": "Why?"},
        ]
        self.s.context = self.ctx
        self.s.push_context()
        roles = [m["role"] for m in self.ctx.messages]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)
        self.assertIn(
            "I'd cache the read path", " ".join(m.get("content", "") for m in self.ctx.messages)
        )
        # The stale system message is gone, replaced by the current one --
        # not merely appended alongside it.
        self.assertNotIn("stale persona", " ".join(m.get("content", "") for m in self.ctx.messages))
        self.assertEqual(sum(1 for r in roles if r == "system"), len(self.s.system_messages()))

    def test_push_context_after_switching_carries_the_answer_key_into_the_bound_context(self):
        from playground import rep

        self.s.context = self.ctx
        self.s.switch_to_coach()
        self.s.push_context()
        text = " ".join(m["content"] for m in self.ctx.messages)
        for probe in rep.PROBES:
            self.assertIn(probe["a"], text)

    def test_push_context_installs_end_round_only_before_any_switch(self):
        """An interviewer that can draw can show the candidate the structure
        the round exists to measure. Ordering: context bound while still in
        interview mode -- the state build_playground_worker is always in at
        construction."""
        self.s.context = self.ctx
        self.s.push_context()
        names = {t.name for t in self.ctx.tools.standard_tools}
        self.assertEqual(names, {"end_round"})

    def test_push_context_narrows_to_draw_diagram_after_switching(self):
        """Same property, the other ordering: context already bound, then a
        live switch_to_coach() -- the end_round handler's and the cap
        handover's actual call order. Both handler call sites get this for
        free through push_context(); this is the property they rely on."""
        self.s.context = self.ctx
        self.s.push_context()  # interviewer's tools installed first, as above
        self.s.switch_to_coach()
        self.s.push_context()
        names = {t.name for t in self.ctx.tools.standard_tools}
        self.assertEqual(names, {"draw_diagram"})
        self.assertNotIn("end_round", names)

    def test_push_context_after_a_board_update_carries_the_board_into_the_bound_context(self):
        self.s.context = self.ctx
        self.s.board.update({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        self.s.push_context()
        text = " ".join(m["content"] for m in self.ctx.messages)
        self.assertIn("Cache", text)

    def test_push_context_after_a_second_board_update_carries_the_change_summary(self):
        """The board message alone is a snapshot; the change summary is the
        memory of the previous frame. Both must reach the model, not just
        the one BoardContext already covers with its own tests."""
        self.s.context = self.ctx
        self.s.board.update({"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0})
        self.s.push_context()
        self.s.board.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
                "edges": [],
                "unreadable": 0,
            }
        )
        self.s.push_context()
        text = " ".join(m["content"] for m in self.ctx.messages)
        self.assertIn("added Cache", text)


if __name__ == "__main__":
    unittest.main()
