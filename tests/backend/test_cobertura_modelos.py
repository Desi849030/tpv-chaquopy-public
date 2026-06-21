import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"


# ============ models/ ============
class TestModels:
    def test_producto_typeddict(self):
        from models.inventario import Producto
        p = Producto(producto_id="p1", nombre="Test", precio=10.0)
        assert p["producto_id"] == "p1"
        assert p["nombre"] == "Test"

    def test_categoria_typeddict(self):
        from models.inventario import Categoria
        c = Categoria(categoria_id=1, nombre="Cat1")
        assert c["categoria_id"] == 1

    def test_inventario_general_typeddict(self):
        from models.inventario import InventarioGeneral
        ig = InventarioGeneral(producto_id="p1", stock_actual=100.0)
        assert ig["stock_actual"] == 100.0

    def test_usuario_typeddict(self):
        from models.sistema import Usuario
        u = Usuario(usuario_id="u1", username="test", rol="admin")
        assert u["rol"] == "admin"

    def test_cliente_typeddict(self):
        from models.sistema import Cliente
        c = Cliente(cliente_id="c1", nombre="Juan")
        assert c["nombre"] == "Juan"

    def test_caja_typeddict(self):
        from models.sistema import Caja
        c = Caja(caja_id=1, estado="abierta")
        assert c["estado"] == "abierta"

    def test_venta_typeddict(self):
        from models.ventas import Venta
        v = Venta(venta_id="v1", total=100.0, metodo_pago="efectivo")
        assert v["total"] == 100.0

    def test_detalle_venta_typeddict(self):
        from models.ventas import DetalleVenta
        d = DetalleVenta(detalle_id=1, venta_id="v1", cantidad=2.0)
        assert d["cantidad"] == 2.0

    def test_api_response_typeddict(self):
        from models.ventas import APIResponse
        r = APIResponse(ok=True, data={"x": 1})
        assert r["ok"] == True

    def test_paginated_response_typeddict(self):
        from models.ventas import PaginatedResponse
        r = PaginatedResponse(ok=True, total=50, pagina=1, por_pagina=10, total_paginas=5)
        assert r["total"] == 50

    def test_validation_result_typeddict(self):
        from models.ventas import ValidationResult
        r = ValidationResult(valido=True, total_filas=10, total_errores=0, total_validos=10, errores=[], advertencias=[])
        assert r["valido"] == True


# ============ license/ ============
class TestLicense:
    def test_generar_licencia_trial(self):
        from license.core import generar_licencia
        lic = generar_licencia("test-device-001", tipo="trial", valor=7, unidad="dias")
        assert lic["licencia_id"].startswith("LIC-")
        assert lic["tipo"] == "trial"
        assert lic["valor"] == 7
        assert "firma" in lic

    def test_generar_licencia_mensual(self):
        from license.core import generar_licencia
        lic = generar_licencia("device-002", tipo="mensual", valor=1, unidad="meses")
        assert lic["tipo"] == "mensual"

    def test_generar_licencia_horas(self):
        from license.core import generar_licencia
        lic = generar_licencia("device-003", tipo="demo", valor=24, unidad="horas")
        assert lic["valor"] == 24


# ============ dictionary/ ============
class TestDictionary:
    def test_buscar_sinonimos_arroz(self):
        from dictionary.helpers import buscar_sinonimos
        r = buscar_sinonimos("arroz")
        assert isinstance(r, list)
        assert len(r) > 0

    def test_buscar_sinonimos_palabra_inexistente(self):
        from dictionary.helpers import buscar_sinonimos
        r = buscar_sinonimos("xyznonexist123")
        assert isinstance(r, list)

    def test_definir_termino(self):
        from dictionary.helpers import definir_termino
        r = definir_termino("stock")
        assert r is None or isinstance(r, str)

    def test_corregir(self):
        from dictionary.helpers import corregir
        r = corregir("arrozz")
        assert r is None or isinstance(r, str)  # puede devolver None si no corrige

    def test_levenshtein(self):
        from dictionary.helpers import _levenshtein
        d = _levenshtein("casa", "casa")
        assert isinstance(d, int)
        d2 = _levenshtein("casa", "calle")
        assert isinstance(d2, int)

    def test_sin_tildes(self):
        from dictionary.helpers import _sin_tildes
        r = _sin_tildes("café")
        assert "e" in r
