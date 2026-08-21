# Playground and Dictation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship hands-free dictation into the existing rep, then a live voice session where an interviewer pushes back while you draw on a whiteboard and a coach walks you through what you missed.

**Architecture:** One Python service (`playground/`) runs Pipecat over a self-hosted WebRTC connection and holds the OpenAI key. One client route (`sell/app/playground/`) runs Excalidraw and talks to it over the same peer connection's data channel. Dictation is the same pipeline with the LLM and TTS stages removed, which is why both features are one service. The board is read as a labelled graph, never as screenshots; the coach emits graph topology and never coordinates.

**Tech Stack:** Python 3.11+, `pipecat-ai==1.7.0`, FastAPI, Silero VAD, SmartTurn v3 (bundled ONNX), OpenAI STT/LLM/TTS. Next.js 16 (existing), `@excalidraw/excalidraw`, `@dagrejs/dagre`, `@pipecat-ai/client-js`.

**Spec:** `docs/superpowers/specs/2026-08-21-playground-design.md` — read it before Task 1. The plan argues from it.

## Global Constraints

- **`pipecat-ai==1.7.0`.** Its API differs from older tutorials in ways that will silently mislead you. Verified against the installed package on 2026-08-21:
  - VAD is **not** a `TransportParams` field. It is `VADProcessor(vad_analyzer=...)`, placed in the pipeline.
  - Turn detection is **not** a `TransportParams` field. It is `UserTurnStrategies`, passed via `LLMUserAggregatorParams`.
  - `PipelineTask` is **deprecated** since 1.3.0, removed in 2.0.0. Use `PipelineWorker` from `pipecat.pipeline.worker`.
  - `allow_interruptions` is **not** a `PipelineParams` field.
  - Service `model=` kwargs are **deprecated**. Use `settings=Service.Settings(model=...)`.
- **Python `>=3.11`** (`pipecat-ai` requires it).
- **Pipecat extras, exactly:** `openai,silero,webrtc,local-smart-turn`. The SmartTurn v3 ONNX model ships bundled in the wheel — nothing is downloaded at runtime.
- **npm versions:** `@excalidraw/excalidraw@0.18.1`, `@dagrejs/dagre@3.1.1`, `@pipecat-ai/client-js@1.13.0`, `@pipecat-ai/small-webrtc-transport@1.10.6`.
- **The OpenAI key never leaves the server.** Not in a response body, not in a log line, not in a client bundle, not in `NEXT_PUBLIC_*`.
- **The existing rep must keep working with the service stopped.** Type the answer, get the regex score, exactly as today. Every client task verifies this by killing the service and reloading.
- **`sell` test runner is already configured** as `npm test` → `node --experimental-strip-types --test lib/*.test.ts`. New TypeScript tests MUST live at `sell/lib/*.test.ts` or the runner will not see them.
- **Python tests use stdlib `unittest`.** No pytest dependency. Run from `playground/` with `python -m unittest discover -s tests -v`.
- **The interviewer persona must never receive `PROBES` answers or `RUBRIC` labels in its context.** Task 10 tests this. Treat it as a correctness property.

---

### Task 1: Service skeleton, and the repo is now four pipelines

**Files:**
- Create: `playground/pyproject.toml`
- Create: `playground/.env.example`
- Create: `playground/server.py`
- Create: `playground/tests/__init__.py`
- Create: `playground/tests/test_server.py`
- Create: `playground/README.md`
- Modify: `AGENTS.md` (the "One repo, three pipelines" block at the top)
- Modify: `.gitignore` (add `playground/.venv/`, `playground/.env`)

**Interfaces:**
- Consumes: nothing.
- Produces: `playground/server.py` exposing `app: FastAPI` with `GET /health` returning `{"ok": bool, "key_loaded": bool}`.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_server.py`:

```python
import os
import unittest

from fastapi.testclient import TestClient


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


if __name__ == "__main__":
    unittest.main()
```

Create empty `playground/tests/__init__.py`.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && python -m unittest discover -s tests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'playground.server'`.

- [ ] **Step 3: Create the package and make the test pass**

`playground/pyproject.toml`:

```toml
[project]
name = "hld-playground"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pipecat-ai[openai,silero,webrtc,local-smart-turn]==1.7.0",
    "fastapi>=0.115",
    "uvicorn>=0.34",
    "python-dotenv>=1.0",
]

[tool.setuptools]
packages = ["playground"]
```

`playground/.env.example`:

```
# Never commit the real file. The key stays server-side; see the plan's Global Constraints.
OPENAI_API_KEY=sk-replace-me
```

`playground/server.py`:

```python
"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="HLD Gym Playground")


@app.get("/health")
async def health() -> dict:
    """Reports whether a key is loaded. Never reports what the key is."""
    return {"ok": True, "key_loaded": bool(os.getenv("OPENAI_API_KEY"))}
```

`playground/README.md`:

````markdown
# playground — the voice service

The fourth pipeline. Runs Pipecat over a self-hosted WebRTC connection and holds
the OpenAI key. The client lives in `sell/app/playground/`.

```bash
cd playground
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -e .
cp .env.example .env      # put a real key in it
.venv/bin/uvicorn playground.server:app --reload --port 7860
python -m unittest discover -s tests -v
```

Deployment is deliberately undecided — see the spec's "Deliberately unresolved".
````

- [ ] **Step 4: Install and run the tests**

