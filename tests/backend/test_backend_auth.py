import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))

    def test_login_dev_ok(self):
        r = self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data["usuario"]["rol"], "desarrollador")

    def test_login_admin_ok(self):
        r = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data["usuario"]["rol"], "administrador")

    def test_login_fail_missing_fields(self):
        r = self.client.post("/api/auth/login", json={
            "username": "",
            "password": ""
        })
        self.assertEqual(r.status_code, 400)
        data = r.get_json()
        self.assertFalse(data.get("ok"))

    def test_login_fail_wrong_password(self):
        r = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "incorrecta"
        })
        self.assertEqual(r.status_code, 401)
        data = r.get_json()
        self.assertFalse(data.get("ok"))

    def test_auth_me_without_session(self):
        r = self.client.get("/api/auth/me")
        self.assertEqual(r.status_code, 401)
        data = r.get_json()
        self.assertFalse(data.get("autenticado"))

    def test_auth_me_with_session(self):
        self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        r = self.client.get("/api/auth/me")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("autenticado"))
        self.assertEqual(data["usuario"]["username"], "desarrollador")

    def test_logout(self):
        self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        r = self.client.post("/api/auth/logout")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))

