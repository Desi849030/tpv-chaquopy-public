import os
import sys
import pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

@pytest.fixture
def client_noauth():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_ventas_registrar_requiere_login(client_noauth):
    r = client_noauth.post("/api/ventas/registrar", json={
        "items": [{"id": "p1", "nombre": "Cafe", "cantidad": 1, "precio": 2.0}]
    })
    assert r.status_code == 401
    d = r.get_json()
    assert d["code"] == "AUTH_REQUIRED"

def test_ventas_hoy_requiere_login(client_noauth):
    r = client_noauth.get("/api/ventas/hoy")
    assert r.status_code == 401
    d = r.get_json()
    assert d["code"] == "AUTH_REQUIRED"