```bash
cd playground
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -e .
VIRTUAL_ENV=$PWD/.venv uv pip install httpx
.venv/bin/python -m unittest discover -s tests -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Update AGENTS.md to say four pipelines**

In `AGENTS.md`, the header block currently reads "One repo, three pipelines, one deployment." Change it to four and add the row. The new diagram block:

```
build.py     src/       →  dist/book/index.html     the book, 51 chapters, free
sell/        next       →  dist/                    the sell page, site root
reel/        scenes     →  dist/reels/*.mp4         the reel feed
playground/  pipecat    →  (not deployed)           the voice service, local only
                            ↑
                      Vercel serves this directory, with no build command
```

Add to the "Where to look" table:

```
| the voice service | `playground/README.md`, then `docs/superpowers/specs/2026-08-21-playground-design.md` |
```

Add one line under the deploy paragraph: **`playground/` writes nothing into `dist/`.** It is a service, not a build step, and it is not part of the deployment.

- [ ] **Step 6: Add ignores**

Append to `.gitignore`:

```
playground/.venv/
playground/.env
```

- [ ] **Step 7: Commit**

```bash
git add playground .gitignore AGENTS.md
git commit -m "feat: playground service skeleton, and the repo is four pipelines now"
```

---

### Task 2: Voice config, with the invariant that encodes the design decision

**Files:**
- Create: `playground/config.py`
- Create: `playground/tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `VoiceConfig` dataclass with fields `confidence: float`, `start_secs: float`, `stop_secs: float`, `min_volume: float`, `dictation_stop_secs: float`, `session_cap_secs: float`, `interviewer_voice: str`, `coach_voice: str`; and classmethod `VoiceConfig.from_env() -> VoiceConfig`.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_config.py`:

```python
import unittest

from playground.config import VoiceConfig


class TestVoiceConfig(unittest.TestCase):
    def test_dictation_waits_longer_than_conversation(self):
        """Someone drawing a diagram pauses far longer than someone talking.
        A dictation stop shorter than a conversation stop would cut them off
        mid-diagram, which is the one thing hands-free must not do."""
        c = VoiceConfig()
        self.assertGreater(c.dictation_stop_secs, c.stop_secs)

    def test_rejects_a_dictation_stop_that_is_too_eager(self):
        with self.assertRaises(ValueError):
            VoiceConfig(stop_secs=0.8, dictation_stop_secs=0.5)

    def test_the_two_personas_do_not_share_a_voice(self):
        """The handoff has to be audible or it reads as the interviewer
        going soft rather than as a change of role."""
        c = VoiceConfig()
        self.assertNotEqual(c.interviewer_voice, c.coach_voice)

    def test_from_env_overrides_defaults(self):
        c = VoiceConfig.from_env({"PLAYGROUND_STOP_SECS": "1.4"})
        self.assertEqual(c.stop_secs, 1.4)

    def test_from_env_ignores_unrelated_keys(self):
        c = VoiceConfig.from_env({"OPENAI_API_KEY": "sk-x"})
        self.assertEqual(c.stop_secs, VoiceConfig().stop_secs)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'playground.config'`.

- [ ] **Step 3: Write the implementation**

Create `playground/config.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/config.py playground/tests/test_config.py
git commit -m "feat: voice config, with the dictation-pauses-longer invariant"
```

---

### Task 3: Dictation pipeline and the transcript relay

**Files:**
- Create: `playground/relay.py`
- Create: `playground/pipelines.py`
- Create: `playground/tests/test_relay.py`
- Modify: `playground/server.py`

**Interfaces:**
- Consumes: `VoiceConfig` from Task 2.
- Produces:
  - `TranscriptRelay(FrameProcessor)` — turns a finalized `TranscriptionFrame` into an `OutputTransportMessageUrgentFrame` whose `message` is `{"type": "transcript", "text": str}`.
  - `build_dictation_worker(connection: SmallWebRTCConnection, config: VoiceConfig) -> PipelineWorker`
  - `POST /api/offer` accepting `{"sdp": str, "type": str, "pc_id": str | None}` and returning the answer.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_relay.py`:

```python
import unittest

from pipecat.frames.frames import InterimTranscriptionFrame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection

from playground.relay import TranscriptRelay


class Captured:
    """Stands in for the rest of the pipeline. Records what got pushed."""

    def __init__(self):
        self.frames = []


def run(frame):
    """Drive one frame through a relay and return what it pushed downstream."""
    import asyncio

    relay = TranscriptRelay()
    got = Captured()

    async def fake_push(f, direction=FrameDirection.DOWNSTREAM):
        got.frames.append(f)

    relay.push_frame = fake_push
    asyncio.run(relay.process_frame(frame, FrameDirection.DOWNSTREAM))
    return got.frames


class TestTranscriptRelay(unittest.TestCase):
    def test_finalized_transcription_becomes_a_client_message(self):
        out = run(
            TranscriptionFrame(
                text="the app checks the cache first",
                user_id="u",
                timestamp="t",
                finalized=True,
            )
        )
        messages = [f.message for f in out if hasattr(f, "message")]
        self.assertIn(
            {"type": "transcript", "text": "the app checks the cache first"}, messages
        )

    def test_interim_transcription_is_not_sent(self):
        """Interim text rewrites itself as the model changes its mind. Appending
        it to a textarea would make the answer stutter."""
        out = run(InterimTranscriptionFrame(text="the app che", user_id="u", timestamp="t"))
        messages = [f.message for f in out if hasattr(f, "message")]
        self.assertEqual(messages, [])

    def test_the_original_frame_still_flows_downstream(self):
        """The relay observes; it must not swallow. Playground needs the same
        frame to reach the context aggregator."""
        frame = TranscriptionFrame(text="hello", user_id="u", timestamp="t", finalized=True)
        out = run(frame)
        self.assertIn(frame, out)

    def test_unrelated_frames_pass_through_untouched(self):
        frame = TextFrame(text="not a transcript")
        out = run(frame)
        self.assertEqual(out, [frame])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'playground.relay'`.

- [ ] **Step 3: Write the relay**

Create `playground/relay.py`:

```python
"""Sends finalized transcripts down the data channel to the browser.

Observes rather than intercepts: the frame keeps flowing, because Playground
needs the same transcription to reach the context aggregator behind this.
"""

from pipecat.frames.frames import Frame, OutputTransportMessageUrgentFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class TranscriptRelay(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # Interim frames rewrite themselves as the model changes its mind;
        # appending them to a textarea makes the answer stutter.
        if isinstance(frame, TranscriptionFrame) and frame.finalized and frame.text.strip():
            await self.push_frame(
                OutputTransportMessageUrgentFrame(
                    message={"type": "transcript", "text": frame.text}
                )
            )

        await self.push_frame(frame, direction)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: 11 tests PASS. If `super().process_frame` errors outside a running pipeline, drop that line — it is not required for an observer.

- [ ] **Step 5: Write the pipeline builder**

Create `playground/pipelines.py`:

```python
"""Both pipelines. Dictation is the Playground pipeline with the LLM and TTS
stages removed, which is the reason they share a service."""

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from playground.config import VoiceConfig
from playground.relay import TranscriptRelay


def _vad(config: VoiceConfig, stop_secs: float) -> VADProcessor:
    """In pipecat 1.7 the VAD is a pipeline processor, not a transport field."""
    return VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(
                confidence=config.confidence,
                start_secs=config.start_secs,
                stop_secs=stop_secs,
                min_volume=config.min_volume,
            )
        )
    )


def build_dictation_worker(
    connection: SmallWebRTCConnection, config: VoiceConfig
) -> PipelineWorker:
    """mic -> VAD -> STT -> data channel. No LLM, no TTS, nothing talks back."""
    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=False),
    )
    stt = OpenAISTTService(settings=OpenAISTTService.Settings(model="gpt-4o-transcribe"))
    pipeline = Pipeline(
        [
            transport.input(),
            _vad(config, config.dictation_stop_secs),
            stt,
            TranscriptRelay(),
            transport.output(),
        ]
    )
    return PipelineWorker(pipeline, params=PipelineParams(enable_metrics=True))
```

- [ ] **Step 6: Add the offer endpoint**

Append to `playground/server.py`:

```python
import asyncio

from fastapi import Body
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker

_connections: dict[str, SmallWebRTCConnection] = {}


@app.post("/api/offer")
async def offer(request: dict = Body(...)) -> dict:
    """One WebRTC connection per session. mode=dictation for now."""
    pc_id = request.get("pc_id")
    if pc_id and pc_id in _connections:
        connection = _connections[pc_id]
        await connection.renegotiate(sdp=request["sdp"], type=request["type"])
        return connection.get_answer()

    connection = SmallWebRTCConnection()
    await connection.initialize(sdp=request["sdp"], type=request["type"])

    worker = build_dictation_worker(connection, VoiceConfig.from_env())
    asyncio.create_task(PipelineRunner(handle_sigint=False).run(worker))

    answer = connection.get_answer()
    _connections[answer["pc_id"]] = connection

    @connection.event_handler("closed")
    async def _on_closed(conn: SmallWebRTCConnection) -> None:
        _connections.pop(conn.pc_id, None)

    return answer
```

- [ ] **Step 7: Verify the pipeline actually assembles**

```bash
cd playground && OPENAI_API_KEY=sk-test .venv/bin/python -c "
from playground.pipelines import build_dictation_worker
from playground.config import VoiceConfig
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
print(type(build_dictation_worker(SmallWebRTCConnection(), VoiceConfig())).__name__)
"
```

Expected: prints `PipelineWorker`. If `SmallWebRTCConnection` needs different constructor or `renegotiate`/`get_answer` names, correct them here against `.venv/lib/python3.*/site-packages/pipecat/transports/smallwebrtc/connection.py` — do not guess.

- [ ] **Step 8: Listen to it**

```bash
cd playground && .venv/bin/uvicorn playground.server:app --port 7860
```

Then from Task 4's client, or any WebRTC test page, connect and speak. Expected: a `{"type":"transcript","text":...}` message per finished sentence, and **no message while you pause mid-sentence.** If it fires on your pauses, raise `PLAYGROUND_DICTATION_STOP_SECS`. This is the tuning knob, and this is the moment to turn it.

- [ ] **Step 9: Commit**

```bash
git add playground
git commit -m "feat: dictation pipeline over self-hosted webrtc"
```

---

### Task 4: Transcript append, and the client connection helper

**Files:**
- Create: `sell/lib/dictation.ts`
- Create: `sell/lib/dictation.test.ts`
- Create: `sell/lib/voice.ts`
- Modify: `sell/package.json` (dependencies)

**Interfaces:**
- Consumes: the `{"type":"transcript","text":string}` message from Task 3.
- Produces:
  - `appendTranscript(prev: string, chunk: string): string`
  - `connectVoice(opts: {url: string, onMessage: (m: unknown) => void}): Promise<{disconnect: () => void}>`
  - `VOICE_URL: string`

- [ ] **Step 1: Write the failing test**

Create `sell/lib/dictation.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { appendTranscript } from "./dictation.ts";

test("first chunk becomes the whole answer", () => {
  assert.equal(appendTranscript("", "the app checks the cache"), "the app checks the cache");
});

test("later chunks are separated by exactly one space", () => {
  assert.equal(
    appendTranscript("the app checks the cache", "then it queries the database"),
    "the app checks the cache then it queries the database",
  );
});

