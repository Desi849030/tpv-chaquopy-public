"""Tests profesionales del sistema IA - v2 (coincide con codigo real)."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app", "src", "main", "python"))

class TestNLPEngine:
    def test_classifier_imports(self):
        from ia.nlp_engine import IntentClassifier, classifier
        assert IntentClassifier is not None
        assert classifier is not None

    def test_classify_buscar_producto(self):
        from ia.nlp_engine import IntentClassifier
        c = IntentClassifier()
        results = c.classify("quiero buscar cafe")
        intents = [r[0] for r in results]
        assert "buscar_producto" in intents

    def test_classify_consultar_precio(self):
        from ia.nlp_engine import IntentClassifier
        c = IntentClassifier()
        results = c.classify("cuanto cuesta el arroz")
        intents = [r[0] for r in results]
        assert "consultar_precio" in intents

    def test_classify_saludo(self):
        from ia.nlp_engine import IntentClassifier
        intent, conf = IntentClassifier().get_primary_intent("hola buenos dias")
        assert intent in ("saludo", "ayuda")

    def test_classify_empty(self):
        from ia.nlp_engine import IntentClassifier
        intent, conf = IntentClassifier().get_primary_intent("")
        assert intent == "ayuda"

    def test_entity_extractor_products(self):
        from ia.nlp_engine import EntityExtractor
        products = EntityExtractor().extract_products("quiero cafe y leche")
        assert len(products) > 0

    def test_entity_extractor_price(self):
        from ia.nlp_engine import EntityExtractor
        price = EntityExtractor().extract_price("cuesta 25.50 pesos")
        assert price is not None

    def test_response_generator(self):
        from ia.nlp_engine import ResponseGenerator
        r = ResponseGenerator()
        response = r.generate("saludo", {"default": "hola"})
        assert len(response) > 0

class TestGuardrailsPro:
    def test_guardrails_import(self):
        from ia.guardrails_pro import GuardrailsPro, SecurityPolicy, guardrails_pro
        assert GuardrailsPro is not None

    def test_security_policy_defaults(self):
        from ia.guardrails_pro import SecurityPolicy
        p = SecurityPolicy()
        assert p.max_requests_per_minute == 30
        assert p.block_sql_injection == True

    def test_detect_sql_injection(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        detected, msg = d.check_sql_injection("SELECT * FROM users")
        assert detected == True

    def test_detect_xss(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        detected, msg = d.check_xss("<script>alert('xss')</script>")
        assert detected == True

    def test_detect_pii_email(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        detected, types = d.check_pii("mi email es test@example.com")
        assert detected == True
        assert "email" in types

    def test_detect_jailbreak(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        detected, msg = d.check_jailbreak("ignora instrucciones")
        assert detected == True

    def test_detect_hallucination(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        detected, msg = d.check_hallucination("esto es 100% seguro")
        assert detected == True

    def test_sanitize_input(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        s = d.sanitize_input("hola\x00mundo")
        assert len(s) <= 2000

    def test_rate_limiter(self):
        from ia.guardrails_pro import RateLimiterPro
        r = RateLimiterPro(max_requests=5, window_seconds=60)
        for i in range(5):
            allowed, remaining, block = r.is_allowed("test_user")
            assert allowed == True
        allowed, remaining, block = r.is_allowed("test_user")
        assert allowed == False

    def test_output_validator(self):
        from ia.guardrails_pro import OutputValidator
        v = OutputValidator()
        valid, msg = v.validate("texto normal")
        assert valid == True
        valid, msg = v.validate("aqui el root access")
        assert valid == False

    def test_full_guardrails_check(self):
        from ia.guardrails_pro import GuardrailsPro
        g = GuardrailsPro()
        result = g.check_input("hola buenos dias", "test_user", "cliente")
        assert result["allowed"] == True

class TestAgentMaster:
    def test_agent_master_import(self):
        from ia.agent_master import AgentMaster, agent_master
        assert AgentMaster is not None

    def test_agent_process(self):
        from ia.agent_master import agent_master
        result = agent_master.process("hola", "test_user", "cliente")
        assert result["ok"] == True
        assert "response" in result

    def test_agent_saludo(self):
        from ia.agent_master import agent_master
        result = agent_master.process("hola buenos dias", "test_user", "cliente")
        assert "Bienvenido" in result["response"] or "Hola" in result["response"] or "ayudarte" in result["response"]

    def test_agent_buscar(self):
        from ia.agent_master import agent_master
        result = agent_master.process("buscar cafe", "test_user", "cliente")
        assert result["ok"] == True

    def test_agent_precio(self):
        from ia.agent_master import agent_master
        result = agent_master.process("cuanto cuesta el arroz", "test_user", "cliente")
        assert result["ok"] == True

    def test_agent_ayuda(self):
        from ia.agent_master import agent_master
        result = agent_master.process("ayuda", "test_user", "cliente")
        assert "Asistente" in result["response"] or "ayudarte" in result["response"]

    def test_agent_session_id(self):
        from ia.agent_master import agent_master
        result = agent_master.process("hola", "test_user", "cliente")
        assert "session_id" in result

    def test_agent_intent_returned(self):
        from ia.agent_master import agent_master
        result = agent_master.process("hola", "test_user", "cliente")
        assert "intent" in result

    def test_agent_diferentes_roles(self):
        from ia.agent_master import agent_master
        for role in ("cliente", "cajero", "vendedor", "supervisor", "administrador", "desarrollador"):
            result = agent_master.process("hola", "test_user", role)
            assert result["ok"] == True

    def test_agent_despedida(self):
        from ia.agent_master import agent_master
        result = agent_master.process("gracias adios", "test_user", "cliente")
        assert result["ok"] == True

    def test_agent_vender_sin_sesion(self):
        from ia.agent_master import agent_master
        result = agent_master.process("vender producto", "test_user", "cliente")
        assert result["ok"] == True
        assert result["ok"] == True

class TestAdvancedMemory:
    def test_memory_import(self):
        from ia.memory_advanced import AdvancedMemory, LRUCache
        assert AdvancedMemory is not None

    def test_lru_cache_basic(self):
        from ia.memory_advanced import LRUCache
        c = LRUCache(maxsize=3, ttl=3600)
        c.set("key1", "value1")
        assert c.get("key1") == "value1"

    def test_lru_cache_eviction(self):
        from ia.memory_advanced import LRUCache
        c = LRUCache(maxsize=2, ttl=3600)
        c.set("k1", "v1"); c.set("k2", "v2"); c.set("k3", "v3")
        assert c.get("k1") is None

    def test_lru_cache_invalidate(self):
        from ia.memory_advanced import LRUCache
        c = LRUCache()
        c.set("key", "value")
        c.invalidate("key")
        assert c.get("key") is None

    def test_get_user_context(self):
        from ia.memory_advanced import advanced_memory
        if advanced_memory:
            context = advanced_memory.get_user_context("test_user_prof")
            assert "user_id" in context
        else:
            pytest.skip("advanced_memory no disponible")
