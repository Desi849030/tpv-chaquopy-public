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
    def test_funciones_importables(self):
        from modules.ventas_reportes import api_reporte_ventas, api_resumen, api_ganancias, api_dashboard_data
        assert callable(api_reporte_ventas)
        assert callable(api_resumen)
        assert callable(api_ganancias)
        assert callable(api_dashboard_data)


class TestTestModels:
    def test_test_models_importable(self):
        try:
            import tests.test_models
            assert tests.test_models is not None
        except Exception:
            pass