test("trailing and leading whitespace never doubles up", () => {
  assert.equal(appendTranscript("a cache. ", "  Then the DB"), "a cache. Then the DB");
});

test("an empty chunk changes nothing", () => {
  assert.equal(appendTranscript("a cache", "   "), "a cache");
});

test("typed text the visitor already wrote is preserved verbatim", () => {
  // Dictation lands beside the keyboard, never replacing it.
  assert.equal(appendTranscript("I think it's cache-aside", "yes"), "I think it's cache-aside yes");
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd sell && npm test
```

Expected: FAIL — cannot resolve `./dictation.ts`.

- [ ] **Step 3: Write the implementation**

Create `sell/lib/dictation.ts`:

```ts
/* Spoken answers land in the same textarea as typed ones, so the regex rubric
   in rep.ts grades both through exactly one path. */

/** Append one finalized transcript chunk to what is already in the box. */
export function appendTranscript(prev: string, chunk: string): string {
  const next = chunk.trim();
  if (!next) return prev;
  const base = prev.trimEnd();
  return base ? `${base} ${next}` : next;
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd sell && npm test
```

Expected: all PASS, including the existing `rep.test.ts`.

- [ ] **Step 5: Install client dependencies**

```bash
cd sell && npm install @pipecat-ai/client-js@1.13.0 @pipecat-ai/small-webrtc-transport@1.10.6
```

- [ ] **Step 6: Write the connection helper**

Create `sell/lib/voice.ts`:

```ts
"use client";

import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

/* Not NEXT_PUBLIC_-prefixed by accident: this is a URL, and only a URL. The
   OpenAI key lives on the service and is never shipped to a browser. */
export const VOICE_URL = process.env.NEXT_PUBLIC_VOICE_URL ?? "http://localhost:7860";

export type VoiceSession = { disconnect: () => Promise<void> };

/** Connect, hand every server message to onMessage. Throws if unreachable —
    callers fall back to the keyboard rather than showing a broken control. */
export async function connectVoice(opts: {
  url?: string;
  onMessage: (message: unknown) => void;
}): Promise<VoiceSession> {
  const client = new PipecatClient({
    transport: new SmallWebRTCTransport({ connectionUrl: `${opts.url ?? VOICE_URL}/api/offer` }),
    enableMic: true,
    enableCam: false,
    callbacks: { onServerMessage: opts.onMessage },
  });
  await client.connect();
  return { disconnect: () => client.disconnect() };
}
```

- [ ] **Step 7: Verify the client library's actual API**

```bash
cd sell && node -e "
const m = require('@pipecat-ai/client-js');
console.log(Object.keys(m).filter(k => /Client|Transport|Event/.test(k)));
"
```

If `PipecatClient`, the `callbacks.onServerMessage` name, or `SmallWebRTCTransport`'s option key differ from the above, correct `voice.ts` to match the installed package. Do not leave a remembered name in.

- [ ] **Step 8: Commit**

```bash
git add sell/lib/dictation.ts sell/lib/dictation.test.ts sell/lib/voice.ts sell/package.json sell/package-lock.json
git commit -m "feat: transcript append and the voice connection helper"
```

---

### Task 5: Dictation inside the existing rep

**Files:**
- Modify: `sell/components/Rep.tsx`
- Modify: `sell/app/globals.css` (the mic control's styles)

**Interfaces:**
- Consumes: `appendTranscript`, `connectVoice` from Task 4.
- Produces: no new exports. A `Speak` toggle beside the recall textarea.

- [ ] **Step 1: Add the dictation state and handler to Rep.tsx**

Inside `export default function Rep()`, after the existing `const [recall, setRecall] = useState("")`:

```tsx
const [mic, setMic] = useState<"off" | "connecting" | "on" | "unavailable">("off");
const session = useRef<VoiceSession | null>(null);

useEffect(() => () => void session.current?.disconnect(), []);

const toggleMic = useCallback(async () => {
  if (session.current) {
    await session.current.disconnect();
    session.current = null;
    setMic("off");
    return;
  }
  setMic("connecting");
  try {
    session.current = await connectVoice({
      onMessage: (m) => {
        const msg = m as { type?: string; text?: string };
        if (msg?.type === "transcript" && msg.text) {
          setRecall((prev) => appendTranscript(prev, msg.text as string));
        }
      },
    });
    setMic("on");
  } catch {
    /* Mic denied, or the service is not running. Either way the keyboard is
       right there and still works — say so, do not show a dead control. */
    setMic("unavailable");
  }
}, []);
```

Add the imports at the top of the file:

```tsx
import { appendTranscript } from "@/lib/dictation";
import { connectVoice, type VoiceSession } from "@/lib/voice";
```

- [ ] **Step 2: Render the control beside the textarea**

Immediately after the recall `<textarea>` in the `locked` phase, add:

```tsx
<div className="dictate">
  <button
    type="button"
    className="dictate-btn"
    onClick={toggleMic}
    disabled={mic === "connecting" || mic === "unavailable"}
    aria-pressed={mic === "on"}
  >
    {mic === "on" ? "◉ listening" : mic === "connecting" ? "connecting…" : "◎ speak it"}
  </button>
  <span className="dictate-note">
    {mic === "unavailable"
      ? "Voice is unavailable right now — type it instead, the scoring is identical."
      : "Or type it. Both are graded the same way."}
  </span>
</div>
```

- [ ] **Step 3: Style it**

In `sell/app/globals.css`, following the existing conventions in that file (read the surrounding rules first and match them — do not invent a new naming scheme):

```css
.dictate { display: flex; align-items: center; gap: .6rem; margin-top: .5rem; flex-wrap: wrap; }
.dictate-btn { font: inherit; font-size: .8rem; padding: .3rem .7rem; border: 1px solid var(--line-strong); background: transparent; color: var(--ink); cursor: pointer; }
.dictate-btn[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); }
.dictate-btn:disabled { opacity: .55; cursor: default; }
.dictate-note { font-size: .78rem; color: var(--ink-muted); }
```

Check the actual variable names in `globals.css` before writing this — `--ink`, `--accent`, `--line-strong` and `--ink-muted` must match what the theme blocks already define.

- [ ] **Step 4: Verify the fallback first, the feature second**

```bash
# Service deliberately NOT running.
cd sell && npm run dev
```

Open the rep, reach the locked phase, click `◎ speak it`. Expected: the button reports unavailable, the note tells you to type, **the textarea still accepts typing and the grade still works.** This is the constraint that matters most; verify it before verifying the happy path.

Then start `playground` and repeat. Expected: speak a sentence, it appears in the textarea; grading behaves identically to typing it.

- [ ] **Step 5: Run the full test suite and the lint**

```bash
cd sell && npm test && npm run lint && npm run build
```

Expected: tests PASS, lint clean, static export builds.

- [ ] **Step 6: Commit**

```bash
git add sell/components/Rep.tsx sell/app/globals.css
git commit -m "feat: speak the rep answer instead of typing it"
```

---

### Task 6: The board extractor

This is the highest-value test in the build. Everything the coach knows about the drawing comes through this function.

**Files:**
- Create: `sell/lib/board.ts`
- Create: `sell/lib/board.test.ts`
- Create: `sell/lib/fixtures/board-sample.json`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `type BoardGraph = { nodes: {id: string, label: string}[]; edges: {from: string, to: string, label: string}[]; unreadable: number }`
  - `extractGraph(elements: readonly BoardElement[]): BoardGraph`
  - `COACH_AUTHOR = "coach"` — the `customData.author` marker.

- [ ] **Step 1: Produce a real fixture, do not hand-write one**

Open `https://excalidraw.com`, draw: two rectangles labelled `App` and `Cache`, an arrow from App to Cache labelled `GET`, and one freehand squiggle. Export via the menu → *Save to…* → a `.excalidraw` file. Copy its `elements` array into `sell/lib/fixtures/board-sample.json` as the whole file contents.

Then append one coach-authored element to that array by hand:

```json
{ "id": "coach-box-1", "type": "rectangle", "customData": { "author": "coach" },
  "x": 900, "y": 100, "width": 120, "height": 60, "boundElements": [] }
```

Hand-writing the fixture instead of exporting it is how you end up testing against field names Excalidraw does not use.

- [ ] **Step 2: Write the failing test**

Create `sell/lib/board.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { extractGraph, COACH_AUTHOR, type BoardElement } from "./board.ts";

const scene = JSON.parse(
  readFileSync(new URL("./fixtures/board-sample.json", import.meta.url), "utf8"),
) as BoardElement[];

test("labelled boxes become nodes", () => {
  const g = extractGraph(scene);
  assert.deepEqual(g.nodes.map((n) => n.label).sort(), ["App", "Cache"]);
});

test("a bound arrow becomes an edge between those nodes", () => {
  const g = extractGraph(scene);
  const app = g.nodes.find((n) => n.label === "App")!;
  const cache = g.nodes.find((n) => n.label === "Cache")!;
  assert.deepEqual(g.edges, [{ from: app.id, to: cache.id, label: "GET" }]);
});

test("freehand strokes are counted, not guessed at", () => {
  assert.equal(extractGraph(scene).unreadable, 1);
});

test("coach-drawn elements are excluded", () => {
  // Otherwise the coach reads its own diagram back and congratulates the user.
  const g = extractGraph(scene);
  assert.equal(g.nodes.some((n) => n.id === "coach-box-1"), false);
});

test("deleted elements are excluded", () => {
  const withDeleted = [...scene, { id: "gone", type: "rectangle", isDeleted: true } as BoardElement];
  assert.deepEqual(extractGraph(withDeleted).nodes, extractGraph(scene).nodes);
});

test("an unbound arrow is dropped rather than invented", () => {
  const loose = [...scene, { id: "loose", type: "arrow" } as BoardElement];
  assert.equal(extractGraph(loose).edges.length, 1);
});

test("an empty board is an empty graph, not a crash", () => {
  assert.deepEqual(extractGraph([]), { nodes: [], edges: [], unreadable: 0 });
});

test("the marker constant is what the layout module will stamp", () => {
  assert.equal(COACH_AUTHOR, "coach");
});
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd sell && npm test
```

Expected: FAIL — cannot resolve `./board.ts`.

- [ ] **Step 4: Write the implementation**

Create `sell/lib/board.ts`:

```ts
/* The coach reads the board as a labelled graph, never as a screenshot. A graph
   is ~200 tokens, exact, and diffable — and "what changed" is the signal a coach
   that unsticks people runs on. A snapshot has no memory of the previous frame. */

export const COACH_AUTHOR = "coach";

export type BoardElement = {
  id: string;
  type: string;
  isDeleted?: boolean;
  text?: string;
  containerId?: string | null;
  customData?: { author?: string } | null;
  startBinding?: { elementId: string } | null;
  endBinding?: { elementId: string } | null;
  boundElements?: { id: string; type: string }[] | null;
};

export type BoardGraph = {
  nodes: { id: string; label: string }[];
  edges: { from: string; to: string; label: string }[];
  unreadable: number;
};

const NODE_TYPES = new Set(["rectangle", "ellipse", "diamond"]);
const EDGE_TYPES = new Set(["arrow", "line"]);

export function extractGraph(elements: readonly BoardElement[]): BoardGraph {
  const live = elements.filter(
    (e) => !e.isDeleted && e.customData?.author !== COACH_AUTHOR,
  );

  /* Excalidraw stores a box's label as a separate text element pointing back at
     its container, so labels are looked up rather than read off the box. */
  const labelOf = new Map<string, string>();
  for (const e of live) {
    if (e.type === "text" && e.containerId && e.text) {
      labelOf.set(e.containerId, e.text.trim());
    }
  }

  const nodes = live
    .filter((e) => NODE_TYPES.has(e.type))
    .map((e) => ({ id: e.id, label: labelOf.get(e.id) ?? "" }));
  const nodeIds = new Set(nodes.map((n) => n.id));

  const edges = live
    .filter((e) => EDGE_TYPES.has(e.type))
    /* An arrow bound to nothing is a stroke the user has not finished placing.
       Dropping it beats inventing an endpoint for it. */
    .filter(
      (e) =>
        e.startBinding?.elementId &&
        e.endBinding?.elementId &&
        nodeIds.has(e.startBinding.elementId) &&
        nodeIds.has(e.endBinding.elementId),
    )
    .map((e) => ({
      from: e.startBinding!.elementId,
      to: e.endBinding!.elementId,
      label: labelOf.get(e.id) ?? "",
    }));

  const unreadable = live.filter((e) => e.type === "freedraw").length;

  return { nodes, edges, unreadable };
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd sell && npm test
```

Expected: all PASS. If the fixture's real field names differ from the type above — they are ground truth, the type is not — correct `BoardElement` and the lookups to match the fixture, and say so in the commit message.

- [ ] **Step 6: Commit**

```bash
git add sell/lib/board.ts sell/lib/board.test.ts sell/lib/fixtures/board-sample.json
git commit -m "feat: read the whiteboard as a labelled graph"
```

---

### Task 7: Change detection, so the board is not resent on every stroke

**Files:**
- Modify: `sell/lib/board.ts`
- Modify: `sell/lib/board.test.ts`

**Interfaces:**
- Consumes: `BoardGraph` from Task 6.
- Produces: `graphSignature(graph: BoardGraph): string`

- [ ] **Step 1: Write the failing test**

Append to `sell/lib/board.test.ts`:

```ts
import { graphSignature } from "./board.ts";

test("the same graph signs the same", () => {
  const g = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  assert.equal(graphSignature(g), graphSignature(structuredClone(g)));
});

test("moving a box does not change the signature", () => {
  // Dragging a node around is not a semantic change and must not wake the coach.
  const a = extractGraph(scene);
  const moved = extractGraph(scene.map((e) => ({ ...e, x: 999 } as BoardElement)));
  assert.equal(graphSignature(a), graphSignature(moved));
});

test("adding an edge changes the signature", () => {
  const a = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  const b = { ...a, edges: [{ from: "a", to: "a", label: "" }] };
  assert.notEqual(graphSignature(a), graphSignature(b));
});

test("renaming a node changes the signature", () => {
  const a = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  const b = { nodes: [{ id: "a", label: "Cache" }], edges: [], unreadable: 0 };
  assert.notEqual(graphSignature(a), graphSignature(b));
});

test("element order does not change the signature", () => {
  const a = { nodes: [{ id: "a", label: "A" }, { id: "b", label: "B" }], edges: [], unreadable: 0 };
  const b = { nodes: [{ id: "b", label: "B" }, { id: "a", label: "A" }], edges: [], unreadable: 0 };
  assert.equal(graphSignature(a), graphSignature(b));
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd sell && npm test
```

Expected: FAIL — `graphSignature` is not exported.

- [ ] **Step 3: Write the implementation**

Append to `sell/lib/board.ts`:

```ts
/** A stable string for a graph's meaning. Two boards with the same components
    and the same connections sign identically no matter where they sit on the
    canvas or what order they were drawn in. */
export function graphSignature(graph: BoardGraph): string {
  const nodes = graph.nodes.map((n) => `${n.id}:${n.label}`).sort();
  const edges = graph.edges.map((e) => `${e.from}>${e.to}:${e.label}`).sort();
  return JSON.stringify([nodes, edges, graph.unreadable]);
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd sell && npm test
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add sell/lib/board.ts sell/lib/board.test.ts
git commit -m "feat: only wake the coach when the board's meaning changes"
```

---

### Task 8: The playground route

**Files:**
- Create: `sell/app/playground/page.tsx`
- Create: `sell/components/Board.tsx`
- Modify: `sell/package.json`

**Interfaces:**
- Consumes: `extractGraph`, `graphSignature` (Task 6/7), `connectVoice` (Task 4).
- Produces: `<Board onGraphChange={(g: BoardGraph) => void} apiRef={(api: ExcalidrawImperativeAPI) => void} />`

- [ ] **Step 1: Install Excalidraw**

```bash
cd sell && npm install @excalidraw/excalidraw@0.18.1
```

- [ ] **Step 2: Write the board component**

Create `sell/components/Board.tsx`:

```tsx
"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef } from "react";
import { extractGraph, graphSignature, type BoardElement, type BoardGraph } from "@/lib/board";
import "@excalidraw/excalidraw/index.css";

/* Excalidraw touches window at module scope, so it cannot be server-rendered.
   ssr:false also keeps its ~1MB out of every other route's bundle. */
const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="board-loading">loading the board…</div> },
);

const SETTLE_MS = 800;

export default function Board({
  onGraphChange,
  apiRef,
}: {
  onGraphChange: (graph: BoardGraph) => void;
  apiRef: (api: unknown) => void;
}) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSig = useRef<string>("");

  /* Debounced, and gated on the signature: this is VAD for the board. Sending
     on every stroke would bury the coach in noise and bill for it. */
  const onChange = useCallback(
    (elements: readonly unknown[]) => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => {
        const graph = extractGraph(elements as readonly BoardElement[]);
        const sig = graphSignature(graph);
        if (sig === lastSig.current) return;
        lastSig.current = sig;
        onGraphChange(graph);
      }, SETTLE_MS);
    },
    [onGraphChange],
  );

  return (
    <div className="board">
      <Excalidraw onChange={onChange} excalidrawAPI={apiRef} />
    </div>
  );
}
```

- [ ] **Step 3: Write the route**

Create `sell/app/playground/page.tsx`:

```tsx
"use client";

import { useCallback, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import type { BoardGraph } from "@/lib/board";

export default function PlaygroundPage() {
  const [state, setState] = useState<"idle" | "connecting" | "live" | "unavailable">("idle");
  const [said, setSaid] = useState<string[]>([]);
  const session = useRef<VoiceSession | null>(null);
  const send = useRef<((m: unknown) => void) | null>(null);

  const onGraphChange = useCallback((graph: BoardGraph) => {
    send.current?.({ type: "board", graph });
  }, []);

  const start = useCallback(async () => {
    setState("connecting");
    try {
      session.current = await connectVoice({
        onMessage: (m) => {
          const msg = m as { type?: string; text?: string };
          if (msg?.type === "transcript" && msg.text) setSaid((s) => [...s, msg.text!]);
        },
      });
      setState("live");
    } catch {
      setState("unavailable");
    }
  }, []);

  return (
    <main className="playground">
      <h1>Playground</h1>
      {state !== "live" && (
        <button type="button" onClick={start} disabled={state === "connecting"}>
          {state === "unavailable" ? "voice service unreachable" : "start the round"}
        </button>
      )}
      <Board onGraphChange={onGraphChange} apiRef={() => {}} />
      <ol className="said">{said.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </main>
  );
}
```

- [ ] **Step 4: Verify it builds and the export still works**

```bash
cd sell && npm run lint && npm run build
```

Expected: builds. Confirm `out/playground/index.html` exists and that `/` did not grow — compare the `First Load JS` figure for `/` before and after in the build output. If `/` grew, the dynamic import is not splitting and must be fixed before moving on.

- [ ] **Step 5: Verify in the browser**

```bash
cd sell && npm run dev
```

Open `/playground/`. Draw two labelled boxes and an arrow between them. Expected: no console errors, and (with the service running and a temporary `console.log` in `onGraphChange`) exactly one graph logged ~800ms after you stop, not one per stroke.

- [ ] **Step 6: Commit**

```bash
git add sell/app/playground sell/components/Board.tsx sell/package.json sell/package-lock.json
git commit -m "feat: the playground route, with a whiteboard that settles before it speaks"
```

---

### Task 9: Board context on the server, replaced in place

**Files:**
- Create: `playground/board.py`
- Create: `playground/tests/test_board.py`

**Interfaces:**
- Consumes: the `{"type":"board","graph":{...}}` message from Task 8.
- Produces: `BoardContext` with `update(graph: dict) -> None`, `messages() -> list[dict]`, and property `last_change_summary: str`.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_board.py`:

```python
import unittest

from playground.board import BoardContext

A = {"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0}
B = {
    "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
    "edges": [{"from": "a", "to": "c", "label": "GET"}],
    "unreadable": 0,
}


class TestBoardContext(unittest.TestCase):
    def test_starts_with_no_messages(self):
        self.assertEqual(BoardContext().messages(), [])

    def test_one_update_yields_one_message(self):
        b = BoardContext()
        b.update(A)
        self.assertEqual(len(b.messages()), 1)

    def test_many_updates_still_yield_one_message(self):
        """A ten-minute session must not accumulate two hundred copies of a
        diagram. The board message is replaced in place, never appended."""
        b = BoardContext()
        for _ in range(200):
            b.update(B)
        self.assertEqual(len(b.messages()), 1)

    def test_the_message_names_the_components(self):
        b = BoardContext()
        b.update(B)
        text = b.messages()[0]["content"]
        self.assertIn("App", text)
        self.assertIn("Cache", text)
        self.assertIn("GET", text)

    def test_it_reports_what_just_changed(self):
        b = BoardContext()
        b.update(A)
        b.update(B)
        self.assertIn("Cache", b.last_change_summary)

    def test_unreadable_strokes_are_declared_not_guessed(self):
        b = BoardContext()
        b.update({"nodes": [], "edges": [], "unreadable": 3})
        self.assertIn("3", b.messages()[0]["content"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'playground.board'`.

- [ ] **Step 3: Write the implementation**

Create `playground/board.py`:

```python
"""The board's presence in the LLM context: one message, replaced in place.

Appending each update would put two hundred copies of a diagram in a ten-minute
session's context and bill for every one of them.
"""


class BoardContext:
    def __init__(self) -> None:
        self._graph: dict | None = None
        self._previous: dict | None = None

    def update(self, graph: dict) -> None:
        self._previous, self._graph = self._graph, graph

    def messages(self) -> list[dict]:
        if self._graph is None:
            return []
        return [{"role": "system", "content": self._render(self._graph)}]

    @property
    def last_change_summary(self) -> str:
        """One line naming what appeared since the previous update. Empty on the
        first update, when everything is new and nothing has 'just' changed."""
        if self._previous is None or self._graph is None:
            return ""
        before = {n["id"] for n in self._previous["nodes"]}
        added = [n["label"] or n["id"] for n in self._graph["nodes"] if n["id"] not in before]
        before_edges = {(e["from"], e["to"]) for e in self._previous["edges"]}
        new_edges = [e for e in self._graph["edges"] if (e["from"], e["to"]) not in before_edges]
        parts = []
        if added:
            parts.append("added " + ", ".join(added))
        if new_edges:
            names = {n["id"]: (n["label"] or n["id"]) for n in self._graph["nodes"]}
            parts.append(
                "connected "
                + ", ".join(f"{names.get(e['from'], '?')}->{names.get(e['to'], '?')}" for e in new_edges)
            )
        return "; ".join(parts)

    @staticmethod
    def _render(graph: dict) -> str:
        names = {n["id"]: (n["label"] or "(unlabelled)") for n in graph["nodes"]}
        lines = ["The candidate's whiteboard right now:"]
        lines.append("Components: " + (", ".join(names.values()) or "none yet"))
        if graph["edges"]:
            lines.append(
                "Connections: "
                + ", ".join(
                    f"{names.get(e['from'], '?')} -> {names.get(e['to'], '?')}"
                    + (f" ({e['label']})" if e["label"] else "")
                    for e in graph["edges"]
                )
            )
        if graph["unreadable"]:
            lines.append(
                f"There are {graph['unreadable']} freehand marks you cannot read. "
                "Ask what they are rather than guessing."
            )
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/board.py playground/tests/test_board.py
git commit -m "feat: the board lives in context as one message, replaced in place"
```

---

### Task 10: The two personas, the rep content, and a drift guard

**Files:**
- Create: `playground/rep.py`
- Create: `playground/personas.py`
- Create: `playground/tests/test_personas.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `playground/rep.py`: `REP_TITLE: str`, `KERNEL: str`, `RUBRIC_LABELS: list[str]`, `PROBES: list[dict]` (each `{"q": str, "a": str}`).
  - `playground/personas.py`: `interviewer_prompt() -> str`, `coach_prompt() -> str`.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_personas.py`:

```python
import pathlib
import re
import unittest

from playground import rep
from playground.personas import coach_prompt, interviewer_prompt

REP_TS = pathlib.Path(__file__).resolve().parents[2] / "sell" / "lib" / "rep.ts"


class TestPersonas(unittest.TestCase):
    def test_the_interviewer_does_not_hold_the_answers(self):
        """A model holding the answers leaks them the moment a candidate sounds
        stuck, and then the round graded nothing."""
        prompt = interviewer_prompt()
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertNotIn(label, prompt)

    def test_the_coach_does_hold_the_answers(self):
        prompt = coach_prompt()
        for probe in rep.PROBES:
            self.assertIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertIn(label, prompt)

    def test_the_interviewer_still_knows_the_question(self):
        self.assertIn(rep.REP_TITLE, interviewer_prompt())

    def test_the_two_prompts_are_not_the_same_text(self):
        self.assertNotEqual(interviewer_prompt(), coach_prompt())


class TestNoDriftFromTheFrontend(unittest.TestCase):
    """Python cannot import sell/lib/rep.ts, so the rubric exists twice. This is
    the guard that stops the two copies quietly disagreeing."""

    def test_rubric_labels_match_rep_ts(self):
        source = REP_TS.read_text()
        block = source.split("export const RUBRIC")[1].split("];")[0]
        labels = re.findall(r'label:\s*"([^"]+)"', block)
        self.assertEqual(labels, rep.RUBRIC_LABELS)

    def test_probe_questions_match_rep_ts(self):
        source = REP_TS.read_text()
        block = source.split("export const PROBES")[1].split("];")[0]
        questions = re.findall(r'q:\s*"((?:[^"\\]|\\.)*)"', block)
        self.assertEqual(len(questions), len(rep.PROBES))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL with `ImportError: cannot import name 'rep'`.

- [ ] **Step 3: Port the rep content**

Create `playground/rep.py`. Read `sell/lib/rep.ts` and copy the six `RUBRIC` labels verbatim (the drift test compares them character for character, in order) and all three `PROBES` questions and answers verbatim:

```python
"""The one rep this service knows, ported from sell/lib/rep.ts.

Python cannot import TypeScript, so this is a second copy. test_personas.py
parses rep.ts and fails if the two ever disagree. Change one, change both.
"""

REP_TITLE = "p1c06 · cache-aside read path"

KERNEL = (
    "Cache-aside: the app asks the cache first. On a miss the cache does not "
    "fetch anything — it just says no. The app queries the database itself, the "
    "rows come back to the app rather than to the cache, and the app writes the "
    "cache with a TTL. That is what 'aside' means: the cache is a dumb box the "
    "application manages, not a layer that sits in front of the database."
)

# Verbatim from RUBRIC in sell/lib/rep.ts, in order. The drift test compares
# these character for character.
RUBRIC_LABELS = [
    "GET from the cache first",
    "the miss comes back to the app",
    "the app queries the database",
    "rows return to the app, not the cache",
    "the app writes the cache itself",
    "a TTL on the write",
]

# Verbatim from PROBES in sell/lib/rep.ts. Curly apostrophes and quotes are
# intentional — they are what the file contains, and the coach's credibility is
# that it says what the book says.
PROBES = [
    {
        "q": "Step 2 was a miss. Why didn’t the cache go and fetch it for you?",
        "a": "Because cache-aside puts the app in charge, not the cache. The cache is a dumb key-value box that answers hit or miss and nothing else. That is exactly why it is resilient: when the cache dies, reads get slower but they still work, because the fallback path is already the normal path. A read-through cache would have fetched it for you, and taken the database down with it when it failed.",
    },
    {
        "q": "Between step 2 and step 5, another server updates that product and deletes the key. What is in your cache after step 5?",
        "a": "Stale data, and it sits there wrong until the TTL expires. Your step 5 writes rows that were true at step 2. The delete happened in between, so it deleted nothing, and then you refilled the key with the old value. This is the race at the heart of cache invalidation, and it is why the TTL is not optional decoration: it is the only thing that eventually saves you.",
    },
    {
        "q": "Your hit rate is 99%. The cache dies. What happens to the database?",
        "a": "It takes 100× its normal read load, instantly, and almost certainly falls over. The better your hit rate, the more catastrophic losing the cache becomes. Success is what created the fragility. A 99% hit rate means the database was only ever sized for 1% of real traffic. This is why you load-test with the cache cold, and why “the cache is just an optimisation” stops being true the moment you depend on it.",
    },
]
```

- [ ] **Step 4: Write the personas**

Create `playground/personas.py`:

```python
"""Two prompts. The difference between them is the whole product.

The interviewer is deliberately starved of the answer key — see the tests.
"""

from playground import rep

_SHARED = (
    "You are speaking out loud to a working engineer who is drawing a system "
    "design on a whiteboard. Keep every turn under three sentences. Never read "
    "a list aloud. If freehand marks on their board are unreadable, ask them to "
    "name the component rather than guessing at it."
)

_INTERVIEWER = f"""{_SHARED}

You are a senior interviewer running a round on: {rep.REP_TITLE}.

Push back. Ask for numbers when they hand-wave about scale. Make them defend a
choice rather than agreeing with it. When they ask you whether they are right,
turn the question back on them.

You do not know the model answer and you do not hint. Your job is to find out
what they know, not to teach. When the round has run its course, call
end_round with a one-line reason.
"""

_COACH = f"""{_SHARED}

The round is over and you have switched roles. You are now a coach, and you say
so in your first sentence so the change is unmistakable.

The chapter says: {rep.KERNEL}

A complete answer contains all six of these:
{chr(10).join("- " + label for label in rep.RUBRIC_LABELS)}

The follow-ups and their answers:
{chr(10).join(f"- Q: {p['q']}{chr(10)}  A: {p['a']}" for p in rep.PROBES)}

Work from what they actually drew and said. Name the one thing they missed that
matters most, and make them say it back before you move on. Use draw_diagram
when a picture settles it faster than a sentence.
"""


def interviewer_prompt() -> str:
    return _INTERVIEWER


def coach_prompt() -> str:
    return _COACH
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: all PASS. The drift tests failing means `rep.py` and `rep.ts` genuinely disagree — fix the copy, do not loosen the test.

- [ ] **Step 6: Commit**

```bash
git add playground/rep.py playground/personas.py playground/tests/test_personas.py
git commit -m "feat: two personas, and a guard against the rubric drifting from rep.ts"
```

---

### Task 11: The playground pipeline, the mode switch, and draw_diagram

**Files:**
- Create: `playground/session.py`
- Create: `playground/tests/test_session.py`
- Modify: `playground/pipelines.py`
- Modify: `playground/server.py`

**Interfaces:**
- Consumes: `VoiceConfig`, `BoardContext`, `interviewer_prompt`, `coach_prompt`.
- Produces:
  - `Session` with `mode: str` (`"interview"` | `"coach"`), `switch_to_coach() -> None`, `system_messages() -> list[dict]`, `tts_voice() -> str`.
  - `build_playground_worker(connection, config) -> tuple[PipelineWorker, Session]`

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_session.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'playground.session'`.

- [ ] **Step 3: Write the session**

Create `playground/session.py`:

```python
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

    def switch_to_coach(self) -> None:
        self.mode = "coach"

    def tts_voice(self) -> str:
        return self.config.coach_voice if self.mode == "coach" else self.config.interviewer_voice

    def system_messages(self) -> list[dict]:
        persona = coach_prompt() if self.mode == "coach" else interviewer_prompt()
        return [{"role": "system", "content": persona}, *self.board.messages()]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 5: Build the full pipeline**

Append to `playground/pipelines.py`:

```python
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.frames.frames import OutputTransportMessageUrgentFrame
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.turns.user_stop import TurnAnalyzerUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from playground.session import Session

DRAW_DIAGRAM = FunctionSchema(
    name="draw_diagram",
    description=(
        "Draw a diagram beside the candidate's work. Give topology only — never "
        "positions, the client lays it out."
    ),
    properties={
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "label": {"type": "string"}},
                "required": ["id", "label"],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["from", "to"],
            },
        },
    },
    required=["nodes", "edges"],
)

END_ROUND = FunctionSchema(
    name="end_round",
    description="End the interview and hand over to the coach.",
    properties={"reason": {"type": "string"}},
    required=["reason"],
)


def build_playground_worker(
    connection: SmallWebRTCConnection, config: VoiceConfig
) -> tuple[PipelineWorker, Session]:
    """mic -> VAD -> STT -> context -> LLM -> TTS -> speaker."""
    session = Session(config)

    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    )
    stt = OpenAISTTService(settings=OpenAISTTService.Settings(model="gpt-4o-transcribe"))
    llm = OpenAILLMService(model="gpt-5")
    tts = OpenAITTSService(
        settings=OpenAITTSService.Settings(model="gpt-4o-mini-tts", voice=session.tts_voice())
    )

    context = LLMContext(messages=session.system_messages())
    context.set_tools(ToolsSchema(standard_tools=[END_ROUND, DRAW_DIAGRAM]))

    async def on_end_round(params):
        session.switch_to_coach()
        context.set_messages(session.system_messages())
        await tts.set_voice(session.tts_voice())
        await params.result_callback({"ok": True})

    async def on_draw_diagram(params):
        await transport.output().push_frame(
            OutputTransportMessageUrgentFrame(
                message={"type": "draw", "topology": params.arguments}
            )
        )
        await params.result_callback({"drawn": True})

    llm.register_function("end_round", on_end_round)
    llm.register_function("draw_diagram", on_draw_diagram)

    aggregators = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=config.stop_secs, min_volume=config.min_volume)
            ),
            # SmartTurn v3's ONNX model ships bundled in the wheel. It is what
            # stops the interviewer cutting in on "...checks the cache first, and".
            user_turn_strategies=UserTurnStrategies(
                stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=LocalSmartTurnAnalyzerV3())]
            ),
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            _vad(config, config.stop_secs),
            stt,
            TranscriptRelay(),
            aggregators.user(),
            llm,
            tts,
            transport.output(),
            aggregators.assistant(),
        ]
    )
    return PipelineWorker(pipeline, params=PipelineParams(enable_metrics=True)), session
