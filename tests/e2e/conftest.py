"""Fixture de limpieza automática post-tests E2E"""
import pytest
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

@pytest.fixture(autouse=True)
def cleanup_after_tests():
    """Limpia datos de prueba después de TODOS los tests."""
    yield
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cur = conn.cursor()
        
        # Productos de prueba
        cur.execute("DELETE FROM productos WHERE producto_id LIKE 'test-%' OR producto_id LIKE 'prod-test%' OR nombre LIKE '%Test%'")
        cur.execute("DELETE FROM inventario_general WHERE producto_id LIKE 'test-%' OR producto_id LIKE 'prod-test%'")
        
        # Usuarios de prueba
        cur.execute("DELETE FROM usuarios WHERE username LIKE 'test_%' OR username IN ('no_auth')")
        
        # Ventas de prueba
        cur.execute("DELETE FROM historial_ventas WHERE venta_id LIKE 'test-%' OR venta_id LIKE 'vta-test%'")
        cur.execute("DELETE FROM ventas_cabecera WHERE venta_id LIKE 'test-%' OR venta_id LIKE 'vta-test%'")
        cur.execute("DELETE FROM ventas_detalle WHERE venta_id LIKE 'test-%' OR venta_id LIKE 'vta-test%'")
        
        # Licencias de prueba
        cur.execute("DELETE FROM licencias WHERE licencia_id LIKE 'LIC-%' OR device_id LIKE 'test-%'")
        
        # Bio tokens de prueba
        cur.execute("DELETE FROM bio_tokens WHERE device LIKE 'test-%'")
        
        # Clientes de prueba
        cur.execute("DELETE FROM clientes_tienda WHERE cliente_id LIKE 'test-%'")
        
        # Tiendas de prueba
        cur.execute("DELETE FROM tiendas WHERE tienda_id LIKE 'test-%'")
        
        # Restaurar stock de productos demo
        cur.execute("UPDATE inventario_general SET stock_actual=100 WHERE producto_id IN ('p1','p2','p3')")
        
        conn.commit()
        conn.close()
        print("\n🧹 Limpieza post-tests completada")
    except Exception as e:
        print(f"\n⚠️ Error en limpieza: {e}")
