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

    # Playground model names. Unverified against the live API — no key to
    # check them with — so each is overridable here (PLAYGROUND_STT_MODEL /
    # PLAYGROUND_LLM_MODEL / PLAYGROUND_TTS_MODEL) without a code change.
    stt_model: str = "gpt-4o-transcribe"
    llm_model: str = "gpt-5"
    tts_model: str = "gpt-4o-mini-tts"

    # Playground auth (see playground/auth.py). Dictation touches none of
    # this. Defaulted to empty/604800 here so a bare VoiceConfig() -- used
    # throughout this suite -- keeps working with no auth env set at all;
    # token_secret's *actual* "no default" refusal is enforced separately,
    # by playground/auth.py's token_secret_from_env(), called once at
    # server.py's import time (the same way _allowed_origins() refuses a
    # "*" wildcard). A dataclass default here is just Python constructor
    # convenience, not a green light to ship with an empty secret.
    google_client_id: str = ""
    token_secret: str = ""
    session_ttl_secs: int = 604800  # 7 days

    def __post_init__(self) -> None:
        if self.dictation_stop_secs <= self.stop_secs:
            raise ValueError(
                "dictation_stop_secs must exceed stop_secs: someone drawing "
                f"pauses longer than someone talking (got {self.dictation_stop_secs} "
                f"<= {self.stop_secs})"
            )
        if self.interviewer_voice == self.coach_voice:
            raise ValueError(
                "interviewer_voice and coach_voice must differ: the handoff must be "
                f"audible or it reads as the interviewer going soft (got both '{self.interviewer_voice}')"
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
            if f.type is float or f.type == 'float':
                try:
                    kwargs[f.name] = float(raw)
                except ValueError as e:
                    raise ValueError(
                        f"Failed to parse {prefix + f.name.upper()}={raw!r} as float"
                    ) from e
            elif f.type is int or f.type == 'int':
                try:
                    kwargs[f.name] = int(raw)
                except ValueError as e:
                    raise ValueError(
                        f"Failed to parse {prefix + f.name.upper()}={raw!r} as int"
                    ) from e
            else:
                kwargs[f.name] = raw
        return cls(**kwargs)
