import unittest
import requests
import uuid

BASE = "http://127.0.0.1:5000"


class TestAuthRoles(unittest.TestCase):

    def test_login_fail_wrong_password(self):
        r = requests.post(
            f"{BASE}/api/auth/login",
            json={"username": "admin", "password": "incorrecta"},
            timeout=10
        )
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.json().get("ok"))

    def test_login_fail_missing_fields(self):
        r = requests.post(
            f"{BASE}/api/auth/login",
            json={"username": "", "password": ""},
            timeout=10
        )
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json().get("ok"))

    def test_auth_me_without_session(self):
        r = requests.get(f"{BASE}/api/auth/me", timeout=10)
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.json().get("autenticado"))

    def test_logout(self):
        s = requests.Session()
        r = s.post(
            f"{BASE}/api/auth/login",
            json={"username": "desarrollador", "password": "123456"},
            timeout=10
        )
        self.assertEqual(r.status_code, 200)

        r2 = s.post(f"{BASE}/api/auth/logout", timeout=10)
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("ok"))

    def test_admin_can_create_user(self):
        s = requests.Session()
        r = s.post(
            f"{BASE}/api/auth/login",
            json={"username": "desarrollador", "password": "123456"},
            timeout=10
        )
        self.assertEqual(r.status_code, 200)

        username = f"tesis_{uuid.uuid4().hex[:8]}"
        r2 = s.post(
            f"{BASE}/api/admin/usuarios/crear",
            json={
                "username": username,
                "password": "123456",
                "nombre": "Usuario Tesis",
                "rol": "vendedor"
            },
            timeout=10
        )
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("ok"))


if __name__ == "__main__":
    unittest.main()
