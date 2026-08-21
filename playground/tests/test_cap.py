import unittest

from playground.config import VoiceConfig
from playground.session import Session


class TestSessionCap(unittest.TestCase):
    """Voice bills by the minute, so the session ends whether or not anyone
    remembers to stop it. Announced at the start, never enforced silently."""

    def setUp(self):
        self.s = Session(VoiceConfig(session_cap_secs=600))
        self.s.start(now=1000.0)

    def test_a_fresh_session_has_the_full_budget(self):
        self.assertEqual(self.s.remaining_secs(now=1000.0), 600)

    def test_time_spent_comes_off_the_budget(self):
        self.assertEqual(self.s.remaining_secs(now=1060.0), 540)

    def test_it_expires_at_the_cap(self):
        self.assertTrue(self.s.expired(now=1600.0))

    def test_it_does_not_expire_early(self):
        self.assertFalse(self.s.expired(now=1599.0))

    def test_remaining_never_goes_negative(self):
        self.assertEqual(self.s.remaining_secs(now=9999.0), 0)


if __name__ == "__main__":
    unittest.main()
