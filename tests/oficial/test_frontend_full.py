import unittest, os, requests
BASE = "http://127.0.0.1:5000"

class TestFrontendFull(unittest.TestCase):
    def test_page_load(self):
        """Verifica que el HTML principal carga y no esta vacio."""
        r = requests.get(f"{BASE}/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("<title>", r.text)

    def test_static_resources(self):
        """Verifica que el CSS principal es accesible."""
        r = requests.get(f"{BASE}/static/css/tpv_theme.css")
        self.assertEqual(r.status_code, 200)

    def test_api_compatibility(self):
        """Asegura que el frontend encontrara los endpoints necesarios."""
        endpoints = ["/api/publico/catalogo", "/api/metrics", "/api/health"]
        for ep in endpoints:
            r = requests.get(f"{BASE}{ep}")
            self.assertEqual(r.status_code, 200)
