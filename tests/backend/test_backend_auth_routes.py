import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendAuthRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def login_dev(self):
        return self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })

    def login_admin(self):
        return self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })

    def test_logout_ok(self):
        self.login_dev()
        r = self.client.post("/api/auth/logout")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json().get("ok"))

    def test_listar_usuarios_dev(self):
        self.login_dev()
        r = self.client.get("/api/usuarios")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("usuarios", data)

    def test_reset_password_as_dev(self):
        self.login_dev()
        r = self.client.post("/api/usuarios/usr-001/reset-password", json={
            "password_nueva": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertIn(r.status_code, (200, 400))
        self.assertTrue(isinstance(r.get_json(), dict))

    def test_licencias_list(self):
        self.login_dev()
        r = self.client.get("/api/licencias")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("licencias", data)

    def test_licencia_verificar(self):
        self.login_dev()
        r = self.client.get("/api/licencias/verificar/usr-001")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("tiene_licencia", data)

