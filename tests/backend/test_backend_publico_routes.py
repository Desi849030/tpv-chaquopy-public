import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from app import app  # noqa: E402


class TestBackendPublicoRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True

    def setUp(self):
        self.client = app.test_client()

    def test_identity(self):
        r = self.client.get("/api/publico/identity")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(isinstance(data, dict))

    def test_buscar_query_corta(self):
        r = self.client.get("/api/publico/buscar?q=a")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertFalse(data.get("ok"))
        self.assertIn("productos", data)

    def test_buscar_ok(self):
        r = self.client.get("/api/publico/buscar?q=arroz")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("productos", data)

    def test_ofertas(self):
        r = self.client.get("/api/publico/ofertas")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("ofertas", data)

    def test_producto_detalle_ok(self):
        r = self.client.get("/api/publico/producto/p1")
        self.assertIn(r.status_code, (200, 404))
        data = r.get_json()
        self.assertTrue(isinstance(data, dict))

    def test_producto_detalle_not_found(self):
        r = self.client.get("/api/publico/producto/no-existe")
        self.assertEqual(r.status_code, 404)
        data = r.get_json()
        self.assertFalse(data.get("ok"))

    def test_categorias(self):
        r = self.client.get("/api/publico/categorias")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("categorias", data)

    def test_categoria_ok(self):
        r = self.client.get("/api/publico/categoria/Alimentos")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("productos", data)

    def test_tiendas_info(self):
        r = self.client.get("/api/publico/tiendas-info")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("tiendas", data)

