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


# ================================================================
# Objetos de conveniencia P (Productos) y O (Ofertas)
# Usados por handlers_cliente.py y handlers_staff.py
# ================================================================

class ProductAccessor:
    """Acceso rapido a productos para los handlers de IA.
    Cache en memoria con lazy loading desde BD."""

    def __init__(self):
        self._cache = []
        self._cats = []
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._load()
            self._loaded = True

    @property
    def cache(self):
        """Lista de productos en cache: [{n, p, c, s, u, cat}, ...]"""
        self._ensure_loaded()
        return self._cache

    @property
    def cats(self):
        """Lista de categorias unicas."""
        self._ensure_loaded()
        return self._cats

    def _load(self):
        """Carga productos desde BD."""
        try:
            from ia.db_utils import q
            rows = q(
                "SELECT p.nombre n, p.precio_venta p, p.precio_compra c, "
                "COALESCE(i.stock_actual, 0) s, p.unidad_medida u, p.categoria cat "
                "FROM productos p LEFT JOIN inventario_general i "
                "ON p.producto_id = i.producto_id "
                "WHERE p.activo=1 ORDER BY p.nombre"
            )
            if rows:
                self._cache = [dict(r) for r in rows]
                self._cats = sorted(set(r['cat'] or 'General' for r in self._cache))
            else:
                self._cache = []
                self._cats = []
        except Exception:
            # Fallback: intentar sin inventario_general
            try:
                from ia.db_utils import q
                rows = q(
                    "SELECT nombre n, precio p, precio_compra c, "
                    "stock_actual s, unidad_medida u, categoria cat "
                    "FROM productos WHERE activo=1 ORDER BY nombre"
                )
                if rows:
                    self._cache = [dict(r) for r in rows]
                    self._cats = sorted(set(r['cat'] or 'General' for r in self._cache))
            except Exception:
                self._cache = []
                self._cats = []

    def search(self, query, limit=10):
        """Busca productos por texto (con fuzzy match)."""
        self._ensure_loaded()
        if not query or not self._cache:
            return []
        ql = query.lower().strip()
        results = []
        for p in self._cache:
            if ql in p.get('n', '').lower():
                results.append(p)
        # Fuzzy fallback si no hay resultados exactos
        if not results:
            try:
                from ia.fuzzy_match import best_match
                names = [p['n'] for p in self._cache]
                match, score = best_match(query, names, threshold=50)
                if match:
                    results = [p for p in self._cache if p['n'] == match]
            except Exception:
                pass
        return results[:limit]

    def refresh(self):
        """Fuerza recarga desde BD."""
        self._loaded = False
        self._ensure_loaded()


class OfferAccessor:
    """Acceso rapido a ofertas y recomendaciones para los handlers de IA."""

    def mejores(self):
        """Devuelve productos ideales para oferta (margen alto)."""
        try:
            from ia.db_utils import q
            rows = q(
                "SELECT nombre n, precio_venta p, precio_compra c "
                "FROM productos WHERE activo=1 AND precio_compra > 0 "
                "AND (precio_venta - precio_compra) / precio_venta > 0.3 "
                "ORDER BY (precio_venta - precio_compra)/precio_venta DESC LIMIT 10"
            )
            if not rows:
                return []
            ofertas = []
            for r in rows:
                r = dict(r)
                r['m'] = (r['p'] - r['c']) / r['p'] if r['p'] > 0 else 0
                # Precio con 15% descuento
                r['d'] = r['p'] * 0.85
                ofertas.append(r)
            return ofertas
        except Exception:
            return []

    def relacionados(self, nombre, limit=3):
        """Devuelve productos relacionados por categoria."""
        try:
            from ia.db_utils import q
            cat = q("SELECT categoria FROM productos WHERE nombre=? LIMIT 1",
                    (nombre,), one=True)
            if not cat:
                return []
            rows = q(
                "SELECT nombre, precio_venta as precio FROM productos "
                "WHERE activo=1 AND categoria=? AND nombre!=? LIMIT ?",
                (cat['categoria'], nombre, limit)
            )
            return [{'nombre': r['nombre'], 'precio': r['precio']} for r in (rows or [])]
        except Exception:
            return []


# Instancias globales para uso en handlers
P = ProductAccessor()
O = OfferAccessor()
