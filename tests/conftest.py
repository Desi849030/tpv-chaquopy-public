"""tests/conftest.py — Fixtures compartidas para pytest."""
import os, sys, tempfile, shutil
APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python")
if os.path.abspath(APP_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(APP_DIR))
import pytest

@pytest.fixture(scope="session")
def tmp_db_dir():
    d = tempfile.mkdtemp(prefix="tpv_test_")
    os.environ["TPV_FILES_DIR"] = d
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture(scope="session")
def app(tmp_db_dir):
    os.environ["TPV_FRONTEND_DIR"] = os.path.join(os.path.abspath(APP_DIR), "..", "assets", "frontend")
    from database import crear_tablas
    crear_tablas()
    from app import app as _app
    _app.config["TESTING"] = True
    _app.config["DEBUG"] = False
    return _app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session(app, client):
    with client.session_transaction() as sess:
        sess["usuario"] = {"usuario_id": "test-dev-001", "username": "desarrollador", "rol": "desarrollador", "nombre": "Test Dev"}
    return sess

@pytest.fixture
def session_admin(app, client):
    with client.session_transaction() as sess:
        sess["usuario"] = {"usuario_id": "test-admin-001", "username": "admin", "rol": "administrador", "nombre": "Test Admin"}
    return sess