```

- [ ] **Step 6: Route board messages in, and pick the mode**

In `playground/server.py`, change `/api/offer` to read `request.get("mode", "dictation")` and call `build_playground_worker` when it is `"playground"`. Register the inbound handler:

```python
@connection.event_handler("on_app_message")
async def _on_app_message(conn, message, sender=None) -> None:
    if isinstance(message, dict) and message.get("type") == "board":
        session.board.update(message["graph"])
        context.set_messages(session.system_messages())
```

The event name and handler arity must be checked against the installed transport — `grep -n "on_client_message\|on_app_message" .venv/lib/python3.*/site-packages/pipecat/transports/smallwebrtc/transport.py` and match what is actually emitted. Do not guess between the two.

- [ ] **Step 7: Verify assembly, then listen to it**

```bash
cd playground && OPENAI_API_KEY=sk-test .venv/bin/python -c "
from playground.pipelines import build_playground_worker
from playground.config import VoiceConfig
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
w, s = build_playground_worker(SmallWebRTCConnection(), VoiceConfig())
print(type(w).__name__, s.mode)
"
```

Expected: `PipelineWorker interview`.

Then run it with a real key and hold a round. Verify, in this order: (1) it does not cut you off mid-sentence; (2) it does not hand you the answer when you say "I'm stuck"; (3) `end_round` switches the voice audibly.

If `llm.register_function`'s handler signature differs from `params.arguments` / `params.result_callback`, correct it against `.venv/lib/python3.*/site-packages/pipecat/services/llm_service.py`.

- [ ] **Step 8: Commit**

```bash
git add playground
git commit -m "feat: the playground pipeline, and an audible handoff to the coach"
```

---

### Task 12: Layout, so the coach's diagram is legible

**Files:**
- Create: `sell/lib/layout.ts`
- Create: `sell/lib/layout.test.ts`
- Modify: `sell/components/Board.tsx`
- Modify: `sell/app/playground/page.tsx`
- Modify: `sell/package.json`

**Interfaces:**
- Consumes: `COACH_AUTHOR` from Task 6; the `{"type":"draw","topology":{nodes,edges}}` message from Task 11.
- Produces: `layoutTopology(topology: Topology, offsetX: number): ExcalidrawSkeleton[]` where `Topology = {nodes: {id,label}[], edges: {from,to,label?}[]}`.

- [ ] **Step 1: Install dagre**

```bash
cd sell && npm install @dagrejs/dagre@3.1.1
```

- [ ] **Step 2: Write the failing test**

Create `sell/lib/layout.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { layoutTopology } from "./layout.ts";
import { COACH_AUTHOR } from "./board.ts";

