"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import asyncio
import os
from typing import NamedTuple

from dotenv import load_dotenv
from fastapi import FastAPI
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.workers.runner import WorkerRunner
from pydantic import BaseModel

from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker

load_dotenv()

app = FastAPI(title="HLD Gym Playground")


@app.get("/health")
async def health() -> dict:
    """Reports whether a key is loaded. Never reports what the key is."""
    return {"ok": True, "key_loaded": bool(os.getenv("OPENAI_API_KEY"))}


class OfferRequest(BaseModel):
    """A WebRTC SDP offer. A Pydantic model, not a bare dict, so a missing or
    malformed field fails as a clean 422 at the boundary instead of a 500 from
    an unguarded dict index."""

    sdp: str
    type: str
    pc_id: str | None = None


class _Session(NamedTuple):
    connection: SmallWebRTCConnection
    runner: WorkerRunner
    task: asyncio.Task


# Voice bills by the minute. A session must stop costing money the moment its
# connection is truly gone, not just when it hangs up politely.
_sessions: dict[str, _Session] = {}


async def _end_session(conn: SmallWebRTCConnection) -> None:
    """Runs on every terminal connection state: "closed" (clean hangup, or the
    tail of any close() -- including the connect-timeout path) and "failed"
    (ICE failure, which the installed aiortc/pipecat state machine does not
    reliably also report as "closed"). Deliberately excludes "disconnected":
    that event only fires mid-renegotiate-restart, while this same session is
    about to keep running under a fresh peer connection, not while it's dead.

    Idempotent: `_sessions.pop` returns None on a second call for the same
    pc_id, and `WorkerRunner.cancel` is documented idempotent too, so this
    firing twice (e.g. once from "failed", once from "closed" moments later)
    is a no-op the second time, not an error.
    """
    session = _sessions.pop(conn.pc_id, None)
    if session is not None:
        await session.runner.cancel(reason="connection ended")


@app.post("/api/offer")
async def offer(request: OfferRequest) -> dict:
    """One WebRTC connection per session. mode=dictation for now."""
    if request.pc_id and request.pc_id in _sessions:
        session = _sessions[request.pc_id]
        await session.connection.renegotiate(sdp=request.sdp, type=request.type)
        return session.connection.get_answer()

    connection = SmallWebRTCConnection()
    await connection.initialize(sdp=request.sdp, type=request.type)

    worker = build_dictation_worker(connection, VoiceConfig.from_env())
    runner = WorkerRunner(handle_sigint=False)
    task = asyncio.create_task(runner.run(worker))

    answer = connection.get_answer()
    _sessions[answer["pc_id"]] = _Session(connection=connection, runner=runner, task=task)

    connection.add_event_handler("closed", _end_session)
    connection.add_event_handler("failed", _end_session)

    return answer
