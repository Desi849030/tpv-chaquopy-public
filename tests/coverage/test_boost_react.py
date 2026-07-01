"""Ejecuta react_core extensivamente."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_react_all(self):
        from ia.react_core import ReactCore
        c = ReactCore()
        for msg in ["hola","buscar cafe","precio arroz","vender 2 cafe","reporte ventas","ayuda","adios","","stock leche","crear producto"]:
            assert c.think(msg) is not None
        for act in ["search","noop","calculate","unknown","help","exit","greet"]:
            assert c.act(act, {"query":"test","data":{},"empty":None}) is not None
        for obs in ["ok","error","success","failure","","not_found","timeout"]:
            assert c.observe("test_action", {"status":obs,"result":{},"error":None}) is not None