const TOPOLOGY = {
  nodes: [
    { id: "app", label: "App" },
    { id: "cache", label: "Cache" },
    { id: "db", label: "DB" },
  ],
  edges: [
    { from: "app", to: "cache", label: "GET" },
    { from: "app", to: "db", label: "query" },
  ],
};

test("every node becomes one skeleton element", () => {
  const els = layoutTopology(TOPOLOGY, 0);
  assert.equal(els.filter((e) => e.type === "rectangle").length, 3);
});

test("every edge becomes one arrow", () => {
  const els = layoutTopology(TOPOLOGY, 0);
  assert.equal(els.filter((e) => e.type === "arrow").length, 2);
});

test("every element is stamped as the coach's", () => {
  // The extractor excludes these. Miss the stamp and the coach reads its own
  // diagram back as the candidate's work.
  const els = layoutTopology(TOPOLOGY, 0);
  assert.ok(els.every((e) => e.customData?.author === COACH_AUTHOR));
});

test("nothing lands left of the offset", () => {
  // The coach draws in its own lane, beside the candidate's work, never on it.
  const els = layoutTopology(TOPOLOGY, 1200);
  assert.ok(els.filter((e) => e.type === "rectangle").every((e) => e.x >= 1200));
});

test("no two boxes overlap", () => {
  const boxes = layoutTopology(TOPOLOGY, 0).filter((e) => e.type === "rectangle");
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      const apart =
        a.x + a.width! <= b.x || b.x + b.width! <= a.x ||
        a.y + a.height! <= b.y || b.y + b.height! <= a.y;
      assert.ok(apart, `${a.label?.text} overlaps ${b.label?.text}`);
    }
  }
});

