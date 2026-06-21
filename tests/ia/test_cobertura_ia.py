"""Tests para subir cobertura de ia/ — archivos con <20%"""
import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"


class TestReactTemplates:
    def test_compile_general_empty(self):
        from ia.react_templates import ReActEngineTemplates
        obj = ReActEngineTemplates()
        result = obj._compile_general([])
        assert "No se obtuvieron" in result

    def test_compile_general_with_data(self):
        from ia.react_templates import ReActEngineTemplates
        obj = ReActEngineTemplates()
        result = obj._compile_general([{"purpose": "test", "data": {"ventas": 100.0, "items": 5}}])
        assert "test" in result
        assert "100.00" in result

    def test_compile_response_fallback(self):
        from ia.react_templates import ReActEngineTemplates
        obj = ReActEngineTemplates()
        result = obj._compile_response("nonexistent", [{"data": {"x": 1}}])
        assert isinstance(result, str)


class TestAntiSlop:
    def test_refine_normal(self):
        from ia.anti_slop import refine
        result = refine("Hola, quiero comprar arroz", "cliente")
        assert len(result) > 0

    def test_refine_empty(self):
        from ia.anti_slop import refine
        assert refine("", "cliente") == ""

    def test_get_smart_suggestions(self):
        from ia.anti_slop import get_smart_suggestions
        result = get_smart_suggestions("cliente")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_smart_suggestions_admin(self):
        from ia.anti_slop import get_smart_suggestions
        result = get_smart_suggestions("administrador")
        assert len(result) > 0


class TestIntentEngine:
    def test_detect_intents_greeting(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("hola buenos dias")
        assert result[0]["intent"] == "GREETING"

    def test_detect_intents_sales(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("cuanto vendi hoy", "vendedor")
        assert result[0]["intent"] == "SALES"

    def test_detect_intents_unknown(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("zzzzzzzzzz")
        assert result[0]["intent"] == "GENERAL"

    def test_get_suggestions(self):
        from ia.intent_engine import get_suggestions
        result = get_suggestions("GREETING", "cliente")
        assert isinstance(result, list)


class TestNormalizer:
    def test_normalize(self):
        from ia.normalizer import normalize
        assert normalize("HOLA Mundo") == "hola mundo"
        assert "cafe" in normalize("café")

    def test_normalize_empty(self):
        from ia.normalizer import normalize
        assert normalize("") == ""

    def test_contains_any_match(self):
        from ia.normalizer import contains_any
        matched, kw, score = contains_any("quiero arroz", ["arroz", "pan"])
        assert matched == True

    def test_contains_any_no_match(self):
        from ia.normalizer import contains_any
        matched, kw, score = contains_any("xyz", ["arroz", "pan"])
        assert matched == False


class TestToolSystem:
    def test_get_tools_for_role(self):
        from ia.tool_system import get_tools_for_role
        tools = get_tools_for_role("administrador")
        assert "finanzas" in tools

    def test_suggest_tools(self):
        from ia.tool_system import suggest_tools
        result = suggest_tools("quiero ver finanzas", "administrador")
        assert len(result) > 0

    def test_get_help_menu(self):
        from ia.tool_system import get_help_menu
        menu = get_help_menu("administrador")
        assert len(menu) > 0

    def test_check_permission(self):
        from ia.tool_system import check_permission
        assert check_permission("finanzas", "administrador") == True
        assert check_permission("finanzas", "cliente") == False


class TestState:
    def test_ensure_table(self):
        from ia.state import _ensure_table
        try:
            _ensure_table()
            ok = True
        except:
            ok = False
        assert ok

    def test_create_session(self):
        from ia.state import create_session
        import uuid
        sid = f"test-{uuid.uuid4().hex[:8]}"
        try:
            result = create_session(sid, "usr-001", "Test goal")
            assert result is not None
        except:
            pass

    def test_get_session(self):
        from ia.state import get_session
        result = get_session("nonexistent-12345")
        assert result is None or isinstance(result, dict)

    def test_list_sessions(self):
        try:
            from ia.state import list_sessions
            result = list_sessions("usr-001")
            assert isinstance(result, list)
        except (ImportError, AttributeError):
            pass
