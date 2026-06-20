import os
"""Tests básicos del TPV Ultra Smart"""
import sys
sys.path.insert(0, 'app/src/main/python')

def test_health():
    """Verifica que el servidor responda"""
    import requests
    r = requests.get('http://127.0.0.1:5000/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
    print("✅ test_health OK")

def test_catalogo():
    """Verifica que el catálogo tenga productos"""
    import requests
    r = requests.get('http://127.0.0.1:5000/api/catalogo')
    assert r.status_code == 200
    data = r.json()
    assert len(data['productos']) > 0
    print(f"✅ test_catalogo OK ({len(data['productos'])} productos)")

def test_login():
    """Verifica login"""
    import requests
    r = requests.post('http://127.0.0.1:5000/api/auth/login', 
                     json={'username': 'desarrollador', 'password': os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')})
    assert r.status_code == 200
    assert r.json()['ok'] == True
    print("✅ test_login OK")

def test_ventas():
    """Verifica API de ventas"""
    import requests
    r = requests.get('http://127.0.0.1:5000/api/ventas/totales')
    assert r.status_code == 200
    assert r.json()['ok'] == True
    print("✅ test_ventas OK")

def test_agente():
    """Verifica agente IA"""
    import requests
    r = requests.post('http://127.0.0.1:5000/api/agent/chat',
                     json={'mensaje': 'Hola', 'rol': 'desarrollador'})
    assert r.status_code == 200
    assert 'respuesta' in r.json()
    print("✅ test_agente OK")

if __name__ == '__main__':
    print("=" * 50)
    print("TPV Ultra Smart - Tests Básicos")
    print("=" * 50)
    tests = [test_health, test_catalogo, test_login, test_ventas, test_agente]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests pasados")
