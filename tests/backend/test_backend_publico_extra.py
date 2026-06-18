import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendPublicoExtra(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def test_catalogo_meta(self):
        r = self.client.get("/api/publico/catalogo")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("meta", data)

    def test_catalogo_total(self):
        r = self.client.get("/api/publico/catalogo")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("total", data)
        self.assertTrue(data["total"] >= 0)

