"""Tests para lectura de documentos Markdown desde el chat (rol desarrollador)"""
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


class TestDocumentReader:
    def test_leer_readme(self, dev_client):
        r = dev_client.post("/api/agent/chat", json={"mensaje": "leer documento readme"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("tipo") == "documento"
        assert "README" in data.get("respuesta", "")

    def test_leer_api_reference(self, dev_client):
        r = dev_client.post("/api/agent/chat", json={"mensaje": "mostrar api"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("tipo") == "documento"

    def test_siguiente_pagina(self, dev_client):
        # Abrir documento primero
        dev_client.post("/api/agent/chat", json={"mensaje": "leer readme"})
        r = dev_client.post("/api/agent/chat", json={"mensaje": "siguiente"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("tipo") == "documento"
        assert "página" in data.get("respuesta", "").lower() or "pagina" in data.get("respuesta", "").lower()

    def test_cerrar_documento(self, dev_client):
        dev_client.post("/api/agent/chat", json={"mensaje": "leer changelog"})
        r = dev_client.post("/api/agent/chat", json={"mensaje": "cerrar documento"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "cerrado" in data.get("respuesta", "").lower() or "info" == data.get("tipo")

    def test_documento_inexistente_no_rompe(self, dev_client):
        r = dev_client.post("/api/agent/chat", json={"mensaje": "leer documento inventado_xyz"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("tipo") in ("error", "documento", None)

    def test_admin_no_puede_leer_docs(self, client):
        client.post("/api/auth/login", json={"username": "admin", "password": DEMO_PW})
        r = client.post("/api/agent/chat", json={"mensaje": "leer readme"})
        assert r.status_code == 200
        data = json.loads(r.data)
        # Admin no debería recibir tipo 'documento'
        assert data.get("tipo") in (None, "text", "info", "greeting")  # admin no debería ver docs