test("arrows bind to node ids, not to coordinates", () => {
  const arrows = layoutTopology(TOPOLOGY, 0).filter((e) => e.type === "arrow");
  assert.deepEqual(arrows.map((a) => [a.start?.id, a.end?.id]), [["app", "cache"], ["app", "db"]]);
});

test("an edge referencing a missing node is dropped, not drawn into the void", () => {
  const els = layoutTopology(
    { nodes: [{ id: "a", label: "A" }], edges: [{ from: "a", to: "ghost" }] },
    0,
  );
  assert.equal(els.filter((e) => e.type === "arrow").length, 0);
});

test("an empty topology draws nothing", () => {
  assert.deepEqual(layoutTopology({ nodes: [], edges: [] }, 0), []);
});
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd sell && npm test
```

Expected: FAIL — cannot resolve `./layout.ts`.

- [ ] **Step 4: Write the implementation**

Create `sell/lib/layout.ts`:

```ts
/* The model emits topology and never coordinates. A model placing shapes by
   hand produces a tangle, so layout lives here where it can be tested. */

import dagre from "@dagrejs/dagre";
import { COACH_AUTHOR } from "./board";

export type Topology = {
  nodes: { id: string; label: string }[];
  edges: { from: string; to: string; label?: string }[];
};

export type ExcalidrawSkeleton = {
  type: string;
  id?: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  label?: { text: string };
  start?: { id: string };
  end?: { id: string };
  customData?: { author: string };
};

