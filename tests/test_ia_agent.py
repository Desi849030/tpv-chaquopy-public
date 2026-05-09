"""Tests del Gestor IA Total + Modulo Agentic"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


# ============================================================
# Tests principales del agente
# ============================================================

def test_import():
    """Verifica que el agente importe correctamente"""
    from ia_agent import process_question, get_status, ROLES
    assert 'cliente' in ROLES
    assert 'administrador' in ROLES


def test_greeting():
    """Verifica saludo por rol"""
    from ia_agent import process_question
    r = process_question('test', 'hola', 'cliente', 'Test')
    assert 'answer' in r
    assert r['role'] == 'cliente'
    assert len(r['answer']) > 10


def test_product_search():
    """Verifica busqueda de productos"""
    from ia_agent import process_question
    r = process_question('test', 'cafe', 'cliente')
    assert 'answer' in r
    assert len(r['answer']) > 5


def test_finanzas():
    """Verifica finanzas admin"""
    from ia_agent import process_question
    r = process_question('test', 'finanzas', 'administrador')
    assert 'answer' in r
    answer_lower = r['answer'].lower()
    assert 'ingreso' in answer_lower or '$' in r['answer']


def test_abc():
    """Verifica clasificacion ABC"""
    from ia_agent import process_question
    r = process_question('test', 'abc', 'administrador')
    assert 'answer' in r
    assert len(r['answer']) > 5


def test_roles():
    """Verifica los 5 roles"""
    from ia_agent import ROLES
    assert len(ROLES) == 5
    for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
        assert rol in ROLES, "Rol faltante: %s" % rol


# ============================================================
# v18: Agentic Module Tests
# ============================================================

class TestNormalizer:
    """Tests para ia.normalizer"""
    def test_normalize_basic(self):
        from ia.normalizer import normalize
        assert normalize("hola") == "hola"
        assert normalize("HELLO") == "hello"
        assert normalize("") == ""

    def test_normalize_tildes(self):
        from ia.normalizer import normalize
        assert normalize("analisis") == normalize("analisis")
        assert normalize("proyeccion") == normalize("proyeccion")

    def test_normalize_enye(self):
        from ia.normalizer import normalize
        assert normalize("espana") == normalize("espana")

    def test_contains_any_exact(self):
        from ia.normalizer import contains_any
        matched, kw, score = contains_any("quiero ver ventas", ["ventas", "stock"])
        assert matched is True
        assert kw == "ventas"

    def test_contains_any_fuzzy(self):
        from ia.normalizer import contains_any
        matched, kw, score = contains_any("ventaz del cafe", ["ventas", "stock"])
        assert matched is True

    def test_extract_entities(self):
        from ia.normalizer import extract_entities
        entities = extract_entities("cuanto cuesta el cafe con leche")
        assert "cafe" in entities
        assert "leche" in entities
        assert "el" not in entities
        assert "cuanto" not in entities


class TestIntentEngine:
    """Tests para ia.intent_engine"""
    def test_detect_greeting(self):
        from ia.intent_engine import detect_intents
        results = detect_intents("hola buenos dias")
        assert len(results) > 0
        assert results[0]["intent"] == "GREETING"

    def test_detect_sales(self):
        from ia.intent_engine import detect_intents
        results = detect_intents("cuanto vendi hoy")
        assert len(results) > 0
        intents = [r["intent"] for r in results]
        assert "SALES" in intents

    def test_detect_multi_intent(self):
        from ia.intent_engine import detect_intents
        results = detect_intents("ofertas y stock bajo")
        assert len(results) >= 2
        intents = [r["intent"] for r in results]
        assert "OFFERS" in intents
        assert "STOCK_LOW" in intents

    def test_detect_frustration(self):
        from ia.intent_engine import detect_intents
        results = detect_intents("esto no funciona mal")
        intents = [r["intent"] for r in results]
        assert "FRUSTRATION" in intents

    def test_suggestions_cliente(self):
        from ia.intent_engine import get_suggestions
        sug = get_suggestions("GREETING", "cliente")
        assert len(sug) > 0
        assert isinstance(sug, list)


class TestContextMemory:
    """Tests para ia.context_memory"""
    def test_create_context(self):
        from ia.context_memory import get_context
        ctx = get_context("test-session-123")
        assert ctx.sid == "test-session-123"

    def test_add_turn(self):
        from ia.context_memory import get_context
        ctx = get_context("test-session-456")
        ctx.add_turn("hola", "bienvenido", "GREETING")
        assert len(ctx.history) == 1
        assert ctx.last_intent == "GREETING"

    def test_resolve_reference(self):
        from ia.context_memory import get_context
        ctx = get_context("test-session-789")
        ctx.last_product = "cafe"
        ref = ctx.resolve_reference("cuanto cuesta")
        assert "query" in ref
        assert ref["query"] == "cafe"

    def test_get_last_topics(self):
        from ia.context_memory import get_context
        ctx = get_context("test-session-topics")
        ctx.add_turn("ventas", "ventas del dia", "SALES")
        ctx.add_turn("stock", "stock bajo", "STOCK_LOW")
        topics = ctx.get_last_topics()
        assert "SALES" in topics
        assert "STOCK_LOW" in topics
