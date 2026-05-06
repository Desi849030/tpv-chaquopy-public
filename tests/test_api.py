import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

def test_app():
    from app import _MODULOS_DISPONIBLES, _PRIVILEGIOS_DEFAULT
    assert len(_MODULOS_DISPONIBLES) >= 20
    assert len(_PRIVILEGIOS_DEFAULT) >= 3
    print(f"✅ app.py: {len(_MODULOS_DISPONIBLES)} módulos OK")

def test_db():
    from database import obtener_conexion
    print("✅ database.py OK")

def test_routes():
    from app import app
    rules = list(app.url_map.iter_rules())
    print(f"✅ {len(rules)} rutas registradas")

if __name__ == '__main__':
    print("=" * 40)
    r = [test_app(), test_db(), test_routes()]
    print(f"Resultado: {sum(r)}/{len(r)} tests pasados")
