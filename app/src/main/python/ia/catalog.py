"""Product catalog, search and offers for TPV Smart IA."""
import time
from difflib import SequenceMatcher
from ia.db_utils import _db, q

class P:
    """Product cache and fuzzy search."""
    cache = []
    ct = 0
    cats = []

    @classmethod
    def refresh(cls):
        if cls.cache and time.time() - cls.ct < 20:
            return
        c = _db()
        if not c:
            return
        prods = []
        rows = c.execute(
            "SELECT nombre, precio_venta as precio, precio_compra as costo, "
            "categoria, stock_actual, unidad_medida FROM inventario_general"
        ).fetchall()
        if not rows:
            rows = c.execute(
                "SELECT nombre, precio as precio, costoUnitario as costo, "
                "categoria, stock_actual, unidad_medida as um FROM productos WHERE activo=1"
            ).fetchall()
        for r in rows:
            prods.append({
                'n': r[0] or '', 'p': float(r[1] or 0),
                'c': float(r[2] or 0), 'cat': r[3] or 'General',
                's': float(r[4] or 0), 'u': r[5] or 'Un'
            })
        cls.cache = prods
        cls.ct = time.time()
        cls.cats = sorted(set(p['cat'] for p in prods))

    @classmethod
    def search(cls, query, limit=10):
        cls.refresh()
        qr = query.lower().strip()
        if len(qr) < 2:
            return []
        sc = []
        for p in cls.cache:
            s = 0
            nl = p['n'].lower()
            if qr == nl:
                s = 100
            elif qr in nl:
                s = 85
            elif nl in qr:
                s = 70
            else:
                for w in qr.split():
                    if len(w) < 2:
                        continue
                    if w in nl:
                        s += 30
                    for nw in nl.split():
                        if len(nw) >= 3 and SequenceMatcher(None, w, nw).ratio() > 0.7:
                            s += 20
            if s > 0:
                sc.append((s, p))
        sc.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in sc[:limit]]


class O:
    """Offers and related products."""

    @staticmethod
    def mejores():
        deals = []
        for p in P.cache:
            if p['p'] > 0 and p['c'] > 0 and p['s'] >= 10:
                m = (p['p'] - p['c']) / p['p'] * 100
                if m > 30:
                    deals.append({
                        'n': p['n'], 'p': p['p'],
                        'd': p['p'] * 0.85, 'm': m, 's': p['s']
                    })
        return sorted(deals, key=lambda x: x['m'], reverse=True)[:5]

    @staticmethod
    def relacionados(prod, lim=3):
        return q(
            "SELECT b.nombre, COUNT(*) f "
            "FROM historial_ventas a JOIN historial_ventas b "
            "ON a.venta_id=b.venta_id AND a.nombre!=b.nombre "
            "WHERE a.nombre LIKE ? AND DATE(a.fecha)>=DATE('now','-30 days') "
            "GROUP BY b.nombre ORDER BY f DESC LIMIT " + str(lim),
            ('%' + prod + '%',)
        )
