"""Playground's own session tokens, and the Google sign-in that mints them.

Dictation needs none of this -- see server.py's mode=="playground" gate.
Anyone with a Google account is let in; there is no allowlist, a decision
made knowingly (see sell/PROGRESS.md).

The token is deliberately not a JWT: base64url(payload_json) + "." +
base64url(hmac_sha256(secret, payload_json)). A JWT carries an `alg` field
the verifier has to trust and dispatch on -- that field is exactly what
algorithm-confusion attacks (e.g. RS256 -> HS256, verifying an RSA-signed
token against its own public key reinterpreted as an HMAC secret) exploit.
This format has no `alg` to parse: verification is always HMAC-SHA256,
always compared with hmac.compare_digest, full stop.
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
from typing import Callable, Mapping

from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


class AuthError(Exception):
    """Any rejection on the auth path -- expired, tampered, malformed, no
    signature, a rejected Google credential, a verified token with no email.
    One type so server.py has exactly one except clause to turn into a 401.
    Never lets a raw exception (a KeyError, a binascii.Error, ValueError
    from json.loads) escape as an unhandled 500 -- every failure here is an
    expected rejection, not a bug.

    Its message can carry google-auth's own exception text, which may embed
    the caller's own submitted credential (confirmed live: a malformed
    token produces "Wrong number of segments in token: b'...'" with the
    token inline). Fine to log; server.py deliberately does not put
    str(AuthError) in an HTTP response body -- see login()."""


class GoogleUnavailableError(Exception):
    """Google itself couldn't be reached to verify the token -- a
    google.auth.exceptions.TransportError fetching its public certs, not a
    rejected credential. Kept distinct from AuthError so server.py can
    report this as a 503 (try again shortly) rather than a 401 (sign in
    again) -- collapsing the two would tell a learner their own sign-in was
    wrong when the real problem is Google being briefly unreachable."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def sign_token(email: str, secret: str, now: float, ttl_secs: int) -> str:
    """Issues one of our own session tokens. `now` and `ttl_secs` are
    parameters, not read from the clock/env internally, so this is pure and
    testable without freezing time."""
    payload = json.dumps(
        {"email": email, "exp": now + ttl_secs}, separators=(",", ":"), sort_keys=True
    )
    payload_bytes = payload.encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(sig)}"


def verify_token(token: str | None, secret: str, now: float) -> str:
    """Returns the verified email, or raises AuthError. Every rejection path
    -- missing, malformed, unparseable base64, a bad signature, a tampered
    or non-dict payload, a wrong-typed exp/email, expiry -- raises AuthError
    rather than letting a KeyError/TypeError/binascii.Error/json error
    escape, so the caller can turn *any* failure into a clean 401.

    The signature is checked (with hmac.compare_digest, never `==`) before
    the payload is ever json.loads()'d or its fields trusted -- a payload
    that didn't come from someone holding `secret` gets no further than
    that comparison."""
    if not token or "." not in token:
        raise AuthError("malformed token")
    payload_part, _, sig_part = token.partition(".")
    try:
        payload_bytes = _b64url_decode(payload_part)
        sig = _b64url_decode(sig_part)
    except (binascii.Error, ValueError) as e:
        raise AuthError("malformed token") from e

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected_sig):
        raise AuthError("bad signature")

    try:
        payload = json.loads(payload_bytes)
    except ValueError as e:
        raise AuthError("malformed payload") from e

    if not isinstance(payload, dict):
        raise AuthError("malformed payload")
    email, exp = payload.get("email"), payload.get("exp")
    if not isinstance(email, str) or not isinstance(exp, (int, float)):
        raise AuthError("malformed payload")
    if now >= exp:
        raise AuthError("expired")
    return email


def token_secret_from_env(env: Mapping[str, str] | None = None) -> str:
    """PLAYGROUND_TOKEN_SECRET, required, with no default -- unlike every
    other PLAYGROUND_* knob. server.py calls this once, at import time, the
    same way _allowed_origins() refuses a "*" wildcard: raising here means
    the service refuses to start rather than either 500ing on every
    playground request or silently signing sessions with a guessable
    secret, which would let anyone forge one."""
    src = os.environ if env is None else env
    secret = src.get("PLAYGROUND_TOKEN_SECRET")
    if not secret:
        raise ValueError(
            "PLAYGROUND_TOKEN_SECRET is required and has no default: without it "
            "the service would either crash on every playground request or fall "
            "back to a guessable secret, and a default signing secret means "
            "anyone can forge a session. Set it in playground/.env."
        )
    return secret


def verify_google_id_token(
    id_token: str,
    client_id: str,
    verifier: Callable[[str, str], dict] | None = None,
) -> str:
    """Verifies a Google ID token -- signature, issuer, audience against our
    client ID, expiry -- and returns the verified email.

    The real Google call (google.oauth2.id_token.verify_oauth2_token) does
    IO: it fetches (and caches) Google's public keys over HTTPS. `verifier`
    is injectable so tests never touch the network; it defaults to the real
    call. google-auth raises ValueError for every failure mode (bad
    signature, wrong issuer, wrong audience, expired) -- wrapped here as
    AuthError so server.py has one exception type to turn into a 401."""
    if verifier is None:

        def verifier(idt: str, aud: str) -> dict:
            return google_id_token.verify_oauth2_token(idt, google_requests.Request(), aud)

    try:
        claims = verifier(id_token, client_id)
    except google_auth_exceptions.TransportError as e:
        # A network/DNS/HTTP failure fetching Google's own public certs --
        # Google being briefly unreachable, not a bad credential. Caught
        # ahead of the blanket `except Exception` below so it isn't
        # misreported as one.
        raise GoogleUnavailableError(str(e)) from e
    except Exception as e:
        raise AuthError(f"Google sign-in verification failed: {e}") from e
    email = claims.get("email") if isinstance(claims, dict) else None
    if not email:
        raise AuthError("Google token has no email claim")
    return email
