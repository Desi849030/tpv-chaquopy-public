import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"


# ============ ia/anti_slop.py ============
class TestIaAntiSlop:
    def test_refine_normal_message(self):
        from ia.anti_slop import refine
        result = refine("Hola, quiero buscar arroz", "cliente")
        assert len(result) > 0

    def test_refine_empty_message(self):
        from ia.anti_slop import refine
        result = refine("", "cliente")
        assert result == ""

    def test_refine_short_message(self):
        from ia.anti_slop import refine
        result = refine("ok", "cliente")
        assert result == "ok"

    def test_get_smart_suggestions_cliente(self):
        from ia.anti_slop import get_smart_suggestions
        result = get_smart_suggestions("cliente")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_smart_suggestions_admin(self):
        from ia.anti_slop import get_smart_suggestions
        result = get_smart_suggestions("administrador")
        assert isinstance(result, list)


# ============ ia/intent_engine.py ============
class TestIaIntentEngine:
    def test_detect_intents_greeting(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("hola buenos dias", "cliente")
        assert len(result) > 0
        assert result[0]["intent"] == "GREETING"

    def test_detect_intents_sales(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("cuanto vendi hoy", "vendedor")
        assert result[0]["intent"] == "SALES"

    def test_detect_intents_unknown(self):
        from ia.intent_engine import detect_intents
        result = detect_intents("zzzzzzzzzz", "cliente")
        assert result[0]["intent"] in ("GENERAL",)

    def test_get_suggestions(self):
        from ia.intent_engine import get_suggestions
        result = get_suggestions("GREETING", "cliente")
        assert isinstance(result, list)


# ============ ia/normalizer.py ============
class TestIaNormalizer:
    def test_normalize_lowercase(self):
        from ia.normalizer import normalize
        result = normalize("HOLA Mundo")
        assert result == "hola mundo"

    def test_normalize_accents(self):
        from ia.normalizer import normalize
        result = normalize("café con leche")
        assert "cafe" in result

    def test_normalize_special_chars(self):
        from ia.normalizer import normalize
        result = normalize("¡hola! ¿cómo?")
        assert result == "hola como"

    def test_normalize_empty(self):
        from ia.normalizer import normalize
        assert normalize("") == ""

    def test_contains_any_match(self):
        from ia.normalizer import contains_any
        matched, keyword, score = contains_any("quiero comprar arroz", ["arroz", "pan"])
        assert matched == True

    def test_contains_any_no_match(self):
        from ia.normalizer import contains_any
        matched, keyword, score = contains_any("xyz", ["arroz", "pan"])
        assert matched == False


# ============ ia/tool_system.py ============
class TestIaToolSystem:
    def test_get_tools_for_role_admin(self):
        from ia.tool_system import get_tools_for_role
        tools = get_tools_for_role("administrador")
        assert len(tools) > 0
        assert "finanzas" in tools

    def test_get_tools_for_role_cliente(self):
        from ia.tool_system import get_tools_for_role
        tools = get_tools_for_role("cliente")
        assert "busqueda" in tools

    def test_suggest_tools_finanzas(self):
        from ia.tool_system import suggest_tools
        result = suggest_tools("quiero ver finanzas", "administrador")
        assert len(result) > 0

    def test_get_help_menu_admin(self):
        from ia.tool_system import get_help_menu
        menu = get_help_menu("administrador")
        assert "balance" in menu.lower() or "finanzas" in menu.lower()

    def test_get_help_menu_cliente(self):
        from ia.tool_system import get_help_menu
        menu = get_help_menu("cliente")
        assert len(menu) > 0

    def test_check_permission_valido(self):
        from ia.tool_system import check_permission
        assert check_permission("finanzas", "administrador") == True

    def test_check_permission_invalido(self):
        from ia.tool_system import check_permission
        assert check_permission("finanzas", "cliente") == False
