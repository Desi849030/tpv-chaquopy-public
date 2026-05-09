"""Tests de API con fixtures y BD aislada."""
import pytest

class TestHealth:
    def test_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
    def test_json(self, client):
        r = client.get("/api/health")
        assert r.content_type.startswith("application/json")
    def test_ok(self, client):
        data = client.get("/api/health").get_json()
        assert data.get("ok") is True or data.get("status") == "ok"

class TestAuth:
    def test_no_creds(self, client):
        r = client.post("/api/auth/login", json={"username": "", "password": ""})
        assert r.status_code in (400, 401)
    def test_protected(self, client):
        assert client.get("/api/catalogo").status_code in (401, 302, 403)

class TestImportValidado:
    def test_empty(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [], "ejecutar": False})
        assert r.status_code == 400 and r.get_json()["ok"] is False
    def test_missing_id(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"nombre": "X", "precio": 10.0}], "ejecutar": False})
        assert r.status_code == 400 and r.get_json()["fase"] == "validacion"
    def test_neg_price(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"id": "N1", "nombre": "N", "precio": -5.0}], "ejecutar": False})
        assert r.status_code == 400
    def test_dry_run(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"id": "OK1", "nombre": "OK", "precio": 10.0, "stock_actual": 50}], "ejecutar": False})
        assert r.status_code == 200 and r.get_json()["fase"] == "validacion_ok"
