import os
import sys
import uuid
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendUsers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def login_dev(self):
        r = self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": "123456"
        })
        self.assertEqual(r.status_code, 200)

    def test_create_user_ok(self):
        self.login_dev()
        username = f"backend_{uuid.uuid4().hex[:8]}"
        r = self.client.post("/api/admin/usuarios/crear", json={
            "username": username,
            "password": "123456",
            "nombre": "Backend User",
            "rol": "vendedor"
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("usuario_id", data)

    def test_create_user_missing_fields(self):
        self.login_dev()
        r = self.client.post("/api/admin/usuarios/crear", json={
            "username": "",
            "password": "",
            "nombre": "",
            "rol": "vendedor"
        })
        self.assertIn(r.status_code, (400, 403))
        data = r.get_json()
        self.assertFalse(data.get("ok"))

