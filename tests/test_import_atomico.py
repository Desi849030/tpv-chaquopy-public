import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))
from validacion_productos import validar_productos_lote, ResultadoValidacion

class TestValidacionProductos:
    def test_campo_obligatorio_faltante(self):
        productos = [{"nombre": "Pan", "precio": 1.5}]
        r = validar_productos_lote(productos)
        assert r.valido == False
        assert any("id" in e.campo for e in r.errores)

    def test_precio_negativo(self):
        productos = [{"id": "1", "nombre": "Pan", "precio": -5}]
        r = validar_productos_lote(productos)
        assert r.valido == False

    def test_producto_valido(self):
        productos = [{"id": "1", "nombre": "Pan", "precio": 1.5}]
        r = validar_productos_lote(productos)
        assert r.valido == True
        assert len(r.productos_validos) == 1

    def test_resultado_to_dict(self):
        r = ResultadoValidacion(valido=True, total_filas=10)
        d = r.to_dict()
        assert "valido" in d
        assert d["total_errores"] == 0
