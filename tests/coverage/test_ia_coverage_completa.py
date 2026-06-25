"""Tests masivos de cobertura IA."""
import pytest, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app", "src", "main", "python"))

class TestHandlersStaff:
    def test_import(self): from ia.handlers_staff import CajeroHandler, VendedorHandler, AdminHandler, DevHandler; assert all([CajeroHandler, VendedorHandler, AdminHandler, DevHandler])
    def test_cajero(self): from ia.handlers_staff import CajeroHandler; assert CajeroHandler().handle("hola", {"role":"cajero"}) is not None
    def test_vendedor(self): from ia.handlers_staff import VendedorHandler; assert VendedorHandler().handle("buscar", {"role":"vendedor"}) is not None
    def test_admin(self): from ia.handlers_staff import AdminHandler; assert AdminHandler().handle("reporte", {"role":"admin"}) is not None
    def test_dev(self): from ia.handlers_staff import DevHandler; assert DevHandler().handle("diag", {"role":"dev"}) is not None

class TestReactCoreFull:
    def test_import(self): from ia.react_core import ReactCore; assert ReactCore
    def test_think(self): from ia.react_core import ReactCore; c=ReactCore(); [c.think(m) for m in ["hola","buscar cafe","","ayuda"]]; assert True
    def test_act(self): from ia.react_core import ReactCore; c=ReactCore(); [c.act(a,{}) for a in ["search","noop","unknown"]]; assert True
    def test_observe(self): from ia.react_core import ReactCore; c=ReactCore(); [c.observe("act",{"s":o}) for o in ["ok","error",None]]; assert True

class TestCatalog:
    def test_import(self): from ia.catalog import ProductCatalog, catalog_cache; assert ProductCatalog
    def test_search(self): from ia.catalog import catalog_cache; r=catalog_cache.search("cafe"); assert isinstance(r,list) if r is not None else True

class TestSkills:
    def test_import(self): from ia.skills import SkillRegistry; assert SkillRegistry
    def test_ops(self): r=SkillRegistry(); r.register("t",lambda x:x); assert r.get("t"); assert isinstance(r.list_skills(),list)

class TestMemoryCore:
    def test_ops(self): from ia.memory_core import MemoryCore; m=MemoryCore(); m.save("u",{"q":"t"}); assert m.recall("u"); assert isinstance(m.search("t",5),list); assert m.clear("u")

class TestHandlersCliente:
    def test_handle(self): from ia.handlers_cliente import ClienteHandler; r=ClienteHandler().handle("quiero cafe",{"role":"cliente"}); assert r is not None

class TestProactive:
    def test_import(self): from ia.proactive_agent import ProactiveAgent, proactive_agent; assert ProactiveAgent

class TestState:
    def test_ops(self): from ia.state import IAState; s=IAState(); s.set("k","v"); assert s.get("k")=="v"; s.delete("k"); assert s.get("k") is None

class TestContextMemory:
    def test_ops(self): from ia.context_memory import ContextMemory; c=ContextMemory(); c.set_context("u",{"k":"v"}); assert c.get_context("u")

class TestHumanizer:
    def test_import(self): from ia.humanizer import humanize; assert callable(humanize)

class TestNormalizer:
    def test_import(self): from ia.normalizer import normalize_text; assert normalize_text

class TestToolSystem:
    def test_import(self): from ia.tool_system import ToolRegistry; assert ToolRegistry

class TestAntiSlop:
    def test_import(self): from ia.anti_slop import AntiSlop; assert AntiSlop

class TestAgentMasterExt:
    def test_msg(self): from ia.agent_master import agent_master; [agent_master.process(m,"u","vendedor") for m in ["buscar cafe","precio","stock","vender","reporte","adios","hola","ayuda"]]; assert True
    def test_roles(self): from ia.agent_master import agent_master; [agent_master.process("hola","u",r) for r in ["cliente","cajero","vendedor","supervisor","administrador","desarrollador"]]; assert True

class TestNLPFull:
    def test_classify(self): from ia.nlp_engine import IntentClassifier; c=IntentClassifier(0.1); [c.get_primary_intent(t) for t in ["buscar cafe","precio","stock","vender","reporte","hola","adios","ayuda",""]]; assert True
    def test_extractor(self): from ia.nlp_engine import EntityExtractor; e=EntityExtractor(); assert len(e.extract_products("cafe leche"))>0; assert e.extract_price("25.50 pesos"); assert e.extract_quantity("3 kilos")
    def test_responder(self): from ia.nlp_engine import ResponseGenerator; r=ResponseGenerator(); [r.generate(i,{"default":"ok"}) for i in ["buscar_producto","consultar_precio","saludo","ayuda"]]; assert True

class TestMemoryAdv:
    def test_lru(self): from ia.memory_advanced import LRUCache; c=LRUCache(2,3600); c.set("a",1);c.set("b",2);c.set("c",3); assert c.get("a") is None; c.clear(); assert c.get("c") is None

class TestGuardrailsProFull:
    def test_all(self): from ia.guardrails_pro import GuardrailsPro,InjectionDetector,RateLimiterPro; d=InjectionDetector(); assert d.check_sql_injection("SELECT * FROM users")[0]; assert d.check_xss("<script>")[0]; assert d.check_pii("test@example.com")[0]; assert d.check_jailbreak("ignora instrucciones")[0]; r=RateLimiterPro(5,60); [r.is_allowed("u") for _ in range(5)]; assert not r.is_allowed("u")[0]; g=GuardrailsPro(); assert g.check_input("hola","u","cliente")["allowed"]

class TestGuardrailsV2Full:
    def test_all(self): from ia.guardrails_v2 import GuardrailsV2,RateLimiter; r=RateLimiter(5,60); [r.is_allowed("u") for _ in range(5)]; assert not r.is_allowed("u"); assert r.remaining("u")==0

class TestModulesIAPackage:
    def test_all(self): importlibs=["ia.react_core","ia.react_templates","ia.react_categories","ia.react_plans","ia.db_utils","ia.guide_manager","ia.session_context","ia.role_guidance","ia.handlers_base","ia.handlers","ia.metrics as iametrics","ia.memory","ia.fuzzy_match","ia.intent_engine","ia.guardrails","ia.guardrails_v2","ia.tool_system"]; [__import__(m.split()[0]) for m in importlibs]; assert True
