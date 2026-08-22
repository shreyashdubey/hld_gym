import asyncio
import os
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import playground.server as server
from playground.auth import AuthError, GoogleUnavailableError, sign_token
from playground.config import VoiceConfig
from playground.server import (
    LoginRequest,
    OfferRequest,
    _Session,
    _allowed_origins,
    _apply_board_message,
    _enforce_cap,
    _extract_board_graph,
    _sessions,
    _TOKEN_SECRET,
    login,
    offer,
)
from playground.session import Session


def _fake_openai_key(test: unittest.TestCase) -> None:
    """A fake OPENAI_API_KEY for the duration of one test, restored after.

    Six classes here used to assign os.environ directly with no tearDown.
    `unittest discover` runs the whole suite in one process, so a later test
    asserting on a *missing* key -- /health reporting key_loaded=False, the
    one property that test exists to check -- would have passed or failed on
    class ordering rather than on the code. The rest of this suite already
    injects mappings (_allowed_origins({}), VoiceConfig.from_env(env)); this
    was the one place that mutated the real environment instead.
    """
    patcher = patch.dict(os.environ, {"OPENAI_API_KEY": "sk-secret-do-not-leak"})
    patcher.start()
    test.addCleanup(patcher.stop)


class TestHealth(unittest.TestCase):
    def setUp(self):
        _fake_openai_key(self)
        from playground.server import app

        self.client = TestClient(app)

    def test_health_reports_key_loaded(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True, "key_loaded": True})

    def test_health_never_echoes_the_key(self):
        r = self.client.get("/health")
        self.assertNotIn("sk-secret-do-not-leak", r.text)


class TestOffer(unittest.TestCase):
    def setUp(self):
        _fake_openai_key(self)
        from playground.server import app

        self.client = TestClient(app)

    def test_malformed_body_is_a_4xx_not_a_500(self):
        """A bare dict indexed with request["sdp"] turns a missing field into
        an unhandled KeyError -> 500. The Pydantic model must catch it first."""
        r = self.client.post("/api/offer", json={"type": "offer"})  # no "sdp"
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)

    def test_an_unrecognised_mode_is_a_4xx_not_a_silent_fallback(self):
        """A typo'd or stale ?mode= must not silently behave like dictation --
        that's a mute interviewer and no error. mode is typed Literal, so
        FastAPI/Pydantic reject it before the handler body (and the fake SDP
        below) is ever touched."""
        r = self.client.post("/api/offer?mode=bogus", json={"sdp": "x", "type": "offer"})
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)


class TestAllowedOrigins(unittest.TestCase):
    """CORS started as allow_origins="*" and was narrowed after this build's
    own verification showed why: a wildcard lets any page a visitor has open
    spend their OpenAI quota through a locally-running service, not just
    sell's. These two properties -- a safe default, and an override that
    actually overrides -- are what stop that regressing silently."""

    def test_defaults_to_the_two_localhost_dev_origins(self):
        self.assertEqual(
            _allowed_origins({}),
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        )

    def test_env_override_replaces_the_default_entirely(self):
        origins = _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "https://hld-gym.vercel.app"})
        self.assertEqual(origins, ["https://hld-gym.vercel.app"])

    def test_env_override_is_comma_separated_and_trims_whitespace(self):
        origins = _allowed_origins(
            {"PLAYGROUND_ALLOWED_ORIGINS": "https://a.example, https://b.example ,,"}
        )
        self.assertEqual(origins, ["https://a.example", "https://b.example"])

    def test_a_bare_wildcard_is_rejected_not_silently_widened(self):
        """"*" degrades the whole guard back to allow-everything -- garbage
        and stray whitespace/commas all fail safe to a smaller list, but this
        one value is the standard "allow everything" convention and the
        first thing anyone reaching for it would type, so it must raise
        rather than pass through to CORSMiddleware verbatim."""
        with self.assertRaises(ValueError):
            _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "*"})

    def test_a_wildcard_mixed_with_real_origins_is_also_rejected(self):
        with self.assertRaises(ValueError):
            _allowed_origins({"PLAYGROUND_ALLOWED_ORIGINS": "http://localhost:3000,*"})


class TestExtractBoardGraph(unittest.TestCase):
    """_extract_board_graph is the module-level pure parser board messages go
    through -- hoisted out specifically so it (and the shape it expects) can
    be pinned down without a live WebRTC connection."""

    def test_extracts_the_graph_from_a_well_formed_board_message(self):
        message = {
            "type": "client-message",
            "data": {"t": "board", "d": {"graph": {"nodes": [], "edges": []}}},
        }
        self.assertEqual(_extract_board_graph(message), {"nodes": [], "edges": []})

    def test_none_for_a_non_client_message(self):
        self.assertIsNone(_extract_board_graph({"type": "something-else"}))

    def test_none_for_a_client_message_of_a_different_type(self):
        message = {"type": "client-message", "data": {"t": "not-board", "d": {}}}
        self.assertIsNone(_extract_board_graph(message))

    def test_none_when_data_is_missing_or_not_a_dict(self):
        self.assertIsNone(_extract_board_graph({"type": "client-message"}))
        self.assertIsNone(_extract_board_graph({"type": "client-message", "data": "nope"}))

    def test_none_when_the_payload_is_missing_or_not_a_dict(self):
        self.assertIsNone(
            _extract_board_graph({"type": "client-message", "data": {"t": "board", "d": "nope"}})
        )
        self.assertIsNone(_extract_board_graph({"type": "client-message", "data": {"t": "board"}}))

    def test_none_when_the_graph_key_is_missing_or_not_a_dict(self):
        """The exact key is "graph", not e.g. "board" -- catches a handler
        that reads the wrong key from an otherwise well-formed envelope."""
        self.assertIsNone(
            _extract_board_graph({"type": "client-message", "data": {"t": "board", "d": {}}})
        )
        self.assertIsNone(
            _extract_board_graph(
                {"type": "client-message", "data": {"t": "board", "d": {"graph": "nope"}}}
            )
        )

    def test_none_for_a_completely_unstructured_message(self):
        self.assertIsNone(_extract_board_graph("not even a dict"))
        self.assertIsNone(_extract_board_graph(None))


