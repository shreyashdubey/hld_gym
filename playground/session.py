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
        # Same story: bound by build_playground_worker once the TTS service
        # exists, so the session-cap task in server.py can make the coach
        # handover audible without reaching into pipelines.py's locals.
        self.tts = None
        self._started_at: float | None = None

    def switch_to_coach(self) -> None:
        self.mode = "coach"

    def tts_voice(self) -> str:
        return self.config.coach_voice if self.mode == "coach" else self.config.interviewer_voice

    def system_messages(self) -> list[dict]:
        persona = coach_prompt() if self.mode == "coach" else interviewer_prompt()
        messages = [{"role": "system", "content": persona}, *self.board.messages()]
        # last_change_summary is a computed property, not accumulated state --
        # it always reflects the diff between the two most recent board
        # updates, so this never grows across pushes any more than the board
        # message itself does. Empty (and skipped) on the first update, when
        # everything is new and nothing has "just" changed -- BoardContext
        # already encodes that. The design is board-as-diffable-graph, not
        # board-as-screenshot; a coach that never hears what just changed is
        # the screenshot we said we weren't building.
        summary = self.board.last_change_summary
        if summary:
            messages.append({"role": "system", "content": f"Since the last update: {summary}."})
        return messages

    def start(self, now: float) -> None:
        """Marks the clock start. Takes `now` as an argument rather than
        reading time.monotonic() itself, same reason config is a dataclass
        of plain values, not a magic-computed one: a Session under test
        should never depend on when the test happens to run."""
        self._started_at = now

    def remaining_secs(self, now: float) -> float:
        """Never negative -- a caller doing `remaining <= handover_threshold`
        math shouldn't have to clamp it themselves. config.session_cap_secs
        before start() is called, since nothing has been spent yet."""
        if self._started_at is None:
            return self.config.session_cap_secs
        return max(0.0, self.config.session_cap_secs - (now - self._started_at))

    def expired(self, now: float) -> bool:
        return self.remaining_secs(now) <= 0

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
