import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendCatalogo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def test_catalogo_publico_ok(self):
        r = self.client.get("/api/publico/catalogo")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("productos", data)

    def test_catalogo_tiene_productos(self):
        r = self.client.get("/api/publico/catalogo")
        data = r.get_json()
        self.assertTrue(len(data["productos"]) > 0)

    def test_producto_tiene_campos(self):
        r = self.client.get("/api/publico/catalogo")
        productos = r.get_json()["productos"]
        p = productos[0]
        for field in ["id", "nombre", "precio", "categoria", "stock_total"]:
            self.assertIn(field, p)

    def test_producto_precio_valido(self):
        r = self.client.get("/api/publico/catalogo")
        productos = r.get_json()["productos"]
        self.assertTrue(any(float(p.get("precio", 0)) >= 0 for p in productos))

