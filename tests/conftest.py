# -*- coding: utf-8 -*-
"""conftest.py - Fixtures compartidos v8.9.

Incluye fixtures para tests con sesion atomica (client, client_anon)
y compat con tests antiguos (tmp_db_dir module-scoped)."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'
))


@pytest.fixture
def app():
    os.environ['TPV_TESTING'] = '1'
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Cliente HTTP CON sesion de desarrollador (v8.9)."""
    with app.test_client() as c:
        c.post("/api/auth/login", json={
            "username": "desarrollador",
            "password": os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
        })
        yield c


@pytest.fixture
def client_anon(app):
    """Cliente HTTP SIN sesion."""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def tmp_db_dir(tmp_path_factory):
    """Directorio temporal MODULE-scoped (compat tests antiguos)."""
    return tmp_path_factory.mktemp("tpv_test_db")
