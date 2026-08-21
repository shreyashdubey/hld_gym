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