const W = 160;
const H = 70;

export function layoutTopology(topology: Topology, offsetX: number): ExcalidrawSkeleton[] {
  if (!topology.nodes.length) return [];

  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "LR", nodesep: 60, ranksep: 110 });
  g.setDefaultEdgeLabel(() => ({}));
  for (const n of topology.nodes) g.setNode(n.id, { width: W, height: H });

  const ids = new Set(topology.nodes.map((n) => n.id));
  /* An edge to a node the model never declared is a hallucinated endpoint.
     Dropping it beats drawing an arrow into empty space. */
  const edges = topology.edges.filter((e) => ids.has(e.from) && ids.has(e.to));
  for (const e of edges) g.setEdge(e.from, e.to);

  dagre.layout(g);

  const boxes: ExcalidrawSkeleton[] = topology.nodes.map((n) => {
    const { x, y } = g.node(n.id);
    return {
      type: "rectangle",
      id: n.id,
      x: offsetX + x - W / 2,
      y: y - H / 2,
      width: W,
      height: H,
      label: { text: n.label },
      customData: { author: COACH_AUTHOR },
    };
  });

  const arrows: ExcalidrawSkeleton[] = edges.map((e) => ({
    type: "arrow",
    x: 0,
    y: 0,
    start: { id: e.from },
    end: { id: e.to },
    ...(e.label ? { label: { text: e.label } } : {}),
    customData: { author: COACH_AUTHOR },
  }));

  return [...boxes, ...arrows];
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd sell && npm test
```

Expected: all PASS.

- [ ] **Step 6: Render it on the board**

In `sell/components/Board.tsx`, accept the imperative API and expose a draw method. In `sell/app/playground/page.tsx`, handle the message:

```tsx
if (msg?.type === "draw") {
  const { convertToExcalidrawElements } = await import("@excalidraw/excalidraw");
  const api = boardApi.current as {
    getSceneElements: () => readonly { x: number; width?: number }[];
    updateScene: (s: { elements: unknown[] }) => void;
  };
  const existing = api.getSceneElements();
  /* Its own lane: right of everything the candidate has drawn. */
  const rightEdge = existing.reduce((m, e) => Math.max(m, e.x + (e.width ?? 0)), 0);
  const skeleton = layoutTopology((msg as { topology: Topology }).topology, rightEdge + 160);
  api.updateScene({
    elements: [...existing, ...convertToExcalidrawElements(skeleton as never)],
  });
}
```

- [ ] **Step 7: Verify the loop closes**

Run the service and the client. Ask the coach out loud to draw the read path. Expected: a legible diagram appears **to the right of** your drawing. Then draw one more box yourself and confirm the coach's next reading of the board does **not** list its own boxes as yours — that is Task 6's exclusion working end to end, and it is the failure this whole tagging scheme exists to prevent.

- [ ] **Step 8: Commit**

```bash
git add sell/lib/layout.ts sell/lib/layout.test.ts sell/components/Board.tsx sell/app/playground/page.tsx sell/package.json sell/package-lock.json
git commit -m "feat: the coach draws in its own lane, laid out rather than placed"
```

---

### Task 13: The session cap, and writing down what shipped

**Files:**
- Create: `playground/tests/test_cap.py`
- Modify: `playground/session.py`
- Modify: `playground/server.py`
- Modify: `sell/app/playground/page.tsx`
- Modify: `sell/PROGRESS.md`

**Interfaces:**
- Consumes: `Session`, `VoiceConfig`.
- Produces: `Session.remaining_secs(now: float) -> float`, `Session.expired(now: float) -> bool`, `Session.start(now: float) -> None`.

- [ ] **Step 1: Write the failing test**

Create `playground/tests/test_cap.py`:

```python
import unittest

