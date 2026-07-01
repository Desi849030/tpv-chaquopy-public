"""Ejecuta handlers reales."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_cajero_all(self):
        from ia.handlers_staff import CajeroHandler
        h = CajeroHandler()
        for msg in ["hola","buscar cafe","precio","vender","reporte","ayuda","adios","stock","inventario"]:
            assert h.handle(msg, {"role":"cajero"}) is not None
    def test_vendedor_all(self):
        from ia.handlers_staff import VendedorHandler
        h = VendedorHandler()
        for msg in ["hola","buscar cafe","precio","vender","reporte","ayuda","adios","stock"]:
            assert h.handle(msg, {"role":"vendedor"}) is not None
    def test_admin_all(self):
        from ia.handlers_staff import AdminHandler
        h = AdminHandler()
        for msg in ["hola","reporte","usuarios","config","ayuda","admin"]:
            assert h.handle(msg, {"role":"administrador"}) is not None
    def test_dev_all(self):
        from ia.handlers_staff import DevHandler
        h = DevHandler()
        for msg in ["hola","diagnostico","debug","log","test","ayuda"]:
            assert h.handle(msg, {"role":"desarrollador"}) is not None
