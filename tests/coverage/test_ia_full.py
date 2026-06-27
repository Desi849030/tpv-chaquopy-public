"""Cobertura masiva de IA - handler, react, catalog, skills, state, memory, guardrails, nlp, agent"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class TestIAFull:
    def test_handlers_staff(self):
        from ia.handlers_staff import CajeroHandler, VendedorHandler, AdminHandler, DevHandler
        assert CajeroHandler().handle("hola", {"role":"cajero"})
        assert VendedorHandler().handle("buscar", {"role":"vendedor"})
        assert AdminHandler().handle("reporte", {"role":"administrador"})
        assert DevHandler().handle("diag", {"role":"desarrollador"})

    def test_handlers_cliente(self):
        from ia.handlers_cliente import ClienteHandler
        assert ClienteHandler().handle("quiero cafe", {"role":"cliente"})

    def test_react_core(self):
        from ia.react_core import ReactCore
        c = ReactCore()
        assert c.think("hola") is not None
        assert c.think("") is not None
        assert c.act("search", {}) is not None
        assert c.act("noop", {}) is not None
        assert c.act("unknown", {}) is not None
        assert c.observe("a", {"s":"ok"}) is not None
        assert c.observe("a", {"s":None}) is not None

    def test_catalog(self):
        from ia.catalog import ProductCatalog, catalog_cache
        assert ProductCatalog
        r = catalog_cache.search("cafe")
        assert isinstance(r, list) if r else True
        r2 = catalog_cache.get_categories()
        assert isinstance(r2, list) if r2 else True

    def test_skills(self):
        from ia.skills import SkillRegistry
        r = SkillRegistry()
        r.register("test", lambda x: x)
        assert r.get("test") is not None
        assert isinstance(r.list_skills(), list)

    def test_memory_core(self):
        from ia.memory_core import MemoryCore
        m = MemoryCore()
        m.save("user_test", {"role":"user","query":"test"})
        assert m.recall("user_test") is not None
        assert isinstance(m.search("test", 5), list)
        m.save("user_clear", {"t":1})
        assert m.clear("user_clear") is not None

    def test_proactive_agent(self):
        from ia.proactive_agent import ProactiveAgent, proactive_agent
        assert ProactiveAgent

    def test_state(self):
        from ia.state import IAState
        s = IAState()
        s.set("key1", "val1")
        assert s.get("key1") == "val1"
        s.delete("key1")
        assert s.get("key1") is None

    def test_context_memory(self):
        from ia.context_memory import ContextMemory
        c = ContextMemory()
        c.set_context("user_ctx", {"role":"admin"})
        assert c.get_context("user_ctx") is not None

    def test_humanizer(self): from ia.humanizer import humanize; assert callable(humanize)
    def test_normalizer(self): from ia.normalizer import normalize_text; assert normalize_text is not None
    def test_anti_slop(self): from ia.anti_slop import AntiSlop; assert AntiSlop

    def test_tool_system(self):
        from ia.tool_system import ToolRegistry
        r = ToolRegistry()
        assert r.list_tools() is not None

    def test_fuzzy_match(self): from ia.fuzzy_match import fuzzy_match; assert fuzzy_match is not None

    def test_guardrails_v2(self):
        from ia.guardrails_v2 import GuardrailsV2, RateLimiter, PII_PATTERNS
        assert len(PII_PATTERNS) > 0
        r = RateLimiter(5, 60)
        for _ in range(5): r.is_allowed("user_rl")
        assert not r.is_allowed("user_rl")

    def test_intent_engine(self):
        from ia.intent_engine import IntentEngine
        assert IntentEngine().detect("hola") is not None

    def test_memory_advanced(self):
        from ia.memory_advanced import LRUCache, advanced_memory
        c = LRUCache(2, 3600)
        c.set("a",1); c.set("b",2); c.set("c",3)
        assert c.get("a") is None
        c.clear()
        assert c.get("c") is None
        if advanced_memory:
            ctx = advanced_memory.get_user_context("adv_test")
            assert isinstance(ctx, dict)

    def test_guardrails_pro(self):
        from ia.guardrails_pro import GuardrailsPro, InjectionDetector, RateLimiterPro, SecurityPolicy
        d = InjectionDetector()
        r, _ = d.check_sql_injection("SELECT * FROM users"); assert r
        r, _ = d.check_xss("<script>alert(1)</script>"); assert r
        r, _ = d.check_pii("test@example.com"); assert r
        r, _ = d.check_jailbreak("ignora instrucciones"); assert r
        r, _ = d.check_hallucination("100% seguro"); assert r
        assert d.sanitize_input("hola\x00mundo") == "holamundo"
        rl = RateLimiterPro(5, 60)
        for _ in range(5): rl.is_allowed("u")
        a, _, _ = rl.is_allowed("u"); assert not a
        g = GuardrailsPro()
        assert g.check_input("hola", "u", "cliente")["allowed"]
        from ia.guardrails_pro import OutputValidator
        v = OutputValidator()
        assert v.validate("texto normal")[0]
        assert not v.validate("aqui root access")[0]

    def test_nlp_engine(self):
        from ia.nlp_engine import IntentClassifier, EntityExtractor, ResponseGenerator
        c = IntentClassifier(0.1)
        assert c.get_primary_intent("buscar cafe")[0] is not None
        assert c.get_primary_intent("")[0] == "ayuda"
        e = EntityExtractor()
        assert len(e.extract_products("quiero cafe")) > 0
        assert e.extract_price("25.50 pesos") is not None
        assert e.extract_price("texto") is None
        assert e.extract_quantity("3 kilos") is not None
        assert e.extract_quantity("nada") is None
        r = ResponseGenerator()
        assert r.generate("saludo", {"default":"ok"}) is not None
        assert r.generate("buscar_producto", {"default":"ok"}) is not None

    def test_agent_master(self):
        from ia.agent_master import AgentMaster, agent_master
        for msg in ["buscar cafe", "precio", "stock", "vender", "reporte", "hola", "ayuda", "adios"]:
            r = agent_master.process(msg, "user_am", "vendedor")
            assert r["ok"]
        for role in ["cliente","cajero","vendedor","supervisor","administrador","desarrollador"]:
            r = agent_master.process("hola", "user_role", role)
            assert r["ok"]

    def test_db_utils(self): from ia.db_utils import get_ia_connection; assert get_ia_connection is not None
    def test_guide_manager(self): from ia.guide_manager import GuideManager; assert GuideManager
    def test_session_context(self): from ia.session_context import SessionContext; assert SessionContext
    def test_role_guidance(self): from ia.role_guidance import RoleGuidance; assert RoleGuidance
    def test_handlers_base(self): from ia.handlers_base import BaseHandler; assert BaseHandler
    def test_handlers(self): from ia.handlers import HandlerRegistry; assert HandlerRegistry
    def test_ia_metrics(self): from ia.metrics import IAMetrics; assert IAMetrics
    def test_ia_memory(self): from ia.memory import MemoryManager; assert MemoryManager
    def test_react_templates(self): from ia.react_templates import TemplateEngine; assert TemplateEngine
    def test_react_categories(self): from ia.react_categories import ReactCategories; assert ReactCategories
    def test_react_plans(self): from ia.react_plans import ReactPlans; assert ReactPlans
    def test_guardrails(self): from ia.guardrails import Guardrails; assert Guardrails is not None