class _FakeContext:
    """Stands in for pipecat's LLMContext -- see test_session.py's version,
    duplicated here rather than imported so this test module doesn't reach
    into another test module's internals."""

    def __init__(self):
        self.messages = []
        self.tools = None

    def set_messages(self, messages):
        self.messages = messages

    def transform_messages(self, transform):
        self.set_messages(transform(self.messages))

    def set_tools(self, tools):
        self.tools = tools

    def get_messages(self):
        return self.messages


class TestApplyBoardMessage(unittest.TestCase):
    """_apply_board_message is the second (and last) caller of
    Session.push_context() -- see test_session.py's TestSessionContextBinding
    for the first. Both must be independently provable, since a board update
    that never reaches the model fails silently: the client's UI still shows
    the drawing, only the interviewer stays blind to it."""

    def setUp(self):
        self.session = Session(VoiceConfig())
        self.session.context = _FakeContext()

    def _board_message(self, graph):
        return {"type": "client-message", "data": {"t": "board", "d": {"graph": graph}}}

    def test_a_well_formed_board_message_updates_the_board_and_pushes_context(self):
        graph = {"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0}
        _apply_board_message(self.session, self._board_message(graph))
        text = " ".join(m["content"] for m in self.session.context.messages)
        self.assertIn("Cache", text)

    def test_a_malformed_message_leaves_a_good_board_untouched(self):
        good = self._board_message({"nodes": [{"id": "a", "label": "Cache"}], "edges": [], "unreadable": 0})
        _apply_board_message(self.session, good)
        _apply_board_message(self.session, {"type": "client-message", "data": {"t": "board", "d": {}}})
        text = " ".join(m["content"] for m in self.session.board.messages())
        self.assertIn("Cache", text)

    def test_an_unrelated_message_does_not_touch_the_board_or_the_context(self):
        _apply_board_message(self.session, {"type": "server-message"})
        self.assertEqual(self.session.board.messages(), [])
        self.assertEqual(self.session.context.messages, [])


class _FakeConnection:
    """Stands in for SmallWebRTCConnection -- same house style as
    _FakeContext/_FakeTTS/_FakeConnection in test_pipelines.py. offer()
    constructs SmallWebRTCConnection() by name from its own module
    namespace, so patching playground.server.SmallWebRTCConnection to
    return this is enough to drive the connection-leak guard directly: no
    TestClient, no aiortc, no real SDP handshake."""

    def __init__(self):
        self.disconnect_calls = 0
        self.renegotiate_calls = 0
        # Real SmallWebRTCConnection.pc_id is what get_answer()["pc_id"]
        # echoes back and what _enforce_cap's `connection.pc_id in _sessions`
        # reads -- both need the same value here.
        self.pc_id = "fake-pc-id"
        # _run_diagnostic_end's failure-map delivery -- see TestRunDiagnosticEnd.
        self.app_messages = []

    async def initialize(self, sdp, type):
        pass

    async def disconnect(self):
        self.disconnect_calls += 1

    async def renegotiate(self, sdp, type):
        self.renegotiate_calls += 1

    def send_app_message(self, message):
        self.app_messages.append(message)

    def event_handler(self, name):
        def decorator(fn):
            return fn

        return decorator

    def add_event_handler(self, name, handler):
        pass

    def get_answer(self):
        return {"pc_id": self.pc_id}


class TestConnectionLeakGuard(unittest.TestCase):
    """Both guards in offer() exist to stop a leaked peer connection
    holding an OpenAI audio stream open, which bills per minute. Prove it
    directly rather than trusting the diff -- this build has repeatedly
    shown untested code regresses silently."""

    def setUp(self):
        _fake_openai_key(self)
        self.fake = _FakeConnection()
        self.request = OfferRequest(sdp="x", type="offer")

    def test_a_config_failure_after_initialize_closes_the_connection(self):
        """VoiceConfig.from_env() raises on a malformed PLAYGROUND_* env
        var or the dictation-threshold/distinct-voice invariants -- after
        the connection is already initialize()d. The guard must still tear
        it down."""
        with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
            with patch.object(VoiceConfig, "from_env", side_effect=ValueError("bad env")):
                with self.assertRaises(ValueError):
                    asyncio.run(offer(self.request))
        self.assertEqual(self.fake.disconnect_calls, 1)

    def test_a_cancellation_during_the_worker_build_closes_the_connection_and_propagates(self):
        """asyncio.CancelledError is a BaseException, not an Exception --
        loading SmartTurn plus Silero is exactly the slow window where a
        client giving up mid-request is most likely. The guard must still
        tear the connection down, and must not swallow the cancellation."""
        with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
            with patch(
                "playground.server.build_dictation_worker",
                side_effect=asyncio.CancelledError(),
            ):
                with self.assertRaises(asyncio.CancelledError):
                    asyncio.run(offer(self.request))
        self.assertEqual(self.fake.disconnect_calls, 1)


class _FakeWorkerRunner:
    """Stands in for WorkerRunner -- offer() only ever calls .run(worker) on
    it and passes handle_sigint as a kwarg; neither needs to do anything
    real for a test that only cares about the order _sessions gets written
    in."""

    def __init__(self, *args, **kwargs):
        self.cancel_calls = 0

    async def run(self, worker):
        return

    async def cancel(self, reason=None):
        self.cancel_calls += 1


class TestCapTaskRegistrationOrder(unittest.TestCase):
    """_enforce_cap's own `while connection.pc_id in _sessions` reads
    _sessions on its very first iteration. offer() used to create the cap
    task and *then* write _sessions[pc_id] -- correct only because nothing
    awaited in between the two lines, so the cap task's first step could
    never run before the write landed. An await introduced between them
    later (trivial, and invisible in a diff) would make that condition false
    on entry, and the cap would silently never enforce. offer() now writes
    _sessions[pc_id] first and fills in cap_task with _replace() once it
    exists. Proven here by checking _sessions state from inside the mocked
    _enforce_cap's own call, not by timing -- timing is exactly what let the
    old order look correct."""

    def setUp(self):
        _fake_openai_key(self)
        self.fake = _FakeConnection()
        self.request = OfferRequest(sdp="x", type="offer")
        from playground.auth import sign_token
        from playground.server import _TOKEN_SECRET

        # mode=playground is gated on our own session token now -- see
        # TestPlaygroundAuthGate for the gate itself. This test is about the
        # registration-order bug, so it needs to get past the gate with a
        # valid token, not exercise it.
        self.auth = f"Bearer {sign_token('learner@example.com', _TOKEN_SECRET, now=time.time(), ttl_secs=3600)}"

    def test_the_session_is_registered_before_the_cap_task_runs(self):
        seen: dict[str, bool] = {}

        async def fake_enforce_cap(connection, worker, pg_session):
            seen["registered"] = connection.pc_id in _sessions

        fake_session = Session(VoiceConfig())

        async def scenario():
            answer = await offer(self.request, mode="playground", authorization=self.auth)
            # asyncio.create_task only schedules _enforce_cap's coroutine;
            # it needs one trip round the loop to actually take its first
            # step. Do that here, inside the same running loop, rather than
            # relying on asyncio.run()'s own shutdown-time task cancellation
            # (which can cancel a not-yet-started task before it ever runs a
            # single line, and would make this test pass for the wrong
            # reason -- an empty `seen`, not a proven ordering).
            await asyncio.sleep(0)
            return answer

        answer = None
        try:
            with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
                with patch(
                    "playground.server.build_playground_worker",
                    return_value=(object(), fake_session),
                ):
                    with patch("playground.server.WorkerRunner", _FakeWorkerRunner):
                        with patch(
                            "playground.server._enforce_cap", side_effect=fake_enforce_cap
                        ):
                            answer = asyncio.run(scenario())
            self.assertTrue(
                seen.get("registered"),
                "the cap task ran before the session was registered in _sessions",
            )
        finally:
            if answer is not None:
                _sessions.pop(answer["pc_id"], None)


class _FakeCapRunner:
    def __init__(self):
        self.cancel_calls = []
        self.cancelled_at = None

    async def cancel(self, reason=None):
        self.cancel_calls.append(reason)
        self.cancelled_at = time.monotonic()


class _FakeCapWorker:
    def __init__(self):
        self.queued = []
        self.queued_at = None

    async def queue_frames(self, frames):
        self.queued.append(list(frames))
        if self.queued_at is None:
            self.queued_at = time.monotonic()


class _FakeCapConnection:
    def __init__(self, pc_id):
        self.pc_id = pc_id
        # _enforce_diagnostic_cap's fallback end path (_run_diagnostic_end)
        # delivers the failure map through this -- see TestEnforceDiagnosticCap.
        self.app_messages = []

    def send_app_message(self, message):
        self.app_messages.append(message)


class _FakeTTS:
    """Same double as test_pipelines.py's -- duplicated rather than
    imported so this test module doesn't reach into another one's
    internals."""

    def __init__(self):
        self.voice = None

    async def set_voice(self, voice):
        self.voice = voice


class TestEnforceCap(unittest.TestCase):
    """_enforce_cap is the scheduling half of the session cap -- Session's
    own start/remaining_secs/expired are pure and covered by test_cap.py,
    but the polling loop that calls them is where the real bug in this
    build lived (a flat sleep interval that could step clean over a short
    handover window). Session's clock is real time.monotonic() here, not a
    fake -- that bug is exactly the kind of scheduling defect a mocked clock
    would never exercise -- so these run for real, for about a second each,
    against a real short cap rather than the 12-minute default."""

    def _run(self, session):
        session.tts = _FakeTTS()
        session.start(now=time.monotonic())
        connection = _FakeCapConnection(f"pc-{id(session)}")
        runner = _FakeCapRunner()
        worker = _FakeCapWorker()
        _sessions[connection.pc_id] = _Session(
            connection=connection, runner=runner, task=None, mode="playground"
        )
        asyncio.run(_enforce_cap(connection, worker, session))
        return worker, runner

    def test_the_handover_happens_before_the_cut(self):
        session = Session(VoiceConfig(session_cap_secs=1.0))
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(len(worker.queued), 1)
        self.assertEqual(runner.cancel_calls, ["connection ended"])
        self.assertLess(worker.queued_at, runner.cancelled_at)

    def test_a_very_short_cap_still_gets_a_handover_not_a_bare_cut(self):
        """The regression test for the bug this task found: a flat 1s poll
        ceiling could step clean over a handover window narrower than a
        second and reach expiry having never handed over at all."""
        session = Session(VoiceConfig(session_cap_secs=0.5))
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(len(worker.queued), 1)

    def test_the_handover_narrows_a_bound_context_to_draw_diagram(self):
        """The cap's handover branch calls switch_to_coach() then
        push_context(), the exact same pair end_round's handler calls (see
        test_pipelines.py's TestEndRound) -- proof the tool narrowing is a
        property of Session, not something each caller has to remember to
        do. An interviewer that can draw can show the candidate the
        structure the round exists to measure."""
        session = Session(VoiceConfig(session_cap_secs=1.0))
        session.context = _FakeContext()
        self._run(session)
        names = {t.name for t in session.context.tools.standard_tools}
        self.assertEqual(names, {"draw_diagram"})

    def test_a_session_already_in_coach_mode_gets_no_second_run_frame(self):
        """end_round switches a session to coach independently of the cap,
        and nothing ends the connection when it does -- reaching the
        handover mark already in coach mode is routine, not exotic. The cap
        must not force a second, unprompted completion with no user turn
        behind it: the coach interjecting out of nowhere mid-conversation."""
        session = Session(VoiceConfig(session_cap_secs=1.0))
        session.switch_to_coach()  # end_round already ran, before the cap fired
        worker, runner = self._run(session)
        self.assertEqual(session.mode, "coach")
        self.assertEqual(worker.queued, [])
        self.assertEqual(runner.cancel_calls, ["connection ended"])


class TestPlaygroundAuthGate(unittest.TestCase):
    """mode=playground is gated on our own session token, checked before any
    connection or session exists -- a rejected request must create nothing
    and bill nothing (voice bills by the minute). mode=dictation is
    deliberately untouched by any of this; see the design's "stays
    completely open". offer() is called directly here, the same way
    TestConnectionLeakGuard and TestCapTaskRegistrationOrder do, rather than
    through TestClient -- it gives the same fine control over the event loop
    without a real WebRTC handshake."""

    def setUp(self):
        _fake_openai_key(self)
        from playground.server import _TOKEN_SECRET

        self.secret = _TOKEN_SECRET
        self.request = OfferRequest(sdp="x", type="offer")

    def _token(self, email="learner@example.com", now=None, ttl_secs=3600):
        return sign_token(email, self.secret, now=now if now is not None else time.time(), ttl_secs=ttl_secs)

    def test_no_authorization_header_is_a_401_and_creates_no_connection(self):
        with patch("playground.server.SmallWebRTCConnection") as mock_conn:
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(offer(self.request, mode="playground", authorization=None))
        self.assertEqual(ctx.exception.status_code, 401)
        mock_conn.assert_not_called()

    def test_a_non_bearer_scheme_is_a_401(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                offer(self.request, mode="playground", authorization=f"Basic {self._token()}")
            )
        self.assertEqual(ctx.exception.status_code, 401)

    def test_an_expired_token_is_a_401(self):
        token = self._token(now=time.time() - 10_000, ttl_secs=1)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(offer(self.request, mode="playground", authorization=f"Bearer {token}"))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_a_tampered_token_is_a_401(self):
        """Tampers the *first* character of the signature, not the last --
        found flaky during a security-review re-run: a base64url-encoded
        32-byte HMAC digest has 2 unused padding bits in its final
        character, so flipping the last character sometimes decodes to the
        exact same bytes (measured: ~5.75% of the time), and the "tampered"
        token verifies fine. The first character has no such don't-care
        bits -- confirmed deterministic across 2000 trials, 0 misses."""
        token = self._token()
        payload_part, sig_part = token.split(".")
        tampered_sig = ("A" if sig_part[0] != "A" else "B") + sig_part[1:]
        tampered = f"{payload_part}.{tampered_sig}"
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                offer(self.request, mode="playground", authorization=f"Bearer {tampered}")
            )
        self.assertEqual(ctx.exception.status_code, 401)

    def test_a_malformed_token_is_a_401(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                offer(self.request, mode="playground", authorization="Bearer not-a-real-token")
            )
        self.assertEqual(ctx.exception.status_code, 401)

    def test_a_valid_token_passes_the_gate_and_reaches_the_pipeline_build(self):
        """Past the gate, offer() goes on to build the real playground
        worker -- mocked here the same way TestCapTaskRegistrationOrder
        mocks it (including _enforce_cap itself, so no real polling task is
        left running past this test). This proves the gate lets a valid
        token through; it does not re-test the pipeline build."""
        fake = _FakeConnection()
        fake_session = Session(VoiceConfig())

        async def fake_enforce_cap(connection, worker, pg_session):
            return

        try:
            with patch("playground.server.SmallWebRTCConnection", return_value=fake):
                with patch(
                    "playground.server.build_playground_worker",
                    return_value=(object(), fake_session),
                ):
                    with patch("playground.server.WorkerRunner", _FakeWorkerRunner):
                        with patch(
                            "playground.server._enforce_cap", side_effect=fake_enforce_cap
                        ):
                            answer = asyncio.run(
                                offer(
                                    self.request,
                                    mode="playground",
                                    authorization=f"Bearer {self._token()}",
                                )
                            )
            self.assertEqual(answer["pc_id"], fake.pc_id)
            # The load-bearing assertion for the renegotiate-bypass fix: the
            # session offer() actually *creates* must be recorded as
            # mode="playground", not just whatever the request happened to
            # claim -- a security review mutated the construction site's
            # `mode=mode` to a hardcoded `mode="dictation"` and every other
            # test in this suite still passed, because none of them checked
            # what got written into _sessions. This one does.
            self.assertEqual(_sessions[fake.pc_id].mode, "playground")
            self.assertEqual(_sessions[fake.pc_id].email, "learner@example.com")
        finally:
            _sessions.pop(fake.pc_id, None)

    def test_dictation_needs_no_token_at_all(self):
        fake = _FakeConnection()
        try:
            with patch("playground.server.SmallWebRTCConnection", return_value=fake):
                with patch("playground.server.build_dictation_worker", return_value=object()):
                    with patch("playground.server.WorkerRunner", _FakeWorkerRunner):
                        answer = asyncio.run(
                            offer(self.request, mode="dictation", authorization=None)
                        )
            self.assertEqual(answer["pc_id"], fake.pc_id)
            self.assertEqual(_sessions[fake.pc_id].mode, "dictation")
            self.assertIsNone(_sessions[fake.pc_id].email)
        finally:
            _sessions.pop(fake.pc_id, None)

    def test_dictation_ignores_even_a_garbage_authorization_header(self):
        """Proof, not just absence of a check: dictation must still work
        when the header is present but worthless, not merely when it's
        missing."""
        fake = _FakeConnection()
        try:
            with patch("playground.server.SmallWebRTCConnection", return_value=fake):
                with patch("playground.server.build_dictation_worker", return_value=object()):
                    with patch("playground.server.WorkerRunner", _FakeWorkerRunner):
                        answer = asyncio.run(
                            offer(self.request, mode="dictation", authorization="Bearer garbage")
                        )
            self.assertEqual(answer["pc_id"], fake.pc_id)
        finally:
            _sessions.pop(fake.pc_id, None)


