"""Tests unitarios del pipeline de validacion."""
import pytest
from validacion_productos import validar_productos_lote, _sanitizar_texto, _sanitizar_precio, _sanitizar_bool, _detectar_peligro

class TestSanitizacionTexto:
    def test_none_retorna_vacio(self): assert _sanitizar_texto(None) == ""
    def test_strip_espacios(self): assert _sanitizar_texto("  Hola  ") == "Hola"
    def test_null_bytes(self): assert _sanitizar_texto("test\x00val") == "testval"
    def test_max_length(self): assert len(_sanitizar_texto("x" * 1000, max_len=100)) <= 100
    def test_numero_a_string(self): assert _sanitizar_texto(12345) == "12345"

class TestSanitizacionPrecio:
    def test_none(self): assert _sanitizar_precio(None) == 0.0
    def test_string(self): assert _sanitizar_precio("19.99") == 19.99
    def test_entero(self): assert _sanitizar_precio(25) == 25.0
    def test_negativo(self): assert _sanitizar_precio(-5.0) == 0.0
    def test_invalido(self): assert _sanitizar_precio("abc") == 0.0
    def test_redondeo(self): assert _sanitizar_precio(19.999) == 20.0

class TestSanitizacionBool:
    def test_true(self): assert _sanitizar_bool(True) is True
    def test_false(self): assert _sanitizar_bool(False) is False
    def test_int_1(self): assert _sanitizar_bool(1) is True
    def test_int_0(self): assert _sanitizar_bool(0) is False
    def test_string_si(self): assert _sanitizar_bool("si") is True
    def test_string_no(self): assert _sanitizar_bool("no") is False

class TestDeteccionPeligro:
    def test_normal(self): assert _detectar_peligro("Producto limpieza") is None
    def test_union(self): assert _detectar_peligro("UNION SELECT") is not None
    def test_drop(self): assert _detectar_peligro("DROP TABLE") is not None

class TestValidacionLote:
    def test_vacio(self):
        r = validar_productos_lote([])
        assert r.valido is False
    def test_excede(self):
        r = validar_productos_lote([{"id": str(i), "nombre": f"P{i}", "precio": 1.0} for i in range(5001)])
        assert r.valido is False
    def test_valido(self):
        r = validar_productos_lote([{"id": "T1", "nombre": "Test", "precio": 10.0}])
        assert r.valido is True and len(r.productos_validos) == 1
    def test_sin_id(self):
        r = validar_productos_lote([{"nombre": "X", "precio": 10.0}])
        assert r.valido is False and any(e.campo == "id" for e in r.errores)
    def test_sin_nombre(self):
        r = validar_productos_lote([{"id": "X1", "precio": 10.0}])
        assert r.valido is False and any(e.campo == "nombre" for e in r.errores)
    def test_precio_neg(self):
        r = validar_productos_lote([{"id": "X1", "nombre": "N", "precio": -5.0}])
        assert r.valido is False and any(e.campo == "precio" for e in r.errores)
    def test_stock_neg(self):
        r = validar_productos_lote([{"id": "X1", "nombre": "N", "precio": 10.0, "stock_actual": -3}])
        assert r.valido is False and any(e.campo == "stock_actual" for e in r.errores)
    def test_dup(self):
        r = validar_productos_lote([{"id": "D", "nombre": "A", "precio": 10.0}, {"id": "D", "nombre": "B", "precio": 20.0}])
        assert r.valido is False and any("duplicado" in e.mensaje.lower() for e in r.errores)
    def test_defaults(self):
        r = validar_productos_lote([{"id": "D1", "nombre": "D", "precio": 5.0}])
        p = r.productos_validos[0]
        assert p["categoria"] == "General" and p["um"] == "C/U" and p["onSale"] is False
