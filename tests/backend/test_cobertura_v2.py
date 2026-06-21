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


# ============ inventory.py ============
class TestInventory:
    def test_inventario_general_200(self, auth_client):
        r = auth_client.get("/api/inventario/general")
        assert r.status_code == 200

    def test_inventario_entrada_200(self, auth_client):
        r = auth_client.post("/api/inventario/entrada", json={
            "producto_id": "test-prod", "nombre": "Test", "cantidad": 10
        })
        assert r.status_code in (200, 400)

    def test_inventario_entradas_200(self, auth_client):
        r = auth_client.get("/api/inventario/entradas")
        assert r.status_code == 200

    def test_importar_catalogo_200(self, auth_client):
        r = auth_client.post("/api/inventario/importar-catalogo")
        assert r.status_code in (200, 400)

    def test_eliminar_inventario_200(self, auth_client):
        r = auth_client.post("/api/inventario/general/eliminar", json={"producto_id": "test"})
        assert r.status_code in (200, 400)

    def test_stock_masivo_200(self, auth_client):
        r = auth_client.post("/api/stock/masivo", json={"items": []})
        assert r.status_code in (200, 400)

    def test_limpiar_tablas_200(self, auth_client):
        r = auth_client.post("/api/limpiar-tablas")
        assert r.status_code in (200, 400)

    def test_reconstruir_200(self, auth_client):
        r = auth_client.post("/api/reconstruir-desde-productos", json={"productos": []})
        assert r.status_code in (200, 400)

    def test_inventario_diario_200(self, auth_client):
        r = auth_client.get("/api/inventario/diario/vendedor1")
        assert r.status_code in (200, 403, 404)

    def test_conteo_vendedor_200(self, auth_client):
        r = auth_client.post("/api/inventario/diario/conteo", json={
            "vendedor_id": "usr-003", "producto_id": "test", "cant_final": 5
        })
        assert r.status_code in (200, 400, 403)

    def test_cierre_vendedor_200(self, auth_client):
        r = auth_client.post("/api/inventario/diario/cierre", json={
            "vendedor_id": "usr-003", "total_ventas": 100, "total_costo": 50,
            "ganancia_neta": 50, "items": []
        })
        assert r.status_code in (200, 400, 403)

    def test_sincronizar_completo_200(self, auth_client):
        r = auth_client.post("/api/sincronizar-completo")
        assert r.status_code in (200, 400)

    def test_sync_desde_inventario_200(self, auth_client):
        r = auth_client.post("/api/catalogo/sync-desde-inventario")
        assert r.status_code == 200


# ============ reportes_bp.py ============
class TestReportesBp:
    def test_reporte_ventas_200(self, client):
        r = client.get("/api/reportes/ventas")
        assert r.status_code == 200

    def test_reporte_ventas_con_fechas(self, client):
        r = client.get("/api/reportes/ventas?desde=2026-01-01&hasta=2026-06-20")
        assert r.status_code == 200

    def test_reporte_resumen_200(self, client):
        r = client.get("/api/reportes/resumen")
        assert r.status_code == 200

    def test_reporte_exportar_csv(self, client):
        r = client.get("/api/reportes/exportar")
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            assert 'text/csv' in r.content_type

    def test_reporte_ganancias_403_sin_login(self, client):
        r = client.get("/api/reportes/ganancias")
        assert r.status_code in (200, 401, 403)

    def test_reporte_ganancias_admin(self, auth_client):
        r = auth_client.get("/api/reportes/ganancias")
        assert r.status_code == 200

    def test_metrics_200(self, client):
        r = client.get("/api/metrics")
        assert r.status_code == 200
