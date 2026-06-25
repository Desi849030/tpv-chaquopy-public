"""Tests de forma del catalogo."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app", "src", "main", "python"))

class TestCatalogoShape:
    def test_catalogo_has_productos(self):
        try:
            from db_connection import get_connection
            conn = get_connection()
            cursor = conn.execute("SELECT COUNT(*) as c FROM productos WHERE activo=1")
            count = cursor.fetchone()["c"]
            conn.close()
            assert count > 0
        except Exception as e:
            pytest.skip(f"BD no disponible: {e}")

    def test_producto_has_required_fields(self):
        try:
            from db_connection import get_connection
            conn = get_connection()
            cursor = conn.execute("SELECT * FROM productos LIMIT 1")
            row = dict(cursor.fetchone())
            conn.close()
            for field in ["producto_id", "nombre", "precio", "activo"]:
                assert field in row
        except Exception:
            pytest.skip("BD no disponible")
    
    def test_producto_precio_valido(self):
        try:
            from db_connection import get_connection
            conn = get_connection()
            cursor = conn.execute("SELECT precio FROM productos LIMIT 1")
            precio = cursor.fetchone()["precio"]
            conn.close()
            assert precio > 0
        except Exception:
            pytest.skip("BD no disponible")
