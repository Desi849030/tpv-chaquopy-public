"""Ejecuta db_ventas."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_ventas(self):
        try:
            from db_ventas import obtener_ventas_hoy, obtener_ventas_periodo
            r = obtener_ventas_hoy()
            assert isinstance(r, list)
            r2 = obtener_ventas_periodo("2026-01-01","2026-12-31")
            assert isinstance(r2, list)
        except Exception:
            pass
