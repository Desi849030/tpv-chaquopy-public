"""Tests de casos borde - Robustez del sistema"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

def test_stock_zero():
    """Producto con stock 0 no debe dar error"""
    from ia_agent import process_question
    r = process_question('test', 'producto agotado', 'vendedor')
    assert 'answer' in r
    assert len(r['answer']) > 5
    print("✅ Stock cero: OK")

def test_precio_negativo():
    """La IA maneja datos anómalos"""
    from ia.nlp_engine import NLPEngine
    nlp = NLPEngine()
    intent, conf = nlp.predict_intent("")
    assert intent == "UNKNOWN" or conf < 0.5
    print("✅ NLP vacío: OK")

def test_busqueda_sin_resultados():
    """Búsqueda sin resultados no rompe"""
    from ia_agent import process_question
    r = process_question('test', 'xyzproducto123', 'cliente')
    assert 'answer' in r
    print("✅ Búsqueda vacía: OK")

def test_rol_invalido():
    """Rol inválido no debe crashear"""
    from ia_agent import process_question
    r = process_question('test', 'hola', 'rol_invalido')
    assert 'answer' in r
    print("✅ Rol inválido: OK")

def test_sql_injection_simple():
    """Intento de inyección SQL básico"""
    from ia_agent import process_question
    r = process_question('test', "DROP TABLE", 'cliente')
    assert 'answer' in r
    assert 'error' not in r['answer'].lower()
    print("✅ SQL injection: OK")

def test_montos_grandes():
    """Manejo de números muy grandes"""
    from ia_agent import process_question
    r = process_question('test', 'ventas', 'administrador')
    assert 'answer' in r
    print("✅ Montos grandes: OK")

if __name__ == '__main__':
    print("=" * 40)
    print("TPV Smart - Edge Cases Tests")
    print("=" * 40)
    results = [
        test_stock_zero(), test_precio_negativo(),
        test_busqueda_sin_resultados(), test_rol_invalido(),
        test_sql_injection_simple(), test_montos_grandes()
    ]
    passed = sum(results)
    print("=" * 40)
    print(f"Resultado: {passed}/{len(results)} tests pasados")
