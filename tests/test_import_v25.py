import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app/src/main/python"))

from db_config import crear_tablas, reconstruir_desde_productos
from db_connection import obtener_conexion
from db_products import importar_catalogo_a_inventario

crear_tablas()

class TestImportacion:
    def _get_admin(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT usuario_id FROM usuarios LIMIT 1")
        row = cur.fetchone()
        if row:
            c.close()
            return row[0]
        # Crear usuario de prueba (CI arranca con BD vacia)
        try:
            cur.execute(
                "INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("test_admin_v25", "test_admin_v25", "Test Admin", "administrador",
                 "sha256$dummy", "salt_dummy")
            )
            c.commit()
        except Exception:
            pass
        cur.execute("SELECT usuario_id FROM usuarios LIMIT 1")
        row = cur.fetchone()
        c.close()
        assert row, "No se pudo crear usuario de prueba"
        return row[0]

    def test_bd_conexion(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        c.close()

    def test_reconstruir_productos(self):
        admin = self._get_admin()
        prods = [
            {"id": "T1", "nombre": "Test v25", "precio": 5.0, "costoUnitario": 2.0,
             "categoria": "General", "um": "C/U", "enOferta": False, "imagen": "", "stock_actual": 10},
            {"id": "T2", "nombre": "Test Dos", "precio": 8.0, "costoUnitario": 3.0,
             "categoria": "Bebidas", "um": "C/U", "enOferta": True, "imagen": "", "stock_actual": 20}
        ]
        r = reconstruir_desde_productos(admin, prods)
        assert r is not None, "reconstruir retorno None"
        assert r["ok"], r.get("mensaje", "fallo")
        assert r["total"] >= 2

    def test_importar_catalogo_inventario(self):
        admin = self._get_admin()
        r = importar_catalogo_a_inventario(admin)
        assert r is not None, "importar retorno None"
        assert r["ok"], r.get("mensaje", "fallo")
        assert r["total"] >= 0

    def test_productos_persistentes(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        assert count >= 0, f"Conteo negativo: {count}"
        c.close()

    def test_inventario_general_poblado(self):
        c = obtener_conexion()
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM inventario_general")
        count = cur.fetchone()[0]
        assert count >= 0, f"Conteo negativo: {count}"
        if count > 0:
            cur.execute("SELECT producto_id, stock_actual FROM inventario_general LIMIT 2")
            rows = cur.fetchall()
            for row in rows:
                assert row[1] >= 0
        c.close()
