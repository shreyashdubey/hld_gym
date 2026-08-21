"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import asyncio
import os
from typing import Literal, NamedTuple

from dotenv import load_dotenv
from fastapi import FastAPI
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.workers.runner import WorkerRunner
from pydantic import BaseModel

from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker, build_playground_worker
from playground.session import Session

Mode = Literal["dictation", "playground"]

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


def _extract_board_graph(message: object) -> dict | None:
    """Pure parser: a raw connection-level "app-message" payload -> the board
    graph dict it carries, or None if this isn't a well-formed board update.

    Inbound client messages arrive at connection-level "app-message" as the
    raw RTVI envelope client.sendClientMessage() produces:
    {"type": "client-message", "data": {"t": <type>, "d": <data>}} -- not the
    flattened {"type": ..., **data} shape this looked like it would be. The
    client sends sendClientMessage("board", {graph}), so the board lives at
    data["d"]["graph"].

    Module-level and side-effect-free so it can be unit-tested directly --
    see test_server.py -- rather than only exercised through a live WebRTC
    connection.

    Returns None both when this isn't a board message at all and when it is
    one but the graph itself isn't a dict: either way there is nothing safe
    to hand BoardContext.update(), and the caller must leave the last good
    board alone rather than replacing it with an empty one."""
    if not (isinstance(message, dict) and message.get("type") == "client-message"):
        return None
    data = message.get("data")
    if not (isinstance(data, dict) and data.get("t") == "board"):
        return None
    payload = data.get("d")
    graph = payload.get("graph") if isinstance(payload, dict) else None
    return graph if isinstance(graph, dict) else None


def _apply_board_message(session: Session, message: object) -> None:
    """Handle one inbound app-message for the board, if it is one.

    Session owns push_context() (see playground/session.py) -- this is the
    second (and last) caller of it, alongside end_round. A malformed or
    unrelated message is a no-op: BoardContext.update() tolerates a
    malformed *graph* by design (missing keys, wrong types, junk entries),
    but a missing/non-dict graph here is a malformed *envelope* one level up,
    and the fix is to leave the board untouched, not to overwrite a good
    board with an empty one."""
    graph = _extract_board_graph(message)
    if graph is None:
        return
    session.board.update(graph)
    session.push_context()


@app.post("/api/offer")
async def offer(request: OfferRequest, mode: Mode = "dictation") -> dict:
    """One WebRTC connection per session. mode is a query param
    (?mode=playground), not a body field -- the client picks it before the
    SDP exchange, see sell/lib/voice.ts. Typed as Literal rather than str so
    an unrecognised mode is a 422 at the boundary (FastAPI/Pydantic validate
    it before the handler body runs) instead of silently falling back to
    dictation -- a mute interviewer with no error is worse than a loud one."""
    if request.pc_id and request.pc_id in _sessions:
        session = _sessions[request.pc_id]
        await session.connection.renegotiate(sdp=request.sdp, type=request.type)
        return session.connection.get_answer()

    connection = SmallWebRTCConnection()
    await connection.initialize(sdp=request.sdp, type=request.type)

    try:
        # Everything from here down can fail before the connection is ever
        # registered in _sessions: VoiceConfig.from_env() on a malformed
        # PLAYGROUND_* env var or the dictation-threshold/distinct-voice
        # invariants, build_*_worker loading models (two, for playground),
        # or get_answer(). Any of them must still tear down the
        # already-initialize()d connection, or it leaks a live peer
        # connection nothing will ever clean up.
        config = VoiceConfig.from_env()
        if mode == "playground":
            worker, pg_session = build_playground_worker(connection, config)

            @connection.event_handler("app-message")
            async def _on_app_message(conn: SmallWebRTCConnection, message: object) -> None:
                _apply_board_message(pg_session, message)
        else:
            worker = build_dictation_worker(connection, config)

        runner = WorkerRunner(handle_sigint=False)
        task = asyncio.create_task(runner.run(worker))

        answer = connection.get_answer()
        _sessions[answer["pc_id"]] = _Session(connection=connection, runner=runner, task=task)

        connection.add_event_handler("closed", _end_session)
        connection.add_event_handler("failed", _end_session)
    except BaseException:
        # BaseException, not Exception: a request cancelled mid-request
        # raises asyncio.CancelledError, a BaseException -- and loading
        # SmartTurn plus Silero is exactly the slow window where a client
        # giving up is most likely. Re-raise once cleanup is done; this
        # tears down, it does not swallow.
        await connection.disconnect()
        raise

    return answer
