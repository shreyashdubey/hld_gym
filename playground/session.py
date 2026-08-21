"""Two modes, one variable. Not a state machine — two states are not a machine.

The switch is one-way on purpose: a coach that can turn back into an
interviewer mid-explanation is just an inconsistent voice.
"""

from playground.board import BoardContext
from playground.config import VoiceConfig
from playground.personas import coach_prompt, interviewer_prompt


class Session:
    def __init__(self, config: VoiceConfig) -> None:
        self.config = config
        self.mode = "interview"
        self.board = BoardContext()
        # Bound by whoever builds the pipeline, once the LLMContext exists.
        # Every caller that changes mode or board state then calls
        # push_context() -- the one place that knows how the context is
        # assembled, so neither caller (the end_round handler in
        # pipelines.py, the board-update handler in server.py) has to.
        self.context = None

    def switch_to_coach(self) -> None:
        self.mode = "coach"

    def tts_voice(self) -> str:
        return self.config.coach_voice if self.mode == "coach" else self.config.interviewer_voice

    def system_messages(self) -> list[dict]:
        persona = coach_prompt() if self.mode == "coach" else interviewer_prompt()
        return [{"role": "system", "content": persona}, *self.board.messages()]

    def push_context(self) -> None:
        """Refresh the system messages (persona + board) at the front of the
        bound LLMContext, in place -- everything else (the user/assistant
        turns, and any in-flight tool_calls/tool pair) survives untouched.

        set_messages() replaces the *whole* list; calling it with just
        system_messages() would erase the conversation on every board update
        and again at handover, which is the one thing a coach who is meant to
        "work from what they actually drew and said" cannot survive. A no-op
        until a context is bound, so calling it early (or from a test that
        never binds one) doesn't crash."""
        if self.context is None:
            return
        fresh = self.system_messages()

        def _refresh(msgs: list) -> list:
            rest = [m for m in msgs if not (isinstance(m, dict) and m.get("role") == "system")]
            return fresh + rest

        self.context.transform_messages(_refresh)
