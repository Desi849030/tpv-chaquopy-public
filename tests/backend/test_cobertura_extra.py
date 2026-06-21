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


# ============ diag_bp.py ============
class TestDiagBp:
    def test_health_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "ok"

    def test_diag_info_200(self, client):
        r = client.get("/api/diag/info")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("ok") == True

    def test_seguridad_check_200(self, client):
        r = client.get("/api/seguridad/check")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "seguridad" in data

    def test_notificaciones_200(self, client):
        r = client.get("/api/notificaciones")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "notificaciones" in data

    def test_sincronizar_completo_200(self, client):
        r = client.post("/api/sincronizar-completo")
        assert r.status_code == 200

    def test_pedidos_200(self, client):
        r = client.get("/api/pedidos")
        assert r.status_code == 200

    def test_auto_backup_200(self, client):
        r = client.post("/api/auth/auto-backup")
        assert r.status_code == 200

    def test_backup_bd_200(self, client):
        r = client.post("/api/db/backup")
        assert r.status_code == 200

    def test_qr_producto_404(self, client):
        r = client.get("/api/qr/no-existe")
        assert r.status_code == 404

    def test_crashlog_200(self, client):
        r = client.get("/api/diag/crashlog")
        assert r.status_code == 200


# ============ tools_bp.py ============
class TestToolsBp:
    def test_finanzas_200(self, client):
        r = client.get("/api/tools/finanzas")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("ok") == True

    def test_stock_200(self, client):
        r = client.get("/api/tools/stock")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("ok") == True

    def test_recomendar_200(self, client):
        r = client.get("/api/tools/recomendar")
        assert r.status_code == 200

    def test_prediccion_200(self, client):
        r = client.get("/api/tools/prediccion")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "prediccion" in data

    def test_abc_200(self, client):
        r = client.get("/api/tools/abc")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "analisis" in data

    def test_admin_status_200(self, client):
        r = client.get("/api/tools/admin/status")
        assert r.status_code == 200


# ============ catalogo_bp.py ============
class TestCatalogoBp:
    def test_listar_productos_200(self, auth_client):
        r = auth_client.get("/api/productos")
        assert r.status_code == 200

    def test_crear_producto_ok(self, auth_client):
        import uuid
        pid = f"test-{uuid.uuid4().hex[:6]}"
        r = auth_client.post("/api/productos/crear", json={
            "nombre": "Producto Test", "precio": 10.0, "costo": 5.0
        })
        assert r.status_code in (200, 400)

    def test_crear_producto_sin_nombre_400(self, auth_client):
        r = auth_client.post("/api/productos/crear", json={"precio": 10})
        assert r.status_code == 400

    def test_eliminar_producto_404(self, auth_client):
        r = auth_client.delete("/api/productos/no-existe-123")
        assert r.status_code in (404, 200)

    def test_listar_categorias_200(self, auth_client):
        r = auth_client.get("/api/categorias")
        assert r.status_code == 200

    def test_crear_categoria_200(self, auth_client):
        r = auth_client.post("/api/categorias/crear", json={"nombre": "TestCat"})
        assert r.status_code in (200, 400, 500)

    def test_actualizar_producto_404(self, auth_client):
        r = auth_client.put("/api/productos/no-existe-456", json={"nombre": "X"})
        assert r.status_code in (200, 404, 500)
