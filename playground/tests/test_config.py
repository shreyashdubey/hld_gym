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

    def test_rejects_the_two_personas_sharing_a_voice(self):
        """Explicit construction with identical voices must fail, catching
        regressions through from_env or any other path."""
        with self.assertRaises(ValueError) as ctx:
            VoiceConfig(interviewer_voice="onyx", coach_voice="onyx")
        self.assertIn("interviewer_voice", str(ctx.exception))
        self.assertIn("coach_voice", str(ctx.exception))

    def test_from_env_rejects_malformed_float(self):
        """Malformed float input must report the field and env var name."""
        with self.assertRaises(ValueError) as ctx:
            VoiceConfig.from_env({"PLAYGROUND_STOP_SECS": "not_a_number"})
        exc_msg = str(ctx.exception)
        self.assertIn("PLAYGROUND_STOP_SECS", exc_msg)
        self.assertIn("not_a_number", exc_msg)

    def test_auth_fields_default_without_any_env(self):
        """A bare VoiceConfig() must keep working with no auth env set at
        all -- dictation never touches these, and the rest of this suite
        constructs VoiceConfig() bare throughout."""
        c = VoiceConfig()
        self.assertEqual(c.google_client_id, "")
        self.assertEqual(c.session_ttl_secs, 604800)

    def test_from_env_reads_the_google_client_id_as_a_plain_string(self):
        c = VoiceConfig.from_env({"PLAYGROUND_GOOGLE_CLIENT_ID": "abc123.apps.googleusercontent.com"})
        self.assertEqual(c.google_client_id, "abc123.apps.googleusercontent.com")

    def test_the_signing_secret_is_not_a_config_field(self):
        """It has no default anywhere, on purpose -- token_secret_from_env()
        raises instead. A VoiceConfig field would have re-added a silently
        empty-defaulting copy of it. See config.py's comment."""
        self.assertNotIn("token_secret", VoiceConfig.__dataclass_fields__)
        c = VoiceConfig.from_env({"PLAYGROUND_TOKEN_SECRET": "s3cret"})
        self.assertFalse(hasattr(c, "token_secret"))

    def test_from_env_coerces_session_ttl_secs_to_int(self):
        """The float-coercion path already existed; int fields shared no
        code with it until now -- session_ttl_secs is the first int field on
        VoiceConfig."""
        c = VoiceConfig.from_env({"PLAYGROUND_SESSION_TTL_SECS": "3600"})
        self.assertEqual(c.session_ttl_secs, 3600)
        self.assertIsInstance(c.session_ttl_secs, int)

    def test_from_env_rejects_a_malformed_session_ttl_secs(self):
        with self.assertRaises(ValueError) as ctx:
            VoiceConfig.from_env({"PLAYGROUND_SESSION_TTL_SECS": "a week"})
        exc_msg = str(ctx.exception)
        self.assertIn("PLAYGROUND_SESSION_TTL_SECS", exc_msg)
        self.assertIn("a week", exc_msg)

    def test_diagnostic_cap_defaults_to_six_minutes(self):
        self.assertEqual(VoiceConfig().diagnostic_cap_secs, 360.0)

    def test_diagnostic_cap_is_env_overridable(self):
        config = VoiceConfig.from_env({"PLAYGROUND_DIAGNOSTIC_CAP_SECS": "120"})
        self.assertEqual(config.diagnostic_cap_secs, 120.0)


if __name__ == "__main__":
    unittest.main()
