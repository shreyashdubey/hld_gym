"""Turn-detection knobs, in one place, because none of them survive contact
with a real microphone in a real room at their library defaults."""

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass
class VoiceConfig:
    """Every field here is tuned by ear against real sessions, not chosen."""

    # Silero VAD.
    confidence: float = 0.7
    start_secs: float = 0.2
    stop_secs: float = 0.8
    min_volume: float = 0.6

    # Dictation runs the same VAD, waiting longer. See the test for why.
    dictation_stop_secs: float = 2.0

    # Voice bills by the minute, so the session ends whether or not anyone
    # remembers to stop it. Announced at the start, never enforced silently.
    session_cap_secs: float = 12 * 60

    # OpenAI TTS voices. Different on purpose — the handoff must be audible.
    interviewer_voice: str = "onyx"
    coach_voice: str = "shimmer"

    def __post_init__(self) -> None:
        if self.dictation_stop_secs <= self.stop_secs:
            raise ValueError(
                "dictation_stop_secs must exceed stop_secs: someone drawing "
                f"pauses longer than someone talking (got {self.dictation_stop_secs} "
                f"<= {self.stop_secs})"
            )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "VoiceConfig":
        src = os.environ if env is None else env
        prefix = "PLAYGROUND_"
        kwargs = {}
        for f in cls.__dataclass_fields__.values():
            raw = src.get(prefix + f.name.upper())
            if raw is None:
                continue
            kwargs[f.name] = float(raw) if f.type is float else raw
        return cls(**kwargs)
