import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendAuthMore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def login_dev(self):
        return self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": "123456"
        })

    def test_delete_usuario(self):
        self.login_dev()
        r = self.client.delete("/api/usuarios/usr-004")
        self.assertIn(r.status_code, (200, 400))
        self.assertTrue(isinstance(r.get_json(), dict))

    def test_licencias_verificar(self):
        self.login_dev()
        r = self.client.get("/api/licencias/verificar/usr-001")
        self.assertEqual(r.status_code, 200)

    def test_licencias_list(self):
        self.login_dev()
        r = self.client.get("/api/licencias")
        self.assertEqual(r.status_code, 200)

