"""Math, financial and analytics utilities for TPV Smart IA."""
import math
from ia.db_utils import q

class M:
    """Mathematical models for business analytics."""

    @staticmethod
    def regresion(x, y):
        n = len(x)
        if n < 2:
            return 0, 0
        sx, sy = sum(x), sum(y)
        sxy = sum(x[i] * y[i] for i in range(n))
        sx2 = sum(v * v for v in x)
        denom = n * sx2 - sx * sx
        m = (n * sxy - sx * sy) / denom if denom != 0 else 0
        return m, (sy - m * sx) / n

    @staticmethod
    def eoq(d, p, m):
        return math.sqrt((2 * d * p) / m) if m > 0 else 0

    @staticmethod
    def punto_eq(cf, p, cv):
        return math.ceil(cf / (p - cv)) if (p - cv) > 0 else float('inf')

    @staticmethod
    def roi(inv, gan):
        return ((gan - inv) / inv) * 100 if inv > 0 else 0


class F:
    """Financial queries and reports."""

    @staticmethod
    def diario():
        d = q(
            "SELECT COUNT(*) t, COALESCE(SUM(total),0) r, "
            "COALESCE(AVG(total),0) a "
            "FROM historial_ventas "
            "WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        g = q(
            "SELECT COALESCE(SUM(monto),0) g "
            "FROM gastos WHERE DATE(fecha)=DATE('now','localtime')",
            one=True)
        return {
            't': d['t'] if d else 0,
            'r': d['r'] if d else 0,
            'a': d['a'] if d else 0,
            'g': g['g'] if g else 0
        }

    @staticmethod
    def semanal():
        d = q(
            "SELECT COUNT(*) t, COALESCE(SUM(total),0) r "
            "FROM historial_ventas WHERE fecha>=DATE('now','-7 days')",
            one=True)
        return {'t': d['t'] if d else 0, 'r': d['r'] if d else 0}

    @staticmethod
    def top(dias=7, lim=5):
        return q(
            "SELECT nombre, SUM(cantidad) q, SUM(total) t "
            "FROM historial_ventas "
            "WHERE fecha>=DATE('now','-" + str(dias) + " days') "
            "GROUP BY nombre ORDER BY q DESC LIMIT " + str(lim))

    @staticmethod
    def abc():
        rows = q(
            "SELECT nombre, SUM(total) rev "
            "FROM historial_ventas "
            "WHERE fecha>=DATE('now','-30 days') "
            "GROUP BY nombre ORDER BY rev DESC LIMIT 30")
        if not rows:
            return {'A': [], 'B': [], 'C': []}
        total = sum(r['rev'] for r in rows)
        if total == 0:
            return {'A': [], 'B': [], 'C': []}
        abc = {'A': [], 'B': [], 'C': []}
        cum = 0
        for r in rows:
            cum += r['rev']
            pv = cum / total * 100
            if pv <= 80:
                abc['A'].append(r['nombre'])
            elif pv <= 95:
                abc['B'].append(r['nombre'])
            else:
                abc['C'].append(r['nombre'])
        return abc


    @staticmethod
    def stock_critico(limite=None):
        """Productos con stock <= minimo (datos reales de inventario_general)."""
        return q(
            "SELECT nombre, stock_actual, stock_minimo "
            "FROM inventario_general "
            "WHERE stock_actual <= COALESCE(NULLIF(stock_minimo,0),5) "
            "ORDER BY stock_actual ASC LIMIT 15")

    @staticmethod
    def stock_resumen():
        """Resumen del inventario general (totales reales)."""
        rows = q(
            "SELECT COUNT(*) total, "
            "SUM(CASE WHEN stock_actual<=0 THEN 1 ELSE 0 END) agotados, "
            "SUM(CASE WHEN stock_actual<=COALESCE(NULLIF(stock_minimo,0),5) AND stock_actual>0 THEN 1 ELSE 0 END) criticos, "
            "SUM(stock_actual) unidades "
            "FROM inventario_general")
        return rows[0] if rows else {"total": 0, "agotados": 0, "criticos": 0, "unidades": 0}

    @staticmethod
    def buscar_stock(nombre):
        """Stock real de un producto por nombre (LIKE)."""
        return q(
            "SELECT nombre, stock_actual, precio_venta "
            "FROM inventario_general WHERE nombre LIKE ? "
            "ORDER BY nombre LIMIT 8", ("%" + nombre + "%",))

    @staticmethod
    def categorias():
        """Productos y valor por categoria (real)."""
        return q(
            "SELECT COALESCE(categoria,'General') cat, COUNT(*) n, "
            "SUM(stock_actual*precio_venta) valor "
            "FROM inventario_general GROUP BY cat ORDER BY valor DESC")

    @staticmethod
    def conteos():
        """Conteos globales para el agente (productos, clientes, ventas hoy)."""
        prod = q("SELECT COUNT(*) n FROM productos WHERE activo=1")
        try:
            cli = q("SELECT COUNT(*) n FROM clientes")
        except Exception:
            cli = [{"n": 0}]
        ventas = q("SELECT COUNT(*) n FROM historial_ventas WHERE fecha LIKE DATE('now')||'%'")
        return {
            "productos": (prod[0]["n"] if prod else 0),
            "clientes": (cli[0]["n"] if cli else 0),
            "ventas_hoy": (ventas[0]["n"] if ventas else 0),
        }
