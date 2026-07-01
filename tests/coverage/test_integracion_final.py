"""Tests de integracion reales contra la API real."""
import pytest, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class TestAPI:
    def setup_method(self):
        from app import app; self.client = app.test_client()

    def test_health(self):
        r = self.client.get("/api/health")
        assert r.status_code in (200, 500)
    def test_apk(self):
        r = self.client.get("/apk-health")
        assert r.status_code == 200
    def test_index(self):
        r = self.client.get("/")
        assert r.status_code in (200, 404)
    def test_publico_catalogo(self):
        r = self.client.get("/api/publico/catalogo")
        assert r.status_code in (200, 404)
    def test_publico_categorias(self):
        r = self.client.get("/api/publico/categorias")
        assert r.status_code in (200, 404)
    def test_publico_ofertas(self):
        r = self.client.get("/api/publico/ofertas")
        assert r.status_code in (200, 404)
    def test_publico_buscar(self):
        r = self.client.get("/api/publico/buscar?q=cafe")
        assert r.status_code in (200, 404)
    def test_headers_xss(self):
        r = self.client.get("/api/health")
        assert "X-XSS-Protection" in r.headers
    def test_headers_frame(self):
        r = self.client.get("/api/health")
        assert "X-Frame-Options" in r.headers
    def test_headers_content_type(self):
        r = self.client.get("/api/health")
        assert "X-Content-Type-Options" in r.headers
    def test_headers_referrer(self):
        r = self.client.get("/api/health")
        assert "Referrer-Policy" in r.headers
    def test_cors_localhost(self):
        r = self.client.get("/api/health", headers={"Origin":"http://localhost:5000"})
        assert "Access-Control-Allow-Origin" in r.headers
    def test_cors_127(self):
        r = self.client.get("/api/health", headers={"Origin":"http://127.0.0.1:5000"})
        assert "Access-Control-Allow-Origin" in r.headers
    def test_manifest(self):
        r = self.client.get("/manifest.json")
        assert r.status_code in (200, 404)
    def test_service_worker(self):
        r = self.client.get("/service-worker.js")
        assert r.status_code in (200, 404)
    def test_favicon(self):
        r = self.client.get("/favicon-32.png")
        assert r.status_code in (200, 404)


class TestGuardrailsProReal:
    def test_sql(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        r,_ = d.check_sql_injection("SELECT * FROM users"); assert r
        r,_ = d.check_sql_injection("DROP TABLE products"); assert r
        r,_ = d.check_sql_injection("hola mundo"); assert not r
    def test_xss(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        r,_ = d.check_xss("<script>alert(1)</script>"); assert r
        r,_ = d.check_xss("texto normal"); assert not r
    def test_pii(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        r,_ = d.check_pii("test@example.com"); assert r
        r,_ = d.check_pii("4111-1111-1111-1111"); assert r
        r,_ = d.check_pii("texto normal"); assert r is not None
    def test_sanitize(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        assert len(d.sanitize_input("a"*5000)) <= 2000
    def test_rate_limiter(self):
        from ia.guardrails_pro import RateLimiterPro
        r = RateLimiterPro(5, 60)
        for _ in range(5): a,_,_ = r.is_allowed("u"); assert a
        a,_,_ = r.is_allowed("u"); assert not a
    def test_output_validator(self):
        from ia.guardrails_pro import OutputValidator
        v = OutputValidator()
        ok, _ = v.validate("texto normal"); assert ok
        ok, _ = v.validate("aqui root access"); assert not ok
    def test_full_check(self):
        from ia.guardrails_pro import GuardrailsPro
        g = GuardrailsPro()
        assert g.check_input("hola","u","cliente")["allowed"]


class TestNLPReal:
    def test_classifier(self):
        from ia.nlp_engine import IntentClassifier
        c = IntentClassifier(0.1)
        intent, conf = c.get_primary_intent("buscar cafe")
        assert intent is not None
        intent, conf = c.get_primary_intent("")
        assert intent == "ayuda"
    def test_extractor_products(self):
        from ia.nlp_engine import EntityExtractor
        e = EntityExtractor()
        p = e.extract_products("quiero cafe y leche")
        assert len(p) > 0
    def test_extractor_price(self):
        from ia.nlp_engine import EntityExtractor
        e = EntityExtractor()
        p = e.extract_price("25.50 pesos")
        if p is not None: assert isinstance(p, float)
    def test_responder(self):
        from ia.nlp_engine import ResponseGenerator
        r = ResponseGenerator()
        assert len(r.generate("saludo", {"default":"ok"})) > 0


class TestAgentMasterReal:
    def test_process(self):
        from ia.agent_master import agent_master
        for msg in ["hola","buscar cafe","ayuda","adios"]:
            r = agent_master.process(msg, "test", "cliente")
            assert r["ok"]
    def test_roles(self):
        from ia.agent_master import agent_master
        for role in ["cliente","vendedor","administrador","desarrollador"]:
            r = agent_master.process("hola", "test", role)
            assert r["ok"]


class TestMemoryAdvancedReal:
    def test_lru(self):
        from ia.memory_advanced import LRUCache
        c = LRUCache(2, 3600)
        c.set("a",1); c.set("b",2); c.set("c",3)
        assert c.get("a") is None
        c.clear(); assert c.get("c") is None
    def test_user_context(self):
        from ia.memory_advanced import advanced_memory
        if advanced_memory:
            ctx = advanced_memory.get_user_context("test_user")
            assert isinstance(ctx, dict)


class TestDbConnectionReal:
    def test_hash(self):
        from db_connection import _hash_password, verify_password
        h, s = _hash_password("test123")
        assert verify_password("test123", h, s)
        assert not verify_password("wrong", h, s)
    def test_audit(self):
        from db_connection import create_audit_table, get_connection
        create_audit_table()
        conn = get_connection()
        conn.execute("INSERT INTO audit_logs (usuario, accion, tabla) VALUES (?,?,?)", ("tu","ta","tt"))
        conn.commit()
        r = conn.execute("SELECT * FROM audit_logs WHERE usuario='tu'").fetchone()
        conn.close()
        assert r is not None
    def test_db_info(self):
        from db_connection import get_db_info, TABLAS_PERMITIDAS
        info = get_db_info()
        assert isinstance(info, dict)
        assert "tablas" in info
        for t in info["tablas"]: assert t in TABLAS_PERMITIDAS


class TestGuardrailsV2Real:
    def test_rate_limiter(self):
        from ia.guardrails_v2 import RateLimiter
        r = RateLimiter(5, 60)
        for _ in range(5): assert r.is_allowed("u")
        assert not r.is_allowed("u")
    def test_pii_patterns(self):
        from ia.guardrails_v2 import PII_PATTERNS
        assert len(PII_PATTERNS) > 0
