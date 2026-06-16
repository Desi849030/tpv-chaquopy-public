"""Tests para reportes: contar tickets reales y no líneas."""
import os
import sys
import uuid

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestReportesTransacciones:
    def test_resumen_cuenta_una_venta_por_ticket(self, client):
        r0 = client.get("/api/reportes/resumen")
        assert r0.status_code == 200
        base = r0.get_json().get("resumen", {})
        tx0 = int(base.get("transacciones_hoy", 0))
        ventas0 = float(base.get("ventas_hoy", 0) or 0)

        payload = {
            "client_txn_id": "rep-" + uuid.uuid4().hex[:12],
            "metodo_pago": "efectivo",
            "items": [
                {"id": "p1", "nombre": "Arroz Premium 1kg", "cantidad": 1, "precio": 25.50},
                {"id": "p2", "nombre": "Frijoles Negros 500g", "cantidad": 1, "precio": 18.75},
            ],
        }
        rv = client.post("/api/ventas/registrar", json=payload)
        assert rv.status_code == 200
        dv = rv.get_json()
        assert dv["ok"] is True
        total_ticket = float(dv["total"])

        r1 = client.get("/api/reportes/resumen")
        assert r1.status_code == 200
        now = r1.get_json().get("resumen", {})

        assert int(now.get("transacciones_hoy", 0)) == tx0 + 1
        assert float(now.get("ventas_hoy", 0) or 0) >= ventas0 + total_ticket

    def test_metrics_cuenta_tickets_reales(self, client):
        r0 = client.get("/api/metrics")
        assert r0.status_code == 200
        base = r0.get_json()
        tx0 = int(base.get("ventas_hoy", 0) or 0)

        payload = {
            "client_txn_id": "met-" + uuid.uuid4().hex[:12],
            "metodo_pago": "tarjeta",
            "items": [
                {"id": "p3", "nombre": "Aceite Vegetal 1L", "cantidad": 1, "precio": 45.00},
                {"id": "p4", "nombre": "Refresco Cola 2L", "cantidad": 1, "precio": 32.00},
                {"id": "p5", "nombre": "Jabon Liquido Multiusos", "cantidad": 1, "precio": 55.00},
            ],
        }
        rv = client.post("/api/ventas/registrar", json=payload)
        assert rv.status_code == 200
        assert rv.get_json()["ok"] is True

        r1 = client.get("/api/metrics")
        assert r1.status_code == 200
        now = r1.get_json()
        assert int(now.get("ventas_hoy", 0) or 0) == tx0 + 1
