import unittest

from playground.auth import (
    AuthError,
    sign_token,
    token_secret_from_env,
    verify_google_id_token,
    verify_token,
)


class TestSignAndVerifyToken(unittest.TestCase):
    """Our own session token -- not a JWT. base64url(payload_json) + "." +
    base64url(hmac_sha256(secret, payload_json)). No `alg` field means
    algorithm-confusion has nothing to parse. See playground/auth.py."""

    def test_a_freshly_signed_token_verifies_and_returns_the_email(self):
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        self.assertEqual(verify_token(token, "secret", now=1000.0), "a@example.com")

    def test_a_token_still_verifies_a_moment_before_it_expires(self):
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        self.assertEqual(verify_token(token, "secret", now=4599.9), "a@example.com")

    def test_an_expired_token_is_rejected(self):
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        with self.assertRaises(AuthError):
            verify_token(token, "secret", now=4600.0)

    def test_a_token_signed_with_a_different_secret_is_rejected(self):
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        with self.assertRaises(AuthError):
            verify_token(token, "a-different-secret", now=1000.0)

    def test_a_tampered_payload_is_rejected(self):
        """Flip the email in the payload without re-signing -- the classic
        tamper: the signature no longer matches the (attacker-controlled)
        payload it's supposed to cover."""
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        payload_part, sig_part = token.split(".")
        import base64

        payload = base64.urlsafe_b64decode(payload_part + "==").decode()
        tampered_payload = payload.replace("a@example.com", "attacker@evil.com")
        tampered_part = base64.urlsafe_b64encode(tampered_payload.encode()).rstrip(b"=").decode()
        tampered_token = f"{tampered_part}.{sig_part}"
        with self.assertRaises(AuthError):
            verify_token(tampered_token, "secret", now=1000.0)

    def test_a_tampered_signature_is_rejected(self):
        token = sign_token("a@example.com", "secret", now=1000.0, ttl_secs=3600)
        payload_part, sig_part = token.split(".")
        tampered_sig = ("A" if sig_part[0] != "A" else "B") + sig_part[1:]
        with self.assertRaises(AuthError):
            verify_token(f"{payload_part}.{tampered_sig}", "secret", now=1000.0)

    def test_a_token_with_no_dot_separator_is_rejected(self):
        with self.assertRaises(AuthError):
            verify_token("not-a-real-token", "secret", now=1000.0)

    def test_an_empty_token_is_rejected(self):
        with self.assertRaises(AuthError):
            verify_token("", "secret", now=1000.0)

    def test_a_token_with_junk_base64_is_rejected(self):
        with self.assertRaises(AuthError):
            verify_token("not!base64!!.also!not!base64", "secret", now=1000.0)

    def test_a_token_whose_payload_is_not_json_is_rejected(self):
        import base64

        garbage_payload = base64.urlsafe_b64encode(b"not json at all").rstrip(b"=").decode()
        # Sign the *real* garbage bytes with the real secret, so this
        # specifically exercises "valid signature, undecodeable payload"
        # rather than being caught earlier by the signature check.
        import hashlib
        import hmac

        sig = hmac.new(b"secret", b"not json at all", hashlib.sha256).digest()
        sig_part = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
        with self.assertRaises(AuthError):
            verify_token(f"{garbage_payload}.{sig_part}", "secret", now=1000.0)

    def test_none_is_rejected_without_crashing(self):
        with self.assertRaises(AuthError):
            verify_token(None, "secret", now=1000.0)


class TestTokenSecretFromEnv(unittest.TestCase):
    """The service refuses to start without PLAYGROUND_TOKEN_SECRET, the
    same way server.py's _allowed_origins() refuses a "*" wildcard: a
    default signing secret would mean anyone could forge a session."""

    def test_a_missing_secret_is_rejected(self):
        with self.assertRaises(ValueError):
            token_secret_from_env({})

    def test_an_empty_secret_is_also_rejected(self):
        with self.assertRaises(ValueError):
            token_secret_from_env({"PLAYGROUND_TOKEN_SECRET": ""})

    def test_a_real_secret_passes_through(self):
        self.assertEqual(
            token_secret_from_env({"PLAYGROUND_TOKEN_SECRET": "real-secret"}), "real-secret"
        )


class TestVerifyGoogleIdToken(unittest.TestCase):
    """The Google verification call itself is IO (it fetches Google's public
    keys) -- verifier is injectable so these tests never reach the network.
    See playground/auth.py."""

    def test_a_verified_token_returns_the_email_claim(self):
        email = verify_google_id_token(
            "some-id-token",
            "client-id.apps.googleusercontent.com",
            verifier=lambda idt, aud: {"email": "learner@example.com", "aud": aud},
        )
        self.assertEqual(email, "learner@example.com")

    def test_a_verifier_that_raises_is_wrapped_as_an_auth_error(self):
        """google.oauth2.id_token.verify_oauth2_token raises ValueError for
        every failure mode -- bad signature, wrong issuer, wrong audience,
        expired. Whatever it raises must become AuthError, not escape as a
        raw exception the route handler doesn't expect."""

        def failing_verifier(idt, aud):
            raise ValueError("Token expired")

        with self.assertRaises(AuthError):
            verify_google_id_token("bad-token", "client-id", verifier=failing_verifier)

    def test_a_verified_claims_set_with_no_email_is_rejected(self):
        """A token can verify (real signature, real issuer) and still carry
        no email -- e.g. a Google Workspace policy that omits it. Email is
        the only identity this service checks, so no email is no session."""
        with self.assertRaises(AuthError):
            verify_google_id_token(
                "some-id-token", "client-id", verifier=lambda idt, aud: {"sub": "12345"}
            )


if __name__ == "__main__":
    unittest.main()
