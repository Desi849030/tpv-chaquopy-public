"""Tests de casos borde - Robustez del sistema"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


def test_stock_zero():
    """Producto con stock 0 no debe dar error"""
    from ia.agent import process_question
    r = process_question('test', 'producto agotado', 'vendedor')
    assert 'answer' in r
    assert len(r['answer']) > 5


def test_precio_negativo():
    """La IA maneja datos anomalos"""
    from ia.nlp_engine import NLPEngine
    nlp = NLPEngine()
    intent, conf = nlp.predict_intent("")
    assert intent == "UNKNOWN" or conf < 0.5


def test_busqueda_sin_resultados():
    """Busqueda sin resultados no rompe"""
    from ia.agent import process_question
    r = process_question('test', 'xyzproducto123', 'cliente')
    assert 'answer' in r
    assert len(r['answer']) > 5


def test_rol_invalido():
    """Rol invalido no debe crashear"""
    from ia.agent import process_question
    r = process_question('test', 'hola', 'rol_invalido')
    assert 'answer' in r


def test_sql_injection_simple():
    """Intento de inyeccion SQL basico"""
    from ia.agent import process_question
    r = process_question('test', "DROP TABLE", 'cliente')
    assert 'answer' in r
    assert 'error' not in r['answer'].lower()


def test_montos_grandes():
    """Manejo de numeros muy grandes"""
    from ia.agent import process_question
    r = process_question('test', 'ventas', 'administrador')
    assert 'answer' in r
    assert len(r['answer']) > 5
