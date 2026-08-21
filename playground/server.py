"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import asyncio
import os

from dotenv import load_dotenv
from fastapi import Body, FastAPI
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker

load_dotenv()

app = FastAPI(title="HLD Gym Playground")


@app.get("/health")
async def health() -> dict:
    """Reports whether a key is loaded. Never reports what the key is."""
    return {"ok": True, "key_loaded": bool(os.getenv("OPENAI_API_KEY"))}


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
