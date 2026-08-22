"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import asyncio
import os
import time
from typing import Literal, Mapping, NamedTuple

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.worker import PipelineWorker
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.workers.runner import WorkerRunner
from pydantic import BaseModel

from playground.auth import (
    AuthError,
    sign_token,
    token_secret_from_env,
    verify_google_id_token,
    verify_token,
)
from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker, build_playground_worker
from playground.session import Session

Mode = Literal["dictation", "playground"]

load_dotenv()

app = FastAPI(title="HLD Gym Playground")


def _allowed_origins(env: Mapping[str, str] | None = None) -> list[str]:
    """PLAYGROUND_ALLOWED_ORIGINS, comma-separated -- same env-var convention
    VoiceConfig.from_env() uses, kept as a standalone function rather than a
    VoiceConfig field because CORS is an app-wide policy fixed at startup,
    not a per-session tuning knob VoiceConfig.from_env() re-reads on every
    /api/offer. Defaults to the two localhost origins `sell` actually runs
    from in dev (npm run dev is :3000; 127.0.0.1 is the same server, some
    browsers resolve it separately). A wildcard was the first version of
    this and was too broad: the service holds no cookie/session to leak (see
    the comment on app.add_middleware below), but with allow_origins="*"
    *any* page open in the same browser while this service is running
    locally could open a session against it and spend the visitor's OpenAI
    quota, not just sell's own pages. Override to widen this deliberately
    if the service is ever hosted somewhere other than localhost -- but "*"
    itself is rejected outright, raising here at import time (before any
    session exists, so failing loudly is free): it is the one value that
    silently undoes this whole guard, and it is also the first thing anyone
    reaching for "allow everything" would type. List the real origins."""
    src = os.environ if env is None else env
    raw = src.get(
        "PLAYGROUND_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    )
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError(
            'PLAYGROUND_ALLOWED_ORIGINS="*" is rejected: a wildcard lets any '
            "page a visitor has open spend their OpenAI quota through this "
            "service. List the origins that should be allowed, explicitly."
        )
    return origins


# sell and playground are two different origins by design -- localhost:3000
# vs :7860 in dev, and a different deployment target in production, per
# NEXT_PUBLIC_VOICE_URL in sell/lib/voice.ts. Found during this task's own
# failure-mode verification: no browser had ever actually reached a live
# instance of this service before (every earlier task's "service running"
# checks were reasoned through, not run, for lack of an OpenAI key), and the
# preflight was rejected outright, before the SDP offer or any mic prompt.
# allow_credentials is never set (default False), so nothing here recreates
# the auth this product has deliberately not built yet (root AGENTS.md: "No
# backend, no auth, no database until someone pays") -- allow_origins is
# still narrowed to _allowed_origins() rather than "*", because a wildcard
# lets any page a visitor has open spend their OpenAI quota through this
# service, not just sell's.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Signs and verifies our own session tokens (see playground/auth.py). Read
# once, at import time -- exactly like _allowed_origins() above, a bad value
# here must stop the service before it ever serves a request, not fail
# request by request. token_secret_from_env() has no fallback default, unlike
# every other PLAYGROUND_* knob: a default signing secret would let anyone
# forge a session, so a missing one raises here rather than silently picking
# one.
_TOKEN_SECRET = token_secret_from_env()


@app.get("/health")
async def health() -> dict:
    """Reports whether a key is loaded. Never reports what the key is."""
    return {"ok": True, "key_loaded": bool(os.getenv("OPENAI_API_KEY"))}


class LoginRequest(BaseModel):
    """The Google ID token straight from Google Identity Services, in the
    browser -- see sell/lib/auth.ts. Never stored past this one
    verification: it is exchanged for our own token below and then
    forgotten."""

    id_token: str


class LoginResponse(BaseModel):
    token: str
    email: str


@app.post("/api/login")
async def login(request: LoginRequest) -> LoginResponse:
    """Exchanges a verified Google ID token for our own session token.
    Google's expires in about an hour; ours lasts PLAYGROUND_SESSION_TTL_SECS
    (7 days by default) so a returning learner isn't re-prompted every
    session. Anyone with a Google account is let in -- there is no allowlist,
    a decision made knowingly (see sell/PROGRESS.md). Verification failures
    (bad signature, wrong audience, expired, no email claim) are all 401,
    never a 500 -- see playground/auth.py's AuthError."""
    config = VoiceConfig.from_env()
    try:
        email = verify_google_id_token(request.id_token, config.google_client_id)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    token = sign_token(email, _TOKEN_SECRET, now=time.time(), ttl_secs=config.session_ttl_secs)
    return LoginResponse(token=token, email=email)


def _authenticate_playground_request(authorization: str | None) -> str:
    """Gates mode=playground -- called before any connection or session
    exists, so a rejected request creates nothing and bills nothing (voice
    bills by the minute the moment a session starts). mode=dictation never
    calls this; see offer()'s mode check below -- that is a deliberate
    decision (docs/superpowers/specs/2026-08-21-playground-design.md), not
    an oversight. Every rejection -- missing header, wrong scheme, expired,
    tampered, malformed -- is a 401, never a 500; see playground/auth.py's
    AuthError."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="sign in required")
    try:
        return verify_token(token, _TOKEN_SECRET, now=time.time())
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


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
    # None for dictation, which has no Session and so nothing to cap. Held
    # here for the same reason `task` is: a task with no other reference
    # can be garbage-collected mid-run.
    cap_task: asyncio.Task | None = None


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


async def _enforce_cap(
    connection: SmallWebRTCConnection, worker: PipelineWorker, pg_session: Session
) -> None:
    """The other half of the session cap (see Session.start/remaining_secs/
    expired). Handover first, always: a learner cut off mid-round with no
    walkthrough is the one outcome the cap must never produce, so the
    interviewer becomes the coach at 80% of the cap, with a full round left
    to actually give the walkthrough, and only the leftover 20% is spent
    before the cut at 100%.

    Polls on a short sleep rather than sleeping once for the full remaining
    time, so a session that disconnects on its own partway through (the
    normal case) is noticed and this task exits instead of idling for up to
    12 minutes doing nothing. Each sleep is capped at the time left until the
    handover instant itself, not just at a flat 1s -- a flat cap alone lets
    the loop step clean over a short handover window (20% of a several-second
    test cap is itself under a second) and reach expiry having never handed
    over at all, which is exactly the outcome this function exists to
    prevent. Caught by running this against a several-second cap, per the
    task brief, rather than trusting it at the 12-minute default where the
    window is wide enough to hide the bug.

    The cut reuses _end_session -- the same teardown the "closed"/"failed"
    handlers already use for a disconnect -- rather than a second way to
    tear a session down. Idempotent for the same reason theirs is: if the
    learner hangs up on their own first, _end_session has already popped
    this pc_id, and calling it again here is a no-op.

    Gated on pg_session.mode, not just the local handed_over flag: end_round
    switches a session to coach mode on its own, independently of the cap,
    and nothing ends the connection when it does -- a round that finishes
    itself well before 80% of the cap elapses is routine, not exotic. Without
    the mode check, arriving at the handover mark already in coach mode would
    still queue a second, unprompted LLMRunFrame with no user turn behind
    it: the coach interjecting out of nowhere mid-conversation. switch_to_coach()
    and push_context() are harmless to re-run (idempotent), but the run frame
    is not, so the whole block -- not just handed_over -- is skipped once the
    session is already there.
    """
    handover_at = pg_session.config.session_cap_secs * 0.2  # remaining_secs at 80% elapsed
    handed_over = False
    while connection.pc_id in _sessions:
        now = time.monotonic()
        if pg_session.expired(now):
            break
        remaining = pg_session.remaining_secs(now)
        if not handed_over and remaining <= handover_at:
            if pg_session.mode != "coach":
                pg_session.switch_to_coach()
                pg_session.push_context()
                if pg_session.tts is not None:
                    await pg_session.tts.set_voice(pg_session.tts_voice())
                # Nothing else prompts the LLM here -- unlike end_round,
                # there's no function-call result to trigger the next
                # completion, so the handover has to be asked for explicitly.
                await worker.queue_frames([LLMRunFrame()])
            handed_over = True
        sleep_for = remaining if handed_over else min(remaining, remaining - handover_at)
        await asyncio.sleep(min(sleep_for, 1.0) if sleep_for > 0 else 0.05)
    await _end_session(connection)


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
async def offer(
    request: OfferRequest,
    mode: Mode = "dictation",
    authorization: str | None = Header(default=None),
) -> dict:
    """One WebRTC connection per session. mode is a query param
    (?mode=playground), not a body field -- the client picks it before the
    SDP exchange, see sell/lib/voice.ts. Typed as Literal rather than str so
    an unrecognised mode is a 422 at the boundary (FastAPI/Pydantic validate
    it before the handler body runs) instead of silently falling back to
    dictation -- a mute interviewer with no error is worse than a loud one.

    mode=playground is gated on our own session token (Authorization: Bearer
    <token>, minted by /api/login) -- see _authenticate_playground_request.
    mode=dictation stays completely open: no token, no gate, by design."""
    if mode == "playground":
        _authenticate_playground_request(authorization)

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
            pg_session.start(now=time.monotonic())

            @connection.event_handler("app-message")
            async def _on_app_message(conn: SmallWebRTCConnection, message: object) -> None:
                _apply_board_message(pg_session, message)
        else:
            # Dictation has no Session, no LLM turn to hand over -- so
            # nothing for _enforce_cap to do.
            worker = build_dictation_worker(connection, config)
            pg_session = None

        runner = WorkerRunner(handle_sigint=False)
        task = asyncio.create_task(runner.run(worker))

        answer = connection.get_answer()
        # Registered before the cap task is created, not after: _enforce_cap's
        # `while connection.pc_id in _sessions` reads _sessions on its very
        # first iteration, and asyncio.create_task only *schedules* the
        # coroutine -- it does not run any of it before the next `await`
        # yields control back to the loop. The old order (create_task, then
        # assign into _sessions) only worked because nothing awaited in
        # between; add one later and the cap task would find its own pc_id
        # missing on entry and exit immediately, silently never enforcing
        # the cap. cap_task itself is filled in with _replace() just below,
        # once it exists -- _enforce_cap doesn't read it, only server.py's
        # own teardown paths do, and none of those can run before this
        # function returns.
        _sessions[answer["pc_id"]] = _Session(
            connection=connection, runner=runner, task=task, cap_task=None
        )
        if pg_session is not None:
            cap_task = asyncio.create_task(_enforce_cap(connection, worker, pg_session))
            _sessions[answer["pc_id"]] = _sessions[answer["pc_id"]]._replace(cap_task=cap_task)

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
