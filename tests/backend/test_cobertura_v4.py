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


# ============ security_het.py ============
class TestSecurityHet:
    def test_check_rate_limit_testing(self):
        from security_het import check_rate_limit
        ok, remaining = check_rate_limit()
        assert ok == True

    def test_detect_sql_injection_limpio(self):
        from security_het import detect_sql_injection
        ok, status = detect_sql_injection("texto normal")
        assert ok == True

    def test_detect_sql_injection_sospechoso(self):
        from security_het import detect_sql_injection
        ok, status = detect_sql_injection("1 UNION SELECT * FROM users")
        assert ok == False

    def test_detect_xss_limpio(self):
        from security_het import detect_xss
        ok, status = detect_xss("texto normal")
        assert ok == True

    def test_detect_xss_sospechoso(self):
        from security_het import detect_xss
        ok, status = detect_xss("<script>alert('xss')</script>")
        assert ok == False

    def test_record_login_result_success(self):
        from security_het import record_login_result
        try:
            record_login_result("192.168.1.1", True)
            ok = True
        except Exception:
            ok = False
        assert ok

    def test_check_login_testing(self):
        from security_het import check_login
        ok, remaining = check_login("127.0.0.1")
        assert ok == True


# ============ security_pci.py ============
class TestSecurityPci:
    def test_tokenize_pan_valido(self):
        from security_pci import tokenize_pan
        token = tokenize_pan("4111111111111111")
        assert token is not None
        assert len(token) == 64

    def test_tokenize_pan_vacio(self):
        from security_pci import tokenize_pan
        assert tokenize_pan("") is None

    def test_mask_pan(self):
        from security_pci import mask_pan
        masked = mask_pan("4111111111111111")
        assert "1111" in masked  # últimos 4 dígitos
        assert "*" in masked

    def test_validate_luhn_valida(self):
        from security_pci import validate_luhn
        assert validate_luhn("4111111111111111") == True

    def test_validate_luhn_invalida(self):
        from security_pci import validate_luhn
        assert validate_luhn("1234567890123456") == False


# ============ modules/agent.py ============
class TestModulesAgent:
    def test_agent_query_sin_palabra_clave(self, auth_client):
        r = auth_client.post("/api/agent/query", json={"query": "xyz no existe"})
        assert r.status_code == 200

    def test_agent_query_ventas(self, auth_client):
        r = auth_client.post("/api/agent/query", json={"query": "ventas hoy"})
        assert r.status_code == 200

    def test_agent_query_inventario(self, auth_client):
        r = auth_client.post("/api/agent/query", json={"query": "inventario"})
        assert r.status_code == 200


# ============ modules/debug_sync_bp.py ============
class TestDebugSyncBp:
    def test_debug_tables_admin(self, auth_client):
        r = auth_client.get("/api/debug/tables")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_debug_tables_sin_login(self, client):
        r = client.get("/api/debug/tables")
        assert r.status_code == 401
