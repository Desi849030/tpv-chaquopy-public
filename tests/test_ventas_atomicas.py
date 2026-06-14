"""test_ventas_atomicas.py — Tests de la venta atómica (#4) y consultas de ventas."""
import os, sys, pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


@pytest.fixture(scope="module")
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["usuario"] = {"id": "dev-001", "usuario_id": "dev-001",
                               "username": "test", "nombre": "Test", "rol": "desarrollador"}
        yield c


class TestRegistrarVenta:
    def test_venta_simple_ok(self, client):
        r = client.post("/api/ventas/registrar", json={
            "items": [{"id": "p-test-1", "nombre": "Café test", "cantidad": 2, "precio": 1.5}],
            "metodo_pago": "efectivo", "vendedor": "test",
        })
        assert r.status_code == 200
        d = r.get_json()
        assert d["ok"] is True
        assert d["total"] == 3.0
        assert d["items"] == 1
        assert d["venta_id"].startswith("vta-")

    def test_venta_multi_items_total_correcto(self, client):
        r = client.post("/api/ventas/registrar", json={
            "items": [
                {"id": "p-a", "nombre": "A", "cantidad": 3, "precio": 2.0},
                {"id": "p-b", "nombre": "B", "cantidad": 1, "precio": 5.5},
            ],
            "metodo_pago": "tarjeta", "vendedor": "test",
        })
        assert r.status_code == 200
        d = r.get_json()
        assert d["ok"] is True
        assert d["total"] == 11.5
        assert d["items"] == 2

    def test_venta_sin_items_rechazada(self, client):
        r = client.post("/api/ventas/registrar", json={"items": [], "vendedor": "test"})
        assert r.status_code == 400
        assert r.get_json()["ok"] is False

    def test_venta_aparece_en_hoy(self, client):
        client.post("/api/ventas/registrar", json={
            "items": [{"id": "p-hoy", "nombre": "ProdHoy", "cantidad": 1, "precio": 9.0}],
            "vendedor": "test",
        })
        r = client.get("/api/ventas/hoy")
        assert r.status_code == 200
        d = r.get_json()
        assert d["ok"] is True
        assert d["cantidad"] >= 1


class TestTotales:
    def test_totales_responde(self, client):
        r = client.get("/api/ventas/totales")
        assert r.status_code == 200
        d = r.get_json()
        assert d["ok"] is True
        assert "hoy" in d and "mes" in d
