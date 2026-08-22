"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import asyncio
import logging
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

from playground import grading
from playground.auth import (
    AuthError,
    GoogleUnavailableError,
    sign_token,
    token_secret_from_env,
    verify_google_id_token,
    verify_token,
)
from playground.config import VoiceConfig
from playground.pipelines import build_dictation_worker, build_playground_worker
from playground.relay import server_message
from playground.session import Session

Mode = Literal["dictation", "playground", "diagnostic"]

logger = logging.getLogger(__name__)

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
    never a 500 -- see playground/auth.py's AuthError. Google being
    unreachable (GoogleUnavailableError, a TransportError fetching its own
    certs) is a 503, not a 401 -- a learner's credential wasn't rejected,
    Google just couldn't be asked.

    Neither exception's own message reaches the caller: AuthError's message
    can carry google-auth's raw exception text, which embeds the caller's
    *own* submitted credential (confirmed live -- a malformed token's
    message was "Wrong number of segments in token: b'...'" with the token
    inline). Nothing secret leaks, since it's the caller's own input, but
    reflecting a credential into devtools, proxy logs and error trackers is
    a habit not worth forming. The real detail is logged server-side only;
    the response body gets a fixed message."""
    config = VoiceConfig.from_env()
    if not config.google_client_id:
        # Without this, google-auth compares the token's `aud` against [""],
        # mismatches every real credential and raises -> AuthError -> 401
        # "Google sign-in failed": every learner told their own Google
        # account was rejected, when the actual cause is an env var the
        # operator never set. Unlike PLAYGROUND_TOKEN_SECRET this does not
        # refuse to boot, because mode=dictation needs no sign-in at all and
        # a dictation-only deploy is legitimate -- it fails on the one
        # endpoint that actually needs it, and says which side is broken.
        logger.error("PLAYGROUND_GOOGLE_CLIENT_ID is unset; /api/login cannot verify anything")
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    try:
        email = verify_google_id_token(request.id_token, config.google_client_id)
    except GoogleUnavailableError as e:
        logger.warning("Google sign-in temporarily unavailable: %s", e)
        raise HTTPException(
            status_code=503, detail="Google sign-in is temporarily unavailable"
        ) from e
    except AuthError as e:
        logger.warning("Google sign-in rejected: %s", e)
        raise HTTPException(status_code=401, detail="Google sign-in failed") from e
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
        # One fixed message for every rejection, the detail to the log --
        # the same rule login() states at length above, for the same two
        # reasons. Today verify_token only raises fixed strings, so nothing
        # leaks; str(e) here still handed a caller a four-way oracle
        # (forged vs expired vs malformed vs no email), and the first
        # AuthError raised with dynamic text on this path would have become
        # a reflection bug with no second review.
        logger.warning("Playground session token rejected: %s", e)
        raise HTTPException(status_code=401, detail="sign in required") from e


def _require_answer(connection: SmallWebRTCConnection) -> dict:
    """The SDP answer, or a 503. SmallWebRTCConnection.get_answer() returns
    None whenever its `_answer` is unset, and both call sites below used it
    unchecked: the new-session path then raised TypeError on
    answer["pc_id"], and the renegotiate path -- worse -- returned HTTP 200
    with a body of literally `null`, which the browser turns into
    setRemoteDescription(null) inside its own retry loop with no status left
    to report."""
    answer = connection.get_answer()
    if answer is None:
        raise HTTPException(status_code=503, detail="voice service unavailable")
    return answer


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
    # The mode this session was actually created with -- not to be confused
    # with the `mode` query param a *later* request to the same pc_id can
    # claim. offer()'s renegotiate branch (a repeat POST carrying an
    # existing pc_id) used to gate only on that later request's own claimed
    # mode, which let an unauthenticated `?mode=dictation` renegotiate onto
    # a *playground* session's pc_id and take over its live, billing
    # connection with no token at all. Gating on this field instead --
    # what the session actually is, fixed at creation and never taken from
    # an untrusted later request -- closes that. See offer().
    mode: Mode
    # The verified email that authenticated this session's creation --
    # None for dictation, which authenticates nothing. Recorded so the
    # renegotiate branch below can require the *same* identity on a repeat
    # request, not just *some* valid token: without this, any Google
    # account -- there is no allowlist -- could renegotiate any other
    # signed-in user's live playground session, since a valid-but-unrelated
    # token satisfied _authenticate_playground_request just fine. A
    # security review demonstrated this live before it shipped.
    email: str | None = None
    # None for dictation, which has no Session and so nothing to cap. Held
    # here for the same reason `task` is (a task with no other reference can
    # be garbage-collected mid-run) and so _end_session can cancel it on a
    # hangup instead of leaving it to notice on its next poll.
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
        # Not when _enforce_cap is calling this on itself at the end of its
        # own loop: cancelling the running task makes the very next await --
        # runner.cancel() on the line below -- raise CancelledError, and the
        # worker would never actually be torn down.
        if session.cap_task is not None and session.cap_task is not asyncio.current_task():
            session.cap_task.cancel()
        await session.runner.cancel(reason="connection ended")


# _run_diagnostic_end sets session.round_over before grading, but the session
# stays registered in _sessions until its own `finally` runs -- so
# _enforce_diagnostic_cap's tail (which reads round_over to decide whether to
# run the end path itself or just tear down) has to be able to tell "an end
# path is in flight, grading" apart from "gone". Bounding grading is what
# keeps that window finite: grading.grade already never raises, but nothing
# upstream previously bounded how long it could hang against a slow or
# wedged provider, and the whole point of an in-flight end path owning its
# own teardown is that it actually finishes.
_GRADING_TIMEOUT_SECS = 45.0


async def _run_diagnostic_end(
    session: Session,
    connection: SmallWebRTCConnection,
    config: VoiceConfig,
    flush_secs: float = 1.0,
) -> None:
    """The one end path for all three diagnostic triggers: end_round, the
    client's finish control, and the cap. round_over makes it first-wins --
    the loop is single-threaded and there is no await between the check and
    the set, so two triggers cannot both grade. The teardown lives in a
    finally so a surprise in grading or delivery can never leave a live
    session billing with nobody coming back for it; grading.grade itself
    never raises, the finally is belt for the braces.

    The grade call is bounded by _GRADING_TIMEOUT_SECS: grading.grade itself
    never raises, but with no bound here a hung provider call would hang this
    function's own teardown along with it -- and _enforce_diagnostic_cap's
    tail deliberately stands down (does nothing) once it sees round_over is
    already set, trusting this function's finally to be the one that tears
    the session down. A timeout renders the honest lost-map line (None),
    same as a failed grading attempt does."""
    if session.round_over:
        return
    session.round_over = True
    try:
        turns = session.context.get_messages() if session.context is not None else []
        board = session.board.messages()
        board_text = board[0]["content"] if board else ""
        try:
            moments = await asyncio.wait_for(
                grading.grade(turns, board_text, model=config.llm_model),
                _GRADING_TIMEOUT_SECS,
            )
        except asyncio.TimeoutError:
            moments = None
        connection.send_app_message(
            server_message({"type": "failure_map", "moments": moments})
        )
        # ponytail: fixed flush sleep before teardown; a delivery ack from the
        # client is the upgrade if maps ever go missing in practice.
        await asyncio.sleep(flush_secs)
    finally:
        await _end_session(connection)


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
        # handover_at is strictly positive, so this is not a clamp and never
        # was -- it read like one, in the one function whose sleep maths was
        # already got wrong once.
        sleep_for = remaining if handed_over else remaining - handover_at
        await asyncio.sleep(min(sleep_for, 1.0) if sleep_for > 0 else 0.05)
    await _end_session(connection)


async def _enforce_diagnostic_cap(
    connection: SmallWebRTCConnection,
    worker: PipelineWorker,
    pg_session: Session,
    config: VoiceConfig,
    closing_secs: float = 30.0,
) -> None:
    """The diagnostic sibling of _enforce_cap. No coach handover ever --
    switch_to_coach() raises for a diagnostic session (see
    playground/session.py), so this must never call it. Instead,
    closing_secs before the cap the interviewer is told time is up
    (Session.closing + push_context, then one LLMRunFrame: the same
    announced-not-silent mechanism the sprint handover uses), which normally
    ends the round via end_round well before the cap. If it does not, the
    cap runs the end path itself: the candidate still gets their map, just
    without a spoken goodbye. Same poll cadence and sleep maths as
    _enforce_cap, for the same recorded reasons.

    closing_secs is clamped to at most 20% of the session's own cap
    (mirroring _enforce_cap's 80%-elapsed handover point) so an
    env-shortened diagnostic_cap_secs can't make closing_secs bigger than
    the whole round -- which would open the round already announcing "time
    is up".

    The tail below has three outcomes, not two: still registered with the
    round not over (nobody else ended it -- this cap task owns the end
    path); no longer registered (the visitor disconnected -- just tear
    down); or still registered *with* round_over already set. That third
    case is a live race, not a missed one: _run_diagnostic_end sets
    round_over before it grades, and only pops the session (in its own
    finally) once grading, delivery, and the flush sleep are done -- which
    can take longer than the time left on the cap when the closing turn was
    only just requested. Calling _end_session here in that window would kill
    the connection out from under send_app_message before the map ever
    reaches the client. round_over already means an end path is in flight
    and owns its own teardown (bounded by _GRADING_TIMEOUT_SECS, so it is
    guaranteed to actually run that finally) -- so this task simply stands
    down and lets it finish."""
    closing = min(closing_secs, pg_session.cap_secs * 0.2)
    closing_requested = False
    while connection.pc_id in _sessions:
        now = time.monotonic()
        if pg_session.expired(now):
            break
        remaining = pg_session.remaining_secs(now)
        if not closing_requested and remaining <= closing:
            if not pg_session.round_over:
                pg_session.closing = True
                pg_session.push_context()
                await worker.queue_frames([LLMRunFrame()])
            closing_requested = True
        sleep_for = remaining if closing_requested else remaining - closing
        await asyncio.sleep(min(sleep_for, 1.0) if sleep_for > 0 else 0.05)
    if connection.pc_id in _sessions and not pg_session.round_over:
        await _run_diagnostic_end(pg_session, connection, config)
    elif connection.pc_id not in _sessions:
        await _end_session(connection)
    # else: an end path already set round_over and owns the teardown -- its
    # finally runs on exception and cancellation alike, so nobody-comes-back
    # is on it, not on this task racing it to _end_session.


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


def _extract_finish(message: object) -> bool:
    """True for the client's finish control: {"type": "client-message",
    "data": {"t": "finish", ...}}. Same envelope walk as
    _extract_board_graph, same reason it is module-level and pure."""
    if not (isinstance(message, dict) and message.get("type") == "client-message"):
        return False
    data = message.get("data")
    return isinstance(data, dict) and data.get("t") == "finish"


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
    mode=dictation stays completely open: no token, no gate, by design.

    The gate checks the *existing* session's own recorded mode, not just
    this request's mode param, precisely because request.pc_id lets a
    caller renegotiate an existing connection below without going through
    the "new session" path at all. Gating on the param alone let
    `?mode=dictation` (no token required) renegotiate onto a *playground*
    session's pc_id and take over its live, billing connection -- a
    security review caught this before it shipped. A pc_id is a
    `uuid4().hex` an attacker cannot guess, and today's default bind to
    127.0.0.1 keeps it off the network entirely, but neither of those is an
    auth check, and sell/PROGRESS.md records that both evaporate the day
    this is hosted.

    Authenticated is not the same as authorized: a valid token proves *a*
    Google account signed in, not that it is *this session's* account, and
    with no allowlist any Google account is the entire set a token can come
    from. So a renegotiate of an existing playground session also checks
    the verified email against the one recorded on the session at creation
    (_Session.email) -- a second learner's own perfectly valid token must
    not renegotiate someone else's live session. A security review
    demonstrated this live before it shipped too.

    mode=diagnostic is gated identically to mode=playground -- it spends
    real OpenAI credit per minute exactly the same way -- and the
    renegotiate identity check above now keys on "not dictation" rather than
    "playground" specifically, for the same recorded reasons, now that a
    second metered mode exists."""
    existing = _sessions.get(request.pc_id) if request.pc_id else None
    authenticated_email = None
    if mode in ("playground", "diagnostic") or (
        existing is not None and existing.mode != "dictation"
    ):
        authenticated_email = _authenticate_playground_request(authorization)

    if existing is not None:
        if existing.mode != "dictation" and authenticated_email != existing.email:
            raise HTTPException(status_code=403, detail="not your session")
        await existing.connection.renegotiate(sdp=request.sdp, type=request.type)
        return _require_answer(existing.connection)

    connection = SmallWebRTCConnection()
    await connection.initialize(sdp=request.sdp, type=request.type)

    # Both filled in inside the try, both read by the cleanup below, so both
    # have to exist before the first line that can throw.
    runner: WorkerRunner | None = None
    registered_pc_id: str | None = None
    try:
        # Everything from here down can fail before the connection is ever
        # registered in _sessions: VoiceConfig.from_env() on a malformed
        # PLAYGROUND_* env var or the dictation-threshold/distinct-voice
        # invariants, build_*_worker loading models (two, for playground),
        # or get_answer(). Any of them must still tear down the
        # already-initialize()d connection, or it leaks a live peer
        # connection nothing will ever clean up.
        config = VoiceConfig.from_env()
        if mode in ("playground", "diagnostic"):
            if mode == "diagnostic":

                async def _on_round_end(s: Session) -> None:
                    await _run_diagnostic_end(s, connection, config)

                worker, pg_session = build_playground_worker(
                    connection, config, kind="diagnostic", on_round_end=_on_round_end
                )
            else:
                worker, pg_session = build_playground_worker(connection, config)
            pg_session.start(now=time.monotonic())

            @connection.event_handler("app-message")
            async def _on_app_message(conn: SmallWebRTCConnection, message: object) -> None:
                _apply_board_message(pg_session, message)
                if pg_session.kind == "diagnostic" and _extract_finish(message):
                    # Inline on purpose (up to ~46s): the round is over, and
                    # nothing else uses this handler in the meantime -- a
                    # second finish (or a stray board message) arriving while
                    # this await is in flight just re-enters _run_diagnostic_end,
                    # which returns immediately on round_over. Contrast
                    # _end_diagnostic_round (pipelines.py), which spawns a
                    # task for the same work because it runs inside the
                    # pipeline's own processing, where a multi-second await
                    # would block the pipeline itself.
                    await _run_diagnostic_end(pg_session, connection, config)
        else:
            # Dictation has no Session, no LLM turn to hand over -- so
            # nothing for _enforce_cap to do.
            worker = build_dictation_worker(connection, config)
            pg_session = None

        runner = WorkerRunner(handle_sigint=False)
        task = asyncio.create_task(runner.run(worker))

        answer = _require_answer(connection)
        registered_pc_id = answer["pc_id"]
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
        _sessions[registered_pc_id] = _Session(
            connection=connection,
            runner=runner,
            task=task,
            mode=mode,
            email=authenticated_email,
            cap_task=None,
        )
        if pg_session is not None:
            if pg_session.kind == "diagnostic":
                cap_task = asyncio.create_task(
                    _enforce_diagnostic_cap(connection, worker, pg_session, config)
                )
            else:
                cap_task = asyncio.create_task(_enforce_cap(connection, worker, pg_session))
            _sessions[registered_pc_id] = _sessions[registered_pc_id]._replace(cap_task=cap_task)

        connection.add_event_handler("closed", _end_session)
        connection.add_event_handler("failed", _end_session)
    except BaseException:
        # BaseException, not Exception: a request cancelled mid-request
        # raises asyncio.CancelledError, a BaseException -- and loading
        # SmartTurn plus Silero is exactly the slow window where a client
        # giving up is most likely. Re-raise once cleanup is done; this
        # tears down, it does not swallow.
        #
        # Disconnecting the peer is not the whole teardown. By the time
        # _require_answer() can raise, create_task(runner.run(worker)) has
        # already started a full STT+LLM+TTS pipeline that nothing else will
        # ever cancel: the "closed"/"failed" handlers are registered further
        # down and so are not installed yet on any of these paths. Same for
        # a throw after _sessions registration -- the entry would never be
        # popped, and its cap task would poll for the whole session cap.
        if registered_pc_id is not None:
            leaked = _sessions.pop(registered_pc_id, None)
            if leaked is not None and leaked.cap_task is not None:
                leaked.cap_task.cancel()
        if runner is not None:
            await runner.cancel(reason="offer failed")
        await connection.disconnect()
        raise

    return answer
