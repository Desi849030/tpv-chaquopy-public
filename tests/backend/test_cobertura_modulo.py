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

class TestTiendaHelpers:
    def test_get_db_connection_valida(self):
        from modules.tienda_helpers import get_db_connection
        conn = get_db_connection()
        assert conn is not None
        conn.close()

    def test_crear_tablas_ok(self):
        from modules.tienda_helpers import crear_tablas_tienda
        crear_tablas_tienda()

    def test_tablas_existen(self):
        from modules.tienda_helpers import get_db_connection, crear_tablas_tienda
        crear_tablas_tienda()
        conn = get_db_connection()
        tablas = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ["clientes_tienda", "tiendas", "pedidos_tienda", "items_pedido"]:
            assert t in tablas
        conn.close()

class TestVentasReportes:
    def test_reporte_ventas_200(self, auth_client):
        r = auth_client.get("/api/reportes/ventas")
        assert r.status_code == 200

    def test_reporte_resumen_200(self, auth_client):
        r = auth_client.get("/api/reportes/resumen")
        assert r.status_code == 200

class TestAdminPrivilegios:
    def test_get_privilegios_200(self, auth_client):
        r = auth_client.get("/api/privilegios/administrador")
        assert r.status_code == 200

    def test_put_privilegios_ok(self, auth_client):
        r = auth_client.put("/api/privilegios/vendedor", json={"privilegios": {"ventas": True}})
        assert r.status_code == 200

    def test_reset_privilegios_ok(self, auth_client):
        r = auth_client.post("/api/privilegios/vendedor/restablecer")
        assert r.status_code == 200

    def test_sin_login_401(self, client):
        r = client.get("/api/privilegios/administrador")
        assert r.status_code == 401
