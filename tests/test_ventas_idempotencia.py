"""Tests de idempotencia y rollback de ventas atómicas."""
import os
import sys
import uuid

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

from db_connection import obtener_conexion  # noqa: E402


class TestVentasIdempotentes:
    def test_reintento_mismo_client_txn_id_no_duplica(self, client):
        conn = obtener_conexion()
        stock_antes = conn.execute(
            "SELECT stock_actual FROM inventario_general WHERE producto_id='p1'"
        ).fetchone()[0]
        conn.close()

        payload = {
            "client_txn_id": "idem-test-" + uuid.uuid4().hex[:12],
            "metodo_pago": "efectivo",
            "items": [
                {"id": "p1", "nombre": "Arroz Premium 1kg", "cantidad": 2, "precio": 25.50}
            ],
        }

        r1 = client.post("/api/ventas/registrar", json=payload)
        assert r1.status_code == 200
        d1 = r1.get_json()
        assert d1["ok"] is True
        assert d1["idempotent"] is False

        r2 = client.post("/api/ventas/registrar", json=payload)
        assert r2.status_code == 200
        d2 = r2.get_json()
        assert d2["ok"] is True
        assert d2["idempotent"] is True
        assert d2["venta_id"] == d1["venta_id"]
        assert d2["total"] == d1["total"]

        conn = obtener_conexion()
        stock_despues = conn.execute(
            "SELECT stock_actual FROM inventario_general WHERE producto_id='p1'"
        ).fetchone()[0]
        total_cabecera = conn.execute(
            "SELECT COUNT(*) FROM ventas_cabecera WHERE client_txn_id=?",
            (payload["client_txn_id"],),
        ).fetchone()[0]
        total_detalle = conn.execute(
            "SELECT COUNT(*) FROM ventas_detalle WHERE venta_id=?",
            (d1["venta_id"],),
        ).fetchone()[0]
        conn.close()

        assert total_cabecera == 1
        assert total_detalle == 1
        assert float(stock_antes) - float(stock_despues) == 2.0

    def test_fallo_por_stock_hace_rollback_total(self, client):
        conn = obtener_conexion()
        stock_antes = conn.execute(
            "SELECT stock_actual FROM inventario_general WHERE producto_id='p2'"
        ).fetchone()[0]
        conn.close()

        payload = {
            "client_txn_id": "idem-test-rollback-" + uuid.uuid4().hex[:12],
            "metodo_pago": "efectivo",
            "items": [
                {"id": "p2", "nombre": "Frijoles Negros 500g", "cantidad": 1, "precio": 18.75},
                {"id": "p2", "nombre": "Frijoles Negros 500g", "cantidad": 9999, "precio": 18.75},
            ],
        }

        r = client.post("/api/ventas/registrar", json=payload)
        assert r.status_code == 409
        d = r.get_json()
        assert d["ok"] is False
        assert d["code"] == "STOCK_INSUFICIENTE"

        conn = obtener_conexion()
        stock_despues = conn.execute(
            "SELECT stock_actual FROM inventario_general WHERE producto_id='p2'"
        ).fetchone()[0]
        cabecera = conn.execute(
            "SELECT COUNT(*) FROM ventas_cabecera WHERE client_txn_id=?",
            (payload["client_txn_id"],),
        ).fetchone()[0]
        conn.close()

        assert float(stock_despues) == float(stock_antes)
        assert cabecera == 0
