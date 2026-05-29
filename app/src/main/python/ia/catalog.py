# -*- coding: utf-8 -*-
"""
Catálogo de Productos - Acceso a BD
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tpv.db')


class Catalog:
    def __init__(self):
        self.db_path = DB_PATH
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_products(self):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, codigo, nombre, descripcion, precio, 
                       precio_compra, costo, categoria, stock_actual, 
                       stock_minimo, unidad_medida, activo
                FROM productos 
                WHERE activo = 1
                ORDER BY categoria, nombre
            """)
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return products
            
        except Exception as e:
            logger.error(f"Error obteniendo productos: {e}")
            return []
    
    def get_products_by_category(self, category):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, codigo, nombre, descripcion, precio, 
                       precio_compra, costo, categoria, stock_actual
                FROM productos 
                WHERE activo = 1 AND categoria = ?
                ORDER BY nombre
            """, (category,))
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return products
            
        except Exception as e:
            logger.error(f"Error obteniendo productos por categoría: {e}")
            return []
    
    def get_product_by_name(self, name):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, codigo, nombre, descripcion, precio, 
                       precio_compra, costo, categoria, stock_actual
                FROM productos 
                WHERE activo = 1 AND nombre LIKE ?
                LIMIT 1
            """, (f'%{name}%',))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Error buscando producto: {e}")
            return None
    
    def get_stock_stats(self):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM productos WHERE activo = 1")
            total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as stock_bajo 
                FROM productos 
                WHERE activo = 1 AND stock_actual <= stock_minimo AND stock_actual > 0
            """)
            stock_bajo = cursor.fetchone()['stock_bajo']
            
            cursor.execute("""
                SELECT COUNT(*) as agotados 
                FROM productos 
                WHERE activo = 1 AND stock_actual = 0
            """)
            agotados = cursor.fetchone()['agotados']
            
            cursor.execute("""
                SELECT COUNT(*) as con_stock 
                FROM productos 
                WHERE activo = 1 AND stock_actual > 0
            """)
            con_stock = cursor.fetchone()['con_stock']
            
            cursor.execute("""
                SELECT SUM(precio * stock_actual) as valor_total 
                FROM productos 
                WHERE activo = 1
            """)
            row = cursor.fetchone()
            valor_total = row['valor_total'] if row['valor_total'] else 0
            
            conn.close()
            
            return {
                'total': total,
                'stock_bajo': stock_bajo,
                'agotados': agotados,
                'con_stock': con_stock,
                'valor_total': valor_total
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total': 0,
                'stock_bajo': 0,
                'agotados': 0,
                'con_stock': 0,
                'valor_total': 0
            }
    
    def refresh(self):
        pass
