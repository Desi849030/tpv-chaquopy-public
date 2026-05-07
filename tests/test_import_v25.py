import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app/src/main/python"))

from database import obtener_conexion, crear_tablas

reconstruir_desde_productos, importar_catalogo_a_inventario

ADMIN = "user-4fd3220f"

class TestImportacion:
    def test_bd_conexion(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        c.close()

    def test_reconstruir_productos(self):
        prods = [
            {"id": "T1", "nombre": "Test Mod v25", "precio": 5.0, "costoUnitario": 2.0,
             "categoria": "General", "um": "C/U", "enOferta": False, "imagen": "", "stock_actual": 10},
            {"id": "T2", "nombre": "Test Dos v25", "precio": 8.0, "costoUnitario": 3.0,
             "categoria": "Bebidas", "um": "C/U", "enOferta": True, "imagen": "", "stock_actual": 20}
        ]
        r = reconstruir_desde_productos(ADMIN, prods)
        assert r["ok"], r.get("mensaje", "fallo")
        assert r["total"] >= 2

    def test_importar_catalogo_inventario(self):
        r = importar_catalogo_a_inventario(ADMIN)
        assert r["ok"], r.get("mensaje", "fallo")
        assert r["total"] >= 0

    def test_productos_persistentes(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        assert count >= 2, f"Esperaba >= 2 productos, tengo {count}"
        c.close()

    def test_inventario_general_poblado(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM inventario_general")
        count = cur.fetchone()[0]
        assert count >= 2, f"Esperaba >= 2 items inventario, tengo {count}"
        cur.execute("SELECT producto_id, stock_actual FROM inventario_general LIMIT 2")
        rows = cur.fetchall()
        for row in rows:
            assert row[1] >= 0
        c.close()
