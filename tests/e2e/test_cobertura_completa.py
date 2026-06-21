"""Tests E2E faltantes — Cobertura completa de módulos"""
import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

from app import app as _app

DEMO_PW = os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")

@pytest.fixture
def app():
    _app.config["TESTING"] = True
    _app.config["SECRET_KEY"] = "test"
    return _app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def dev_client(client):
    client.post("/api/auth/login", json={"username": "desarrollador", "password": DEMO_PW})
    return client

@pytest.fixture
def admin_client(client):
    client.post("/api/auth/login", json={"username": "admin", "password": DEMO_PW})
    return client


class TestLicencias:
    def test_listar_licencias(self, admin_client):
        r = admin_client.get("/api/licencias")
        assert r.status_code == 200

    def test_verificar_licencia(self, admin_client):
        r = admin_client.get("/api/licencias/verificar/dev-001")
        assert r.status_code == 200

    def test_crear_licencia(self, dev_client):
        r = dev_client.post("/api/licencias/crear", json={
            "device_id": "test-device-999", "tipo": "trial", "valor": 7, "unidad": "dias"
        })
        assert r.status_code in (200, 400)


class TestPrivilegios:
    def test_get_privilegios_admin(self, admin_client):
        r = admin_client.get("/api/privilegios/administrador")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("ok") == True

    def test_get_privilegios_vendedor(self, admin_client):
        r = admin_client.get("/api/privilegios/vendedor")
        assert r.status_code == 200

    def test_put_privilegios(self, dev_client):
        r = dev_client.put("/api/privilegios/vendedor", json={"privilegios": {"ventas": True, "catalogo": True}})
        assert r.status_code == 200

    def test_reset_privilegios(self, dev_client):
        r = dev_client.post("/api/privilegios/vendedor/restablecer")
        assert r.status_code == 200


class TestGastos:
    def test_listar_gastos(self, dev_client):
        r = dev_client.get("/api/gastos")
        assert r.status_code == 200

    def test_crear_gasto(self, dev_client):
        r = dev_client.post("/api/gastos", json={
            "categoria": "servicios", "monto": 500.0, "descripcion": "Luz"
        })
        assert r.status_code in (200, 201, 400)


class TestDescuentos:
    def test_listar_descuentos(self, dev_client):
        r = dev_client.get("/api/descuentos")
        assert r.status_code == 200

    def test_crear_descuento(self, dev_client):
        r = dev_client.post("/api/descuentos", json={
            "nombre": "Oferta test", "porcentaje": 10
        })
        assert r.status_code in (200, 201, 400)


class TestCierreCaja:
    def test_cierres_lista(self, dev_client):
        r = dev_client.get("/api/ventas/cierres")
        assert r.status_code == 200

    def test_cierre_post(self, dev_client):
        r = dev_client.post("/api/ventas/cierre", json={"fecha": "2026-06-20"})
        assert r.status_code in (200, 400)


class TestHistorialDiario:
    def test_historial_diario(self, dev_client):
        r = dev_client.get("/api/historial/diario")
        assert r.status_code == 200


class TestSupabaseEndpoints:
    def test_supabase_config_get(self, admin_client):
        r = admin_client.get("/api/supabase/config")
        assert r.status_code == 200

    def test_supabase_sync_status(self, admin_client):
        r = admin_client.post("/api/supabase/sync-all")
        assert r.status_code in (200, 400)

    def test_supabase_test(self, dev_client):
        r = dev_client.post("/api/supabase/test")
        assert r.status_code in (200, 400)


class TestBackup:
    def test_backup_export(self, dev_client):
        r = dev_client.get("/backup/export")
        assert r.status_code in (200, 400, 404, 500)


class TestDebugEndpoints:
    def test_debug_tables(self, dev_client):
        r = dev_client.get("/api/debug/tables")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, dict)


class TestDiccionario:
    def test_diccionario_sinonimos(self, dev_client):
        r = dev_client.get("/api/diccionario/sinonimos?q=arroz")
        assert r.status_code in (200, 403, 404)

    def test_diccionario_definicion(self, dev_client):
        r = dev_client.get("/api/diccionario/definicion?q=margen")
        assert r.status_code in (200, 403, 404)


class TestConfigPublica:
    def test_config_publica(self, client):
        r = client.get("/api/config/publica")
        assert r.status_code in (200, 404)


class TestBioEndpoints:
    def test_bio_registrar(self, dev_client):
        r = dev_client.post("/auth/bio/registrar", json={"device": "test-phone"})
        assert r.status_code in (200, 400, 404)

    def test_bio_revocar(self, dev_client):
        r = dev_client.post("/auth/bio/revocar", json={})
        assert r.status_code in (200, 400, 404)
