"""Tests para endpoints de documentación y tests info"""
import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

from app import app as _app

DEMO_PW = os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")

@pytest.fixture
def app():
    _app.config["TESTING"] = True
    _app.config["SECRET_KEY"] = "test"
    return _app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def dev_client(client):
    client.post("/api/auth/login", json={"username": "desarrollador", "password": DEMO_PW})
    return client


class TestDevDocs:
    def test_dev_docs_200(self, dev_client):
        r = dev_client.get("/api/dev/docs")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["ok"] == True
        assert "endpoints" in data
        assert "modulos" in data
        assert "estadisticas" in data

    def test_dev_docs_sin_login_401(self, client):
        r = client.get("/api/dev/docs")
        assert r.status_code == 401

    def test_dev_docs_tiene_documentos(self, dev_client):
        r = dev_client.get("/api/dev/docs")
        data = json.loads(r.data)
        assert "contenido_documentos" in data
        assert len(data["contenido_documentos"]) >= 5

    def test_dev_docs_tiene_221_endpoints(self, dev_client):
        r = dev_client.get("/api/dev/docs")
        data = json.loads(r.data)
        assert data["endpoints_total"] >= 200


class TestTestsInfo:
    def test_tests_resumen_200(self, dev_client):
        r = dev_client.get("/api/tests/resumen")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["ok"] == True
        assert data["total_tests"] == 510

    def test_tests_resumen_sin_login_401(self, client):
        r = client.get("/api/tests/resumen")
        assert r.status_code == 401

    def test_tests_cobertura_200(self, dev_client):
        r = dev_client.get("/api/tests/cobertura")
        assert r.status_code == 200

    def test_tests_resultados_200(self, dev_client):
        r = dev_client.get("/api/tests/resultados")
        assert r.status_code == 200
