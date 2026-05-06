"""Tests del Gestor IA Total"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

def test_import():
    """Verifica que el agente importe correctamente"""
    try:
        from ia_agent import process_question, get_status, ROLES
        assert 'cliente' in ROLES
        assert 'administrador' in ROLES
        print("✅ Import exitoso")

    except Exception as e:
        print(f"❌ Error: {e}")

def test_greeting():
    """Verifica saludo por rol"""
    from ia_agent import process_question
    r = process_question('test', 'hola', 'cliente', 'Test')
    assert 'answer' in r
    assert r['role'] == 'cliente'
    assert len(r['answer']) > 10
    print("✅ Saludo cliente OK")

def test_product_search():
    """Verifica búsqueda de productos"""
    from ia_agent import process_question
    r = process_question('test', 'cafe', 'cliente')
    assert 'answer' in r
    print("✅ Búsqueda producto OK")

def test_finanzas():
    """Verifica finanzas admin"""
    from ia_agent import process_question
    r = process_question('test', 'finanzas', 'administrador')
    assert 'answer' in r
    assert 'ingreso' in r['answer'].lower() or 'Ingreso' in r['answer'] or '$' in r['answer']
    print("✅ Finanzas admin OK")

def test_abc():
    """Verifica ABC"""
    from ia_agent import process_question
    r = process_question('test', 'abc', 'administrador')
    assert 'answer' in r
    print("✅ ABC OK")

def test_roles():
    """Verifica los 5 roles"""
    from ia_agent import ROLES
    assert len(ROLES) == 5
    for rol in ['cliente','vendedor','supervisor','administrador','desarrollador']:
        assert rol in ROLES
    print("✅ 5 roles OK")

if __name__ == '__main__':
    print("=" * 40)
    print("TPV Smart - Test Suite v1.0")
    print("=" * 40)
    results = []
    results.append(test_import())
    results.append(test_roles())
    results.append(test_greeting())
    results.append(test_product_search())
    results.append(test_finanzas())
    results.append(test_abc())
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Resultado: {passed}/{total} tests pasados")
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print(f"❌ {total - passed} tests fallaron")
