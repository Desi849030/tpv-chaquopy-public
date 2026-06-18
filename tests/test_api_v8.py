import unittest
import requests

BASE_URL = "http://127.0.0.1:5000/api"

class TestTPVCore(unittest.TestCase):
    def test_health_endpoint(self):
        """Verifica que el servidor responda."""
        r = requests.get(f"{BASE_URL}/health")
        self.assertEqual(r.status_code, 200)

    def test_auth_required(self):
        """Verifica que las rutas protegidas devuelvan 401."""
        r = requests.get(f"{BASE_URL}/ventas/totales")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['code'], 'AUTH_REQUIRED')

    def test_public_catalogo(self):
        """Verifica que el catálogo público funcione."""
        r = requests.get(f"{BASE_URL}/publico/catalogo")
        self.assertEqual(r.status_code, 200)

if __name__ == "__main__":
    unittest.main()
