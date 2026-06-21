import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

from app import app as _app
from db_connection import obtener_conexion

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

@pytest.fixture
def conn():
    c = obtener_conexion()
    yield c
    c.close()


class TestDbIndexes:
    def test_crear_indices_no_lanza_error(self, conn):
        from db.indexes import crear_indices
        creados, total, errores = crear_indices(conn)
        assert creados > 0
        assert len(errores) == 0

    def test_indices_minimo(self, conn):
        from db.indexes import crear_indices
        _, total, _ = crear_indices(conn)
        assert total >= 35


class TestDbSchema:
    def test_crear_tablas_schema(self, conn):
        from db.schema import crear_tablas_schema
        try:
            crear_tablas_schema(conn)
            ok = True
        except Exception:
            ok = False
        assert ok

    def test_tablas_principales_existen(self, conn):
        from db.schema import crear_tablas_schema
        crear_tablas_schema(conn)
        tablas = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ["usuarios", "productos", "inventario_general", "historial_ventas", "licencias"]:
            assert t in tablas


class TestDbProductsCatalogo:
    def test_obtener_productos_catalogo(self):
        from db.products_catalogo import obtener_productos_catalogo
        prods = obtener_productos_catalogo()
        assert isinstance(prods, list)

    def test_sincronizar_productos_lista_vacia(self):
        from db.products_catalogo import sincronizar_productos_catalogo
        r = sincronizar_productos_catalogo([], "dev-001")
        assert isinstance(r, dict)

    def test_eliminar_producto_inexistente(self):
        from db.products_catalogo import eliminar_producto_inventario_general
        r = eliminar_producto_inventario_general("no-existe-xyz", "dev-001")
        assert isinstance(r, dict)

    def test_consultar_inventario_actual(self):
        from db.products_catalogo import consultar_inventario_actual
        inv = consultar_inventario_actual()
        assert isinstance(inv, list)


class TestDbProductsInventario:
    def test_cargar_stock_masivo_vacio(self):
        from db.products_inventario import cargar_stock_masivo
        r = cargar_stock_masivo("dev-001", [])
        assert isinstance(r, dict)

    def test_obtener_inventario_general(self):
        from db.products_inventario import obtener_inventario_general
        inv = obtener_inventario_general("dev-001")
        assert isinstance(inv, list)

    def test_obtener_historial_entradas(self):
        from db.products_inventario import obtener_historial_entradas
        hist = obtener_historial_entradas("dev-001")
        assert isinstance(hist, list)

    def test_obtener_inventario_diario(self):
        from db.products_inventario import obtener_inventario_diario
        inv = obtener_inventario_diario("usr-003")
        assert isinstance(inv, list)

    def test_limpiar_inventarios_diarios(self):
        from db.products_inventario import limpiar_inventarios_diarios
        r = limpiar_inventarios_diarios("dev-001")
        assert isinstance(r, dict)

    def test_registrar_entrada_sin_datos(self):
        from db.products_inventario import registrar_entrada_producto
        r = registrar_entrada_producto({}, "dev-001")
        assert r.get("ok") == False


class TestDbConfigInventario:
    def test_sincronizar_estado_completo(self):
        from db_config_inventario import sincronizar_estado_completo
        r = sincronizar_estado_completo("dev-001")
        assert isinstance(r, dict)

    def test_limpiar_tablas_completo(self):
        from db_config_inventario import limpiar_tablas_completo
        r = limpiar_tablas_completo("dev-001")
        assert isinstance(r, dict)

    def test_reconstruir_desde_productos(self):
        from db_config_inventario import reconstruir_desde_productos
        r = reconstruir_desde_productos("dev-001", [])
        assert isinstance(r, dict)
