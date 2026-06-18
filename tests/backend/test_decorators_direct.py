import os
import sys
import unittest
from flask import Flask, jsonify, session

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

from decorators import login_required, requiere_rol, admin_required  # noqa: E402


class TestDecoratorsDirect(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.config["TESTING"] = True

        @self.app.route("/api/privada")
        @login_required
        def privada():
            return jsonify({"ok": True})

        @self.app.route("/api/admin")
        @admin_required
        def admin():
            return jsonify({"ok": True})

        @self.app.route("/api/rol")
        @requiere_rol("desarrollador")
        def solo_dev():
            return jsonify({"ok": True})

        self.client = self.app.test_client()

    def test_login_required_without_session(self):
        r = self.client.get("/api/privada")
        self.assertEqual(r.status_code, 401)

    def test_login_required_with_session(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {
                "usuario_id": "dev-001",
                "rol": "desarrollador",
                "session_token": "abc"
            }
            sess["session_token"] = "abc"
        r = self.client.get("/api/privada")
        self.assertEqual(r.status_code, 200)

    def test_login_required_session_mismatch(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {
                "usuario_id": "dev-001",
                "rol": "desarrollador",
                "session_token": "abc"
            }
            sess["session_token"] = "xyz"
        r = self.client.get("/api/privada")
        self.assertEqual(r.status_code, 401)

    def test_admin_required_forbidden(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {
                "usuario_id": "usr-003",
                "rol": "vendedor",
                "session_token": "abc"
            }
            sess["session_token"] = "abc"
        r = self.client.get("/api/admin")
        self.assertEqual(r.status_code, 403)

    def test_admin_required_ok(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {
                "usuario_id": "dev-001",
                "rol": "desarrollador",
                "session_token": "abc"
            }
            sess["session_token"] = "abc"
        r = self.client.get("/api/admin")
        self.assertEqual(r.status_code, 200)

    def test_requiere_rol_forbidden(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {
                "usuario_id": "usr-001",
                "rol": "administrador",
                "session_token": "abc"
            }
            sess["session_token"] = "abc"
        r = self.client.get("/api/rol")
        self.assertEqual(r.status_code, 403)

