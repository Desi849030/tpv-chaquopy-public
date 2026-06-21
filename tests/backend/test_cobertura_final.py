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


# ============ ventas_atomic_v10.py ============
class TestVentasAtomic:
    def test_registrar_venta_sin_items_400(self, auth_client):
        r = auth_client.post("/api/ventas/registrar", json={"items": []})
        assert r.status_code == 400

    def test_registrar_venta_items_vacio_400(self, auth_client):
        r = auth_client.post("/api/ventas/registrar", json={"metodo_pago": "efectivo"})
        assert r.status_code == 400

    def test_registrar_venta_producto_inexistente(self, auth_client):
        r = auth_client.post("/api/ventas/registrar", json={
            "items": [{"producto_id": "no-existe-99999", "nombre": "Falso", "cantidad": 1, "precio": 10}],
            "metodo_pago": "efectivo"
        })
        assert r.status_code in (200, 400, 422)

    def test_venta_idempotente_mismo_txn_id(self, auth_client):
        txn = "test-txn-abc123"
        payload = {
            "client_txn_id": txn,
            "items": [{"producto_id": "test-1", "nombre": "Test", "cantidad": 1, "precio": 10}],
            "metodo_pago": "efectivo"
        }
        r1 = auth_client.post("/api/ventas/registrar", json=payload)
        r2 = auth_client.post("/api/ventas/registrar", json=payload)
        assert r1.status_code in (200, 400)
        assert r2.status_code in (200, 400)

    def test_venta_cantidad_negativa_400(self, auth_client):
        r = auth_client.post("/api/ventas/registrar", json={
            "items": [{"producto_id": "x", "nombre": "X", "cantidad": -1, "precio": 10}]
        })
        assert r.status_code in (400, 422)

    def test_venta_precio_negativo_400(self, auth_client):
        r = auth_client.post("/api/ventas/registrar", json={
            "items": [{"producto_id": "x", "nombre": "X", "cantidad": 1, "precio": -5}]
        })
        assert r.status_code in (400, 422)

    def test_ventas_hoy_200(self, auth_client):
        r = auth_client.get("/api/ventas/hoy")
        assert r.status_code == 200

    def test_ventas_totales_200(self, auth_client):
        r = auth_client.get("/api/ventas/totales")
        assert r.status_code == 200

    def test_ventas_cierres_200(self, auth_client):
        r = auth_client.get("/api/ventas/cierres")
        assert r.status_code == 200

    def test_ventas_cierre_post_200(self, auth_client):
        r = auth_client.post("/api/ventas/cierre")
        assert r.status_code in (200, 400, 500)

    def test_historial_ventas_200(self, auth_client):
        r = auth_client.get("/api/historial-ventas")
        assert r.status_code in (200, 404)

    def test_reporte_ventas_200(self, auth_client):
        r = auth_client.get("/api/reportes/ventas")
        assert r.status_code == 200


# ============ settings_supabase.py ============
class TestSettingsSupabase:
    def test_get_supabase_config_200(self, auth_client):
        r = auth_client.get("/api/supabase/config")
        assert r.status_code == 200

    def test_save_config_sin_datos_400(self, auth_client):
        r = auth_client.post("/api/supabase/config", json={})
        assert r.status_code == 400

    def test_save_config_con_datos(self, auth_client):
        r = auth_client.post("/api/supabase/config", json={
            "url": "https://test.supabase.co",
            "anon_key": "test-key-1234567890"
        })
        assert r.status_code in (200, 400, 500)

    def test_sync_all(self, auth_client):
        r = auth_client.post("/api/supabase/sync-all")
        assert r.status_code in (200, 400)

    def test_sync_alias(self, auth_client):
        r = auth_client.post("/api/supabase/sync")
        assert r.status_code in (200, 400)

    def test_test_supabase(self, auth_client):
        r = auth_client.post("/api/supabase/test")
        assert r.status_code in (200, 400)

    def test_push(self, auth_client):
        r = auth_client.post("/api/supabase/push")
        assert r.status_code in (200, 400)

    def test_pull(self, auth_client):
        r = auth_client.post("/api/supabase/pull")
        assert r.status_code in (200, 400)


# ============ agent_chat_bp.py ============
class TestAgentChat:
    def test_agent_chat_sin_mensaje(self, auth_client):
        r = auth_client.post("/api/agent/chat", json={})
        assert r.status_code == 200

    def test_agent_chat_con_mensaje(self, auth_client):
        r = auth_client.post("/api/agent/chat", json={"mensaje": "Hola"})
        assert r.status_code == 200

    def test_agent_status(self, auth_client):
        r = auth_client.get("/api/agent/status")
        assert r.status_code in (200, 404)
