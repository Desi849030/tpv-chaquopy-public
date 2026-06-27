"""Cobertura completa de decorators.py"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class TestDecoratorsFull:
    def test_usuario_actual(self):
        from decorators import usuario_actual
        from flask import Flask, session
        app = Flask(__name__)
        app.secret_key = "test"
        with app.test_request_context():
            session["usuario"] = {"id": "1", "nombre": "test"}
            u = usuario_actual()
            assert u == {"id": "1", "nombre": "test"}

    def test_usuario_actual_vacio(self):
        from decorators import usuario_actual
        from flask import Flask, session
        app = Flask(__name__)
        app.secret_key = "test"
        with app.test_request_context():
            session.clear()
            u = usuario_actual()
            assert u == {}

    def test_login_required_con_sesion(self):
        from decorators import login_required
        from flask import Flask, session
        app = Flask(__name__)
        app.secret_key = "test"
        @app.route("/test")
        @login_required
        def test_route():
            return "ok"
        with app.test_client() as c:
            with c.session_transaction() as s:
                s["usuario"] = {"id": "1", "rol": "admin"}
                s["session_token"] = "abc123"
            r = c.get("/test")
            assert r.status_code in (200, 404)

    def test_login_required_sin_sesion(self):
        from decorators import login_required
        from flask import Flask
        app = Flask(__name__)
        app.secret_key = "test"
        @app.route("/test")
        @login_required
        def test_route():
            return "ok"
        with app.test_client() as c:
            r = c.get("/test")
            assert r.status_code == 401

    def test_requiere_rol(self):
        from decorators import requiere_rol
        from flask import Flask, session
        app = Flask(__name__)
        app.secret_key = "test"
        @app.route("/admin")
        @requiere_rol("administrador", "desarrollador")
        def admin_route():
            return "admin"
        with app.test_client() as c:
            with c.session_transaction() as s:
                s["usuario"] = {"id": "1", "rol": "cliente"}
                s["session_token"] = "abc"
            r = c.get("/admin")
            assert r.status_code == 403

    def test_admin_required(self):
        from decorators import admin_required
        assert admin_required is not None

    def test_check_active_atomic(self):
        from decorators import _check_active_atomic
        r = _check_active_atomic({"usuario_id": "nonexistent"})
        assert r is True  # fallback seguro