class TestLogin(unittest.TestCase):
    """/api/login exchanges a verified Google ID token for our own session
    token -- see playground/auth.py. The Google verification call itself is
    IO (it fetches Google's public keys); stubbed here via a patched
    verify_google_id_token, never a real network call."""

    def setUp(self):
        _fake_openai_key(self)

    def test_a_verified_google_token_returns_our_own_session_token(self):
        with patch(
            "playground.server.verify_google_id_token", return_value="learner@example.com"
        ):
            result = asyncio.run(login(LoginRequest(id_token="google-id-token")))
        self.assertEqual(result.email, "learner@example.com")
        from playground.auth import verify_token
        from playground.server import _TOKEN_SECRET

        self.assertEqual(
            verify_token(result.token, _TOKEN_SECRET, now=time.time()), "learner@example.com"
        )

    def test_a_failed_google_verification_is_a_401_not_a_500(self):
        with patch(
            "playground.server.verify_google_id_token",
            side_effect=AuthError("Google sign-in verification failed: bad token"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(login(LoginRequest(id_token="bad-token")))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_the_401_body_does_not_echo_the_caller_supplied_credential(self):
        """A security-review finding: google-auth's own exception text can
        embed the caller's raw submitted token (confirmed live -- a
        malformed token's message was literally "Wrong number of segments
        in token: b'...'" with the token inline). Nothing secret leaks --
        it's the caller's own input -- but reflecting a credential into
        devtools, proxy logs and error trackers is a habit not to form. The
        response body must carry a fixed message, never str(AuthError)."""
        submitted = "attacker-controlled-value-should-never-appear-in-the-response"
        with patch(
            "playground.server.verify_google_id_token",
            side_effect=AuthError(f"Google sign-in verification failed: {submitted}"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(login(LoginRequest(id_token="bad-token")))
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertNotIn(submitted, str(ctx.exception.detail))

    def test_google_being_unreachable_is_a_503_not_a_401(self):
        """GoogleUnavailableError (a TransportError fetching Google's own
        certs) means Google couldn't be asked, not that the credential was
        rejected -- reporting it as a 401 would tell a learner their
        sign-in was wrong when the real problem is on Google's side."""
        with patch(
            "playground.server.verify_google_id_token",
            side_effect=GoogleUnavailableError("could not fetch certs"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(login(LoginRequest(id_token="some-token")))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_a_missing_id_token_is_a_4xx_at_the_http_boundary_not_a_500(self):
        from playground.server import app

        client = TestClient(app)
        r = client.post("/api/login", json={})
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)


class TestRenegotiateAuthGateBypass(unittest.TestCase):
    """The security-review-caught bug: offer()'s renegotiate branch (a
    repeat POST carrying an existing pc_id) used to gate only on *this
    request's own claimed* mode param, not on what the existing session
    actually is. That let an unauthenticated `?mode=dictation` renegotiate
    onto a live *playground* session's pc_id and take over its connection --
    the attacker's SDP becomes the remote description of a session someone
    else is paying OpenAI credit for. Driven directly against a session
    registered in _sessions, not through the full offer()-builds-a-worker
    path -- this is about the gate, not the pipeline."""

    def setUp(self):
        _fake_openai_key(self)
        from playground.server import _TOKEN_SECRET

        self.secret = _TOKEN_SECRET
        self.fake = _FakeConnection()
        self.fake.pc_id = "victim-playground-pc-id"
        # email matches the token test_a_valid_token_still_renegotiates_it_normally
        # signs below -- that test is about the mode gate, not ownership;
        # see TestRenegotiateOwnership for the different-user 403 case.
        _sessions[self.fake.pc_id] = _Session(
            connection=self.fake,
            runner=None,
            task=None,
            mode="playground",
            email="learner@example.com",
        )

    def tearDown(self):
        _sessions.pop(self.fake.pc_id, None)

    def test_mode_dictation_cannot_renegotiate_a_playground_session_without_a_token(self):
        """The exploit as the review demonstrated it: no Authorization
        header, mode=dictation, the victim's pc_id. Must 401, and the
        attacker's SDP must never reach renegotiate()."""
        request = OfferRequest(sdp="attacker-sdp", type="offer", pc_id=self.fake.pc_id)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(offer(request, mode="dictation", authorization=None))
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(self.fake.renegotiate_calls, 0)

    def test_mode_playground_also_cannot_renegotiate_it_without_a_token(self):
        """The half of this that already worked before the fix -- kept
        alongside the dictation case so both routes to the same session are
        visible in one place."""
        request = OfferRequest(sdp="attacker-sdp", type="offer", pc_id=self.fake.pc_id)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(offer(request, mode="playground", authorization=None))
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(self.fake.renegotiate_calls, 0)

    def test_a_valid_token_still_renegotiates_it_normally(self):
        """The fix must not turn into a second bug: the legitimate owner of
        the session, using the same mode as its own client always would,
        must still get through."""
        token = sign_token("learner@example.com", self.secret, now=time.time(), ttl_secs=3600)
        request = OfferRequest(sdp="real-sdp", type="offer", pc_id=self.fake.pc_id)
        answer = asyncio.run(offer(request, mode="playground", authorization=f"Bearer {token}"))
        self.assertEqual(self.fake.renegotiate_calls, 1)
        self.assertEqual(answer["pc_id"], self.fake.pc_id)


class TestRenegotiateOwnership(unittest.TestCase):
    """Authenticated is not the same as authorized: a valid token proves
    *a* Google account signed in, not that it is *this session's* account
    -- and with no allowlist, any Google account is the entire set a token
    can come from. _authenticate_playground_request used to return the
    verified email only for offer() to throw it away, so a second learner's
    own perfectly valid token could renegotiate someone *else's* live
    playground session. A security review demonstrated this live before it
    shipped. _Session.email pins the owner at creation; the renegotiate
    branch now requires a match."""

    def setUp(self):
        _fake_openai_key(self)
        from playground.server import _TOKEN_SECRET

        self.secret = _TOKEN_SECRET
        self.fake = _FakeConnection()
        self.fake.pc_id = "victim-playground-pc-id"
        _sessions[self.fake.pc_id] = _Session(
            connection=self.fake,
            runner=None,
            task=None,
            mode="playground",
            email="victim@example.com",
        )

    def tearDown(self):
        _sessions.pop(self.fake.pc_id, None)

    def _token_for(self, email):
        return sign_token(email, self.secret, now=time.time(), ttl_secs=3600)

    def test_the_owning_user_can_renegotiate_their_own_session(self):
        request = OfferRequest(sdp="real-sdp", type="offer", pc_id=self.fake.pc_id)
        answer = asyncio.run(
            offer(request, mode="playground", authorization=f"Bearer {self._token_for('victim@example.com')}")
        )
        self.assertEqual(self.fake.renegotiate_calls, 1)
        self.assertEqual(answer["pc_id"], self.fake.pc_id)

    def test_a_different_authenticated_user_gets_403_not_200(self):
        """The exploit as demonstrated: a token minted for a *different*,
        entirely valid Google account. Must be rejected as a permissions
        problem (403), distinct from not being authenticated at all (401)
        -- and the attacker's SDP must never reach renegotiate()."""
        request = OfferRequest(sdp="attacker-sdp", type="offer", pc_id=self.fake.pc_id)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                offer(
                    request,
                    mode="playground",
                    authorization=f"Bearer {self._token_for('attacker@example.com')}",
                )
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(self.fake.renegotiate_calls, 0)



class _NoAnswerConnection(_FakeConnection):
    """A connection whose get_answer() returns None -- what the real
    SmallWebRTCConnection returns whenever its `_answer` is unset (see the
    installed pipecat connection.py). Both of offer()'s call sites used to
    take that unchecked."""

    def get_answer(self):
        return None


class TestOfferAnswerMissing(unittest.TestCase):
    """get_answer() returning None used to fail two different ways, both
    wrong: TypeError on answer["pc_id"] for a new session (a 500, with a
    full STT+LLM+TTS worker already running and nothing left to cancel it),
    and HTTP 200 with a body of literally `null` on a renegotiate, which the
    browser turns into setRemoteDescription(null) inside its own retry loop.
    Voice bills by the minute, so an orphaned worker is a money leak, not
    just an untidy one."""

    def setUp(self):
        _fake_openai_key(self)
        self.fake = _NoAnswerConnection()
        self.request = OfferRequest(sdp="x", type="offer")
        self.auth = f"Bearer {sign_token('learner@example.com', _TOKEN_SECRET, now=time.time(), ttl_secs=3600)}"

    def test_a_missing_answer_cancels_the_worker_instead_of_orphaning_it(self):
        runners = []

        def make_runner(*args, **kwargs):
            runners.append(_FakeWorkerRunner())
            return runners[-1]

        with patch("playground.server.SmallWebRTCConnection", return_value=self.fake):
            with patch(
                "playground.server.build_playground_worker",
                return_value=(object(), Session(VoiceConfig())),
            ):
                with patch("playground.server.WorkerRunner", make_runner):
                    with self.assertRaises(HTTPException) as ctx:
                        asyncio.run(offer(self.request, mode="playground", authorization=self.auth))
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(self.fake.disconnect_calls, 1)
        self.assertEqual(
            [r.cancel_calls for r in runners],
            [1],
            "the worker task was left running after the offer failed",
        )
        self.assertNotIn(self.fake.pc_id, _sessions)

    def test_a_renegotiate_with_no_answer_is_a_503_not_a_null_body(self):
        session = _Session(
            connection=self.fake,
            runner=_FakeWorkerRunner(),
            task=None,
            mode="playground",
            email="learner@example.com",
        )
        _sessions[self.fake.pc_id] = session
        try:
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(
                    offer(
                        OfferRequest(sdp="x", type="offer", pc_id=self.fake.pc_id),
                        mode="playground",
                        authorization=self.auth,
                    )
                )
            self.assertEqual(ctx.exception.status_code, 503)
        finally:
            _sessions.pop(self.fake.pc_id, None)


class TestSessionTokenRejectionIsOpaque(unittest.TestCase):
    """login() already refuses to reflect an AuthError's own text; this path
    did the same thing 40 lines later with detail=str(e). Nothing leaks
    today (verify_token only raises fixed strings) -- what it handed a
    caller was an oracle separating a forged signature from an expired one
    from a malformed one, and a licence for the next AuthError raised with
    dynamic text to become a real reflection bug."""

    def _reject(self, header):
        from playground.server import _authenticate_playground_request

        with self.assertRaises(HTTPException) as ctx:
            _authenticate_playground_request(header)
        return ctx.exception

    def test_every_rejection_reason_gives_the_same_401_body(self):
        expired = sign_token("a@b.c", _TOKEN_SECRET, now=time.time() - 7200, ttl_secs=3600)
        forged = sign_token("a@b.c", "a-different-secret", now=time.time(), ttl_secs=3600)
        bodies = {
            self._reject(f"Bearer {expired}").detail,
            self._reject(f"Bearer {forged}").detail,
            self._reject("Bearer not-a-token-at-all").detail,
            self._reject(None).detail,
        }
        self.assertEqual(bodies, {"sign in required"})

    def test_the_body_never_carries_the_submitted_token(self):
        forged = sign_token("a@b.c", "a-different-secret", now=time.time(), ttl_secs=3600)
        self.assertNotIn(forged, self._reject(f"Bearer {forged}").detail)


class TestLoginWithoutAClientId(unittest.TestCase):
    """An unset PLAYGROUND_GOOGLE_CLIENT_ID made google-auth compare every
    token's `aud` against [""], so every learner was told their own Google
    account had been rejected -- for an env var the operator never set. The
    signing secret refuses to boot on the same class of mistake; this one
    cannot (mode=dictation needs no sign-in, so a dictation-only deploy is
    legitimate), so it has to fail honestly on the one endpoint that needs
    it."""

    def test_an_unconfigured_client_id_is_a_503_not_a_401(self):
        with patch.dict(os.environ, {"PLAYGROUND_GOOGLE_CLIENT_ID": ""}):
            with patch("playground.server.verify_google_id_token") as verify:
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(login(LoginRequest(id_token="anything")))
        self.assertEqual(ctx.exception.status_code, 503)
        verify.assert_not_called()


class TestEndSessionCancelsTheCapTask(unittest.TestCase):
    """The cap task used to be left to notice its own session was gone on
    its next poll. Bounded at a second, so never a crash -- but _Session's
    comment claimed teardown paths already cancelled it, and nothing did."""

    def test_a_hangup_cancels_the_cap_task(self):
        from playground.server import _end_session

        conn = _FakeConnection()
        runner = _FakeWorkerRunner()

        async def scenario():
            cap = asyncio.create_task(asyncio.sleep(3600))
            _sessions[conn.pc_id] = _Session(
                connection=conn, runner=runner, task=None, mode="playground",
                email="a@b.c", cap_task=cap,
            )
            await _end_session(conn)
            await asyncio.sleep(0)
            return cap

        cap = asyncio.run(scenario())
        self.assertTrue(cap.cancelled() or cap.cancelling())
        self.assertEqual(runner.cancel_calls, 1)
        self.assertNotIn(conn.pc_id, _sessions)


class TestExtractFinish(unittest.TestCase):
    """_extract_finish is _extract_board_graph's sibling parser -- the
    client's finish control instead of a board update. Module-level and
    pure for the same reason."""

    def test_true_for_a_finish_client_message(self):
        msg = {"type": "client-message", "data": {"t": "finish", "d": {}}}
        self.assertTrue(server._extract_finish(msg))

    def test_false_for_board_messages_and_junk(self):
        self.assertFalse(server._extract_finish({"type": "client-message", "data": {"t": "board", "d": {}}}))
        self.assertFalse(server._extract_finish({"type": "other"}))
        self.assertFalse(server._extract_finish("finish"))
        self.assertFalse(server._extract_finish({"type": "client-message", "data": "finish"}))


class TestDiagnosticAuthGate(unittest.TestCase):
    """A diagnostic session spends real OpenAI credit per minute exactly
    like a playground one, so it gets the same token check -- see
    TestPlaygroundAuthGate for the gate's full coverage; this just proves
    mode=diagnostic actually routes through it. Same TestClient setup as
    TestOffer/TestHealth above."""

    def setUp(self):
        _fake_openai_key(self)
        from playground.server import app

        self.client = TestClient(app)

    def test_mode_diagnostic_without_a_token_is_401(self):
        response = self.client.post(
            "/api/offer?mode=diagnostic", json={"sdp": "x", "type": "offer"}
        )
        self.assertEqual(response.status_code, 401)


def _make_fake_session_entry(connection, mode="diagnostic"):
    """The same _Session-with-a-fake-runner shape TestEndSessionCancelsTheCapTask
    and friends build inline -- pulled into one helper here since three new
    test classes below all need it for a diagnostic session registered in
    _sessions."""
    return _Session(
        connection=connection,
        runner=_FakeWorkerRunner(),
        task=None,
        mode=mode,
        email="e@x",
        cap_task=None,
    )


class TestRunDiagnosticEnd(unittest.IsolatedAsyncioTestCase):
    """_run_diagnostic_end is the one end path all three diagnostic triggers
    (end_round, the client's finish control, the cap) share -- grades,
    delivers the failure map, tears down. Proven directly here rather than
    only through offer()'s wiring."""

    def _session(self):
        s = Session(VoiceConfig(), kind="diagnostic")
        s.context = _FakeContext()
        return s

    async def test_it_grades_sends_the_map_and_tears_down(self):
        session = self._session()
        connection = _FakeConnection()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)

        async def grade_fn(turns, board_text, model, client=None):
            return [{"quote": "q", "probe": "p", "gap": "g", "chapter": "/book/#ch/p1c06"}]

        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        [sent] = connection.app_messages
        self.assertEqual(sent["label"], "rtvi-ai")
        self.assertEqual(sent["data"]["type"], "failure_map")
        self.assertEqual(len(sent["data"]["moments"]), 1)
        self.assertNotIn(connection.pc_id, server._sessions)  # torn down
        self.assertTrue(session.round_over)

    async def test_a_failed_grader_sends_null_moments_not_nothing(self):
        session = self._session()
        connection = _FakeConnection()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)

        async def grade_fn(turns, board_text, model, client=None):
            return None

        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        [sent] = connection.app_messages
        self.assertIsNone(sent["data"]["moments"])

    async def test_the_three_end_triggers_cannot_grade_twice(self):
        session = self._session()
        connection = _FakeConnection()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)
        calls = []

        async def grade_fn(turns, board_text, model, client=None):
            calls.append(1)
            return []

        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        self.assertEqual(len(calls), 1)


class TestEnforceDiagnosticCap(unittest.IsolatedAsyncioTestCase):
    """The diagnostic sibling of TestEnforceCap: no coach handover, ever --
    switch_to_coach() raises for a diagnostic session (see test_session.py),
    so _enforce_diagnostic_cap must never reach it. The two assertions that
    matter: the closing turn is requested (announced, never a silent cut),
    and the end path runs -- the coach handover never does."""

    async def test_closing_turn_then_end_path_never_a_handover(self):
        config = VoiceConfig(diagnostic_cap_secs=0.3)
        session = Session(config, kind="diagnostic")
        session.context = _FakeContext()
        session.start(now=time.monotonic())
        connection = _FakeCapConnection(f"pc-{id(session)}")
        worker = _FakeCapWorker()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)
        ended = []

        async def grade_fn(turns, board_text, model, client=None):
            ended.append(1)
            return []

        with patch.object(server.grading, "grade", grade_fn):
            await server._enforce_diagnostic_cap(
                connection, worker, session, config, closing_secs=0.1
            )
        self.assertTrue(session.closing)          # the announced closing turn
        self.assertTrue(worker.queued)             # LLMRunFrame was queued
        self.assertEqual(session.mode, "interview")  # never a coach
        self.assertEqual(ended, [1])                # the end path ran


if __name__ == "__main__":
    unittest.main()
