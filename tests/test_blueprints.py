"""test_blueprints.py — Tests de integración para los blueprints.
Verifica que cada blueprint se registra y sus rutas principales responden.
Actualizado a v8.14 con las rutas correctas."""
import os, sys, pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestHealth:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"


class TestCatalogo:
    def test_catalogo_list(self, client):
        r = client.get("/api/productos")
        assert r.status_code == 200
        d = r.get_json()
        assert "productos" in d

    def test_catalogo_crear(self, client):
        r = client.post("/api/productos/crear", json={"nombre": "TestProd", "precio": 10})
        assert r.status_code == 200
        assert r.get_json()["ok"]

    def test_productos_crear(self, client):
        r = client.post("/api/productos/crear", json={"nombre": "TestProd2", "precio": 20})
        assert r.status_code == 200


class TestVentas:
    def test_registrar_venta(self, client):
        r = client.post("/api/ventas/registrar", json={
            "items": [{"producto_id": "p1", "nombre": "Arroz", "cantidad": 2, "precio": 25.50}],
            "metodo_pago": "efectivo"
        })
        assert r.status_code == 200
        assert r.get_json()["ok"]

    def test_ventas_hoy(self, client):
        r = client.get("/api/ventas/hoy")
        assert r.status_code == 200

    def test_ventas_totales(self, client):
        r = client.get("/api/ventas/totales")
        assert r.status_code in (200, 404)


class TestReportes:
    def test_reporte_resumen(self, client):
        r = client.get("/api/reportes/resumen")
        assert r.status_code == 200

    def test_metrics(self, client):
        r = client.get("/api/metrics")
        assert r.status_code == 200


class TestDiagnostico:
    def test_diag_info(self, client):
        r = client.get("/api/diag/info")
        assert r.status_code == 200

    def test_crashlog(self, client):
        r = client.get("/api/diag/crashlog")
        assert r.status_code == 200

    def test_state_get(self, client):
        r = client.get("/api/state")
        assert r.status_code == 200

    def test_state_post(self, client):
        r = client.post("/api/state", json={"test_key": "test_value"})
        assert r.status_code == 200

    def test_notificaciones(self, client):
        r = client.get("/api/notificaciones")
        assert r.status_code == 200


class TestClientes:
    def test_registrar_cliente(self, client):
        r = client.post("/api/clientes/registrar", json={
            "nombre": "Juan Test",
            "email": "test_blue@test.com",
            "password": "1234",
            "telefono": "123"
        })
        assert r.status_code == 200

    def test_listar_clientes(self, client):
        r = client.get("/api/clientes")
        assert r.status_code == 200


class TestUsuarios:
    def test_listar_usuarios(self, client):
        r = client.get("/api/usuarios")
        assert r.status_code == 200

    def test_privilegios(self, client):
        r = client.get("/api/admin/privilegios")
        assert r.status_code == 200


class TestTools:
    def test_finanzas(self, client):
        r = client.get("/api/tools/finanzas")
        assert r.status_code == 200

    def test_stock(self, client):
        r = client.get("/api/tools/stock")
        assert r.status_code == 200

    def test_inventario_resumen(self, client):
        r = client.get("/api/tools/inventario/resumen")
        assert r.status_code == 200


class TestImport:
    def test_previsualizar(self, client):
        r = client.post("/api/importar/previsualizar", json={"productos": [{"nombre": "X"}]})
        assert r.status_code in (200, 404)

    def test_importar(self, client):
        r = client.post("/api/importar/excel", json={
            "productos": [{"nombre": "ImportTest", "precio": 15, "stock": 10}]
        })
        assert r.status_code in (200, 404)


class TestAgente:
    def test_agent_chat(self, client):
        r = client.post("/api/agent/chat", json={"mensaje": "hola"})
        assert r.status_code == 200
        d = r.get_json()
        assert d["ok"]
        assert len(d["respuesta"]) > 5

    def test_agent_status(self, client):
        r = client.get("/api/agent/status")
        assert r.status_code == 200

    def test_agent_ventas(self, client):
        r = client.post("/api/agent/chat", json={"mensaje": "cuanto vendi hoy"})
        assert r.status_code == 200

    def test_agent_stock(self, client):
        r = client.post("/api/agent/chat", json={"mensaje": "stock bajo"})
        assert r.status_code == 200


class TestAuth:
    def test_login_fail(self, client):
        r = client.post("/api/auth/login", json={"username": "fake", "password": "wrong"})
        assert r.status_code == 401

    def test_login_empty(self, client):
        r = client.post("/api/auth/login", json={})
        assert r.status_code in (400, 401)

    def test_auth_me(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 200

    def test_logout(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 200


class TestSecurityHeaders:
    def test_security_headers(self, client):
        r = client.get("/api/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert r.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_seguridad_check(self, client):
        r = client.get("/api/seguridad/check")
        assert r.status_code == 200
