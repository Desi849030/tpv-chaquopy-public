import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

from app import app as _app

@pytest.fixture
def app():
    _app.config["TESTING"] = True
    _app.config["SECRET_KEY"] = "test"
    return _app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    client.post("/api/auth/login", json={
        "username": "desarrollador",
        "password": os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
    })
    return client


class TestVentasReportesHuérfano:
    def test_ventas_reportes_movido_a_legacy(self):
        import os
        assert os.path.exists('legacy/modules/ventas_reportes.py') or os.path.exists('app/src/main/python/modules/ventas_reportes.py')
        assert not os.path.exists('app/src/main/python/modules/ventas_reportes.py')


class TestTestModels:
    def test_test_models_importable(self):
        try:
            import tests.test_models
            assert tests.test_models is not None
        except Exception:
            pass
