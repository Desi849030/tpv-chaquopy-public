"""Tests de endurecimiento para endpoints de escritura."""
import os
import sys

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestSeguridadEscritura:
    def test_catalogo_crear_requiere_auth(self, client_anon):
        r = client_anon.post("/api/catalogo/crear", json={"nombre": "X", "precio": 10})
        assert r.status_code == 401

    def test_importar_excel_requiere_auth(self, client_anon):
        r = client_anon.post("/api/importar/excel", json={"productos": [{"nombre": "X", "precio": 10}]})
        assert r.status_code == 401

    def test_previsualizar_importacion_requiere_auth(self, client_anon):
        r = client_anon.post("/api/importar/previsualizar", json={"productos": [{"nombre": "X"}]})
        assert r.status_code == 401

    def test_catalogo_sync_requiere_auth(self, client_anon):
        r = client_anon.post("/api/catalogo/sync", json={"productos": []})
        assert r.status_code == 401

    def test_dev_puede_crear_producto(self, client):
        r = client.post("/api/catalogo/crear", json={"nombre": "SecTestProd", "precio": 11})
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

    def test_dev_puede_previsualizar_importacion(self, client):
        r = client.post("/api/importar/previsualizar", json={"productos": [{"nombre": "X"}]})
        assert r.status_code == 200
        assert r.get_json()["ok"] is True
