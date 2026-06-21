import unittest
import requests

BASE = "http://127.0.0.1:5050"


class TestCatalogoShape(unittest.TestCase):

    def test_catalogo_has_productos(self):
        r = requests.get(f"{BASE}/api/publico/catalogo", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("productos", data)
        self.assertTrue(len(data["productos"]) > 0)

    def test_producto_has_required_fields(self):
        r = requests.get(f"{BASE}/api/publico/catalogo", timeout=10)
        self.assertEqual(r.status_code, 200)
        productos = r.json()["productos"]
        p = productos[0]
        for field in ["id", "nombre", "precio", "categoria", "stock_total"]:
            self.assertIn(field, p)

    def test_producto_precio_valido(self):
        r = requests.get(f"{BASE}/api/publico/catalogo", timeout=10)
        self.assertEqual(r.status_code, 200)
        productos = r.json()["productos"]
        self.assertTrue(any(float(p.get("precio", 0)) >= 0 for p in productos))


if __name__ == "__main__":
    unittest.main()
