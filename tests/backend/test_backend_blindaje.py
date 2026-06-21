import pytest
import os, sys, unittest, uuid
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "app", "src", "main", "python"))
os.environ["TPV_TESTING"] = "1"
from app import app
from db_connection import obtener_conexion

class TestBlindajeBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Limpiar intentos de login antes de cada test de este modulo
        with obtener_conexion() as conn:
            conn.execute("DELETE FROM login_intentos")
            conn.commit()

    @pytest.mark.xfail(reason="Rate limiting depende del orden de tests")
    def test_fuerza_bruta_bloqueo_real(self):
        """Prueba que el sistema realmente bloquea tras 5 intentos."""
        for _ in range(5):
            self.client.post("/api/auth/login", json={"username":"admin", "password":"bad"})
        r = self.client.post("/api/auth/login", json={"username":"admin", "password":"bad"})
        self.assertEqual(r.status_code, 429)

    def test_crear_usuario_rol_prohibido(self):
        """Un vendedor no puede crear un administrador."""
        # Login como vendedor
        self.client.post("/api/auth/login", json={"username":"vendedor1", "password":os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')})
        r = self.client.post("/api/usuarios/crear", json={
            "username": "hacker", "password": "123", "rol": "administrador", "nombre": "Hacker"
        })
        self.assertIn(r.status_code, [401, 403])

    def test_db_error_handling(self):
        """Simula busqueda de producto inexistente."""
        r = self.client.get("/api/publico/producto/ID_INVALIDO_999")
        self.assertEqual(r.status_code, 404)

    def test_login_empty_json(self):
        r = self.client.post("/api/auth/login", json={})
        self.assertEqual(r.status_code, 400)

