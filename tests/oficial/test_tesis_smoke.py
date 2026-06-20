import os
import unittest
import requests

BASE = "http://127.0.0.1:5000"


class TestTesisSmoke(unittest.TestCase):

    def test_health(self):
        r = requests.get(f"{BASE}/api/health", timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("ok"))

    def test_login_dev(self):
        r = requests.post(
            f"{BASE}/api/auth/login",
            json={"username": "desarrollador", "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')},
            timeout=10
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data["usuario"]["rol"], "desarrollador")

    def test_login_admin(self):
        r = requests.post(
            f"{BASE}/api/auth/login",
            json={"username": "admin", "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')},
            timeout=10
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data["usuario"]["rol"], "administrador")

    def test_auth_me_dev(self):
        s = requests.Session()
        r = s.post(
            f"{BASE}/api/auth/login",
            json={"username": "desarrollador", "password": os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')},
            timeout=10
        )
        self.assertEqual(r.status_code, 200)
        r2 = s.get(f"{BASE}/api/auth/me", timeout=10)
        self.assertEqual(r2.status_code, 200)
        data = r2.json()
        self.assertTrue(data.get("autenticado"))
        self.assertEqual(data["usuario"]["username"], "desarrollador")

    def test_catalogo_publico(self):
        r = requests.get(f"{BASE}/api/publico/catalogo", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(isinstance(data, dict))


if __name__ == "__main__":
    unittest.main()
