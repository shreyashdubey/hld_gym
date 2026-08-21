import os
import unittest

from fastapi.testclient import TestClient


class TestHealth(unittest.TestCase):
    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "sk-secret-do-not-leak"
        from playground.server import app

        self.client = TestClient(app)

    def test_health_reports_key_loaded(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True, "key_loaded": True})

    def test_health_never_echoes_the_key(self):
        r = self.client.get("/health")
        self.assertNotIn("sk-secret-do-not-leak", r.text)


if __name__ == "__main__":
    unittest.main()