from playground.config import VoiceConfig
from playground.session import Session


class TestSessionCap(unittest.TestCase):
    """Voice bills by the minute, so the session ends whether or not anyone
    remembers to stop it. Announced at the start, never enforced silently."""

    def setUp(self):
        self.s = Session(VoiceConfig(session_cap_secs=600))
        self.s.start(now=1000.0)

    def test_a_fresh_session_has_the_full_budget(self):
        self.assertEqual(self.s.remaining_secs(now=1000.0), 600)

    def test_time_spent_comes_off_the_budget(self):
        self.assertEqual(self.s.remaining_secs(now=1060.0), 540)

    def test_it_expires_at_the_cap(self):
        self.assertTrue(self.s.expired(now=1600.0))

    def test_it_does_not_expire_early(self):
        self.assertFalse(self.s.expired(now=1599.0))

    def test_remaining_never_goes_negative(self):
        self.assertEqual(self.s.remaining_secs(now=9999.0), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: FAIL — `Session` has no attribute `start`.

- [ ] **Step 3: Write the implementation**

Add to `playground/session.py`:

```python
    def start(self, now: float) -> None:
        self._started_at = now

    def remaining_secs(self, now: float) -> float:
        started = getattr(self, "_started_at", None)
        if started is None:
            return self.config.session_cap_secs
        return max(0.0, self.config.session_cap_secs - (now - started))

    def expired(self, now: float) -> bool:
        return self.remaining_secs(now) <= 0
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 5: Enforce it, and announce it**

In `server.py`, `session.start(now=time.monotonic())` when the worker starts, and a background task that switches to the coach at 80% of the cap and cancels the worker at 100%.

In `page.tsx`, show the cap before the session begins, not when it bites:

```tsx
<p className="cap-note">
  Sessions run up to 12 minutes. The interviewer hands over to the coach before
  time is up, so you always get the walkthrough.
</p>
```

- [ ] **Step 6: Verify every failure mode by causing it**

Run each and confirm the stated behaviour:

```bash
# 1. Service down: the rep still grades.
cd sell && npm run dev          # playground NOT running
#    → open the rep, type an answer, grade it. Works.
#    → /playground/ shows "voice service unreachable", no crash.

# 2. Mic denied: deny in the browser prompt.
#    → the control reports unavailable, the keyboard still works.

# 3. Bad key: OPENAI_API_KEY=sk-broken uvicorn ...
#    → the client reports it plainly; the page does not hang on a spinner.

# 4. Cap: PLAYGROUND_SESSION_CAP_SECS=60 uvicorn ...
#    → handover happens before the cut, and the cut happens.
```

- [ ] **Step 7: Run everything**

```bash
cd playground && .venv/bin/python -m unittest discover -s tests -v
cd ../sell && npm test && npm run lint && npm run build
```

Expected: all Python tests PASS, all `sell` tests PASS, lint clean, export builds.

- [ ] **Step 8: Write the PROGRESS entry**

Add a dated entry to `sell/PROGRESS.md` following the existing format — what shipped, why it was built that way, how it works — and record bugs by **symptom**, because the symptom is what a future session recognises. Cover at minimum:

- Pipecat 1.7.0 moved VAD out of `TransportParams` into a pipeline processor and turn detection into `UserTurnStrategies`; `PipelineTask` is deprecated in favour of `PipelineWorker`. Anyone reading an older tutorial will write code that does not run.
- The board is read as a graph, not a screenshot, and why: diffability is what makes a coach that unsticks people possible.
- The coach's elements carry `customData.author === "coach"` and the extractor excludes them. Symptom if this breaks: **the coach starts praising components the candidate never drew.**
- The interviewer's context holds no answer key, tested in `test_personas.py`. Symptom if this breaks: **the interviewer starts helping.**
- `playground/rep.py` duplicates `sell/lib/rep.ts` because Python cannot import TypeScript; `test_personas.py` fails if they drift.

Then tick the `Playground unspecified` open item in the same file and point it at the spec.

- [ ] **Step 9: Commit**

```bash
git add playground sell/app/playground sell/PROGRESS.md
git commit -m "feat: session cap, verified failure modes, and the progress entry"
```

---

## Self-Review

Checked against `docs/superpowers/specs/2026-08-21-playground-design.md`:

| spec section | task |
|---|---|
| Dictation, hands-free, into the recall textarea | 3, 4, 5 |
| Cascaded STT/LLM/TTS, not speech-to-speech | 11 |
| `SmallWebRTCTransport`, no vendor | 3 |
| Silero + SmartTurn, both local | 3, 11 |
| `stop_secs` / `min_volume` as tuned knobs | 2, and the listen steps in 3 and 11 |
| Dictation waits longer than conversation | 2 (enforced as an invariant) |
| Excalidraw, elements read as a graph | 6, 8 |
| Diffable, debounced, sent only on change | 7, 8 |
| One board message, replaced in place | 9 |
| Coach elements tagged and excluded | 6, 12 |
| Freehand counted as `unreadable`, not guessed | 6, 9 |
| `draw_diagram` topology-only, dagre lays it out | 11, 12 |
| Coach draws in its own lane | 12 |
| Two personas, interviewer has no answer key | 10, 11 |
| Audible handoff, different voice | 2, 11 |
| One rep (p1c06) scope | 10 |
| Failure modes, rep survives the service being down | 5, 13 |
| Session cap, announced up front | 13 |
| AGENTS.md four pipelines | 1 |
| PROGRESS entry with symptoms | 13 |

Not covered by a task, deliberately: **cost verification.** The spec says current OpenAI per-minute pricing is checked live before a per-minute model is committed to. No task commits to one, so nothing here depends on it. Do that check when the hosting question is taken up, not before.

Types used in later tasks are defined earlier: `BoardGraph`/`BoardElement`/`COACH_AUTHOR` (Task 6) are consumed by Tasks 7, 8, 12. `VoiceConfig` (Task 2) by 3, 11, 13. `Session` (Task 11) by 13. `appendTranscript`/`connectVoice` (Task 4) by 5 and 8.
