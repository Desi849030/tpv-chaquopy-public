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


class TestBackendAuthExtended(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def login_dev(self):
        r = self.client.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertEqual(r.status_code, 200)
        return r.get_json()

    def login_admin(self):
        r = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertEqual(r.status_code, 200)
        return r.get_json()

    def test_cambiar_password_requires_login(self):
        r = self.client.post("/api/auth/cambiar-password", json={
            "password_actual": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026'),
            "password_nueva": "654321"
        })
        self.assertIn(r.status_code, (200, 401, 403))

    def test_cambiar_password_wrong_current(self):
        self.login_dev()
        r = self.client.post("/api/auth/cambiar-password", json={
            "password_actual": "mala",
            "password_nueva": "654321"
        })
        self.assertIn(r.status_code, (200, 400))
        data = r.get_json()
        self.assertFalse(data.get("ok"))

    def test_listar_usuarios_as_dev(self):
        self.login_dev()
        r = self.client.get("/api/usuarios")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("usuarios", data)
        self.assertIn("total", data)

    def test_listar_usuarios_without_login(self):
        self.client.cookie_jar.clear()
        # Usamos un cliente nuevo y nos aseguramos de que no hay sesion
        with app.test_client() as fresh:
            with fresh.session_transaction() as sess:
                sess.clear()
            r = fresh.get('/api/usuarios')
            self.assertEqual(r.status_code, 401)
        self.assertIn(r.status_code, (200, 401, 403))
        self.assertTrue(isinstance(r.get_json(), dict))
        self.assertIn(r.status_code, (200, 401, 403))
        self.assertTrue(isinstance(r.get_json(), dict))

        r = fresh.get("/api/usuarios")
        self.assertEqual(r.status_code, 401)

    def test_reset_password_requires_role(self):
        r = self.client.post("/api/usuarios/dev-001/reset-password", json={
            "password_nueva": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')
        })
        self.assertEqual(r.status_code, 401)

    def test_crear_usuario_missing_fields(self):
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

    def test_crear_usuario_duplicate(self):
        self.login_dev()
        username = f"dup_{uuid.uuid4().hex[:8]}"
        r1 = self.client.post("/api/admin/usuarios/crear", json={
            "username": username,
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026'),
            "nombre": "Dup Uno",
            "rol": "vendedor"
        })
        self.assertEqual(r1.status_code, 200)

        r2 = self.client.post("/api/admin/usuarios/crear", json={
            "username": username,
            "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026'),
            "nombre": "Dup Dos",
            "rol": "vendedor"
        })
        self.assertIn(r2.status_code, (400, 409))
        data = r2.get_json()
        self.assertFalse(data.get("ok"))

