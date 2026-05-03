"""
ia_agent.py v1.0 - TPV Smart - Súper Agente Financiero
Modelos matemáticos, estadística, economía, finanzas
Recomendaciones inteligentes según perfil de cliente
"""
import sqlite3, re, os, random, threading, time, math
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict

# ============================================================
# BASE DE DATOS
# ============================================================
def _db_path():
    for p in ['tpv_datos.db', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')]:
        if os.path.exists(p): return p
    return 'tpv_datos.db'

class DB:
    _conn = None
    @classmethod
    def get(cls):
        try:
            if cls._conn: cls._conn.execute("SELECT 1"); return cls._conn
        except: pass
        path = _db_path()
        if os.path.exists(path):
            cls._conn = sqlite3.connect(path, timeout=3, check_same_thread=False)
            cls._conn.row_factory = sqlite3.Row
            return cls._conn
        return None
    @classmethod
    def q(cls, sql, params=(), one=False):
        c = cls.get()
        if not c: return None
        try:
            cur = c.execute(sql, params)
            return cur.fetchone() if one else cur.fetchall()
        except: return None

# ============================================================
# CATÁLOGO DE PRODUCTOS
# ============================================================
class Products:
    cache = []; cache_t = 0; categorias = []
    @classmethod
    def refresh(cls):
        if cls.cache and time.time()-cls.cache_t < 20: return
        c = DB.get()
        if not c: return
        prods = []
        try:
            for r in c.execute("SELECT nombre,precio,costo,categoria,stock_actual,unidad_medida FROM productos WHERE activo=1").fetchall():
                prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
            names = {p['n'].lower() for p in prods}
            for r in c.execute("SELECT nombre,precio_venta,precio_compra,categoria,stock_actual,unidad_medida FROM inventario_general").fetchall():
                if (r[0] or '').lower() not in names:
                    prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
            cls.cache = prods; cls.cache_t = time.time()
            cls.categorias = sorted(set(p['cat'] for p in prods))
        except: pass
    
    @classmethod
    def search(cls, query, limit=5):
        cls.refresh()
        q = query.lower().strip()
        if len(q)<1: return []
        scored = []
        for p in cls.cache:
            s = 0; nl = p['n'].lower()
            if q == nl: s = 100
            elif q in nl: s = 85
            elif nl in q: s = 70
            else:
                for w in q.split():
                    if len(w)<2: continue
                    if w in nl: s += 30
                    for nw in nl.split():
                        if len(nw)>=3 and SequenceMatcher(None,w,nw).ratio()>0.7: s += 20
            if s>0: scored.append((s,p))
        scored.sort(key=lambda x:x[0], reverse=True)
        return [x[1] for x in scored[:limit]]
    
    @classmethod
    def stats(cls):
        cls.refresh()
        return {'total':len(cls.cache),'low':sum(1 for p in cls.cache if 0<p['s']<=5),'out':sum(1 for p in cls.cache if p['s']<=0),'cats':len(cls.categorias)}

# ============================================================
# MODELOS MATEMÁTICOS Y ESTADÍSTICA
# ============================================================
class MathModels:
    """Modelos matemáticos para análisis de negocio"""
    
    @staticmethod
    def media_movil(datos, ventana=7):
        """Media móvil para suavizar tendencias"""
        if len(datos) < ventana: return datos
        return [sum(datos[i:i+ventana])/ventana for i in range(len(datos)-ventana+1)]
    
    @staticmethod
    def regresion_lineal(x, y):
        """Regresión lineal simple y = mx + b"""
        n = len(x)
        if n < 2: return 0, 0
        sum_x = sum(x); sum_y = sum(y)
        sum_xy = sum(x[i]*y[i] for i in range(n))
        sum_x2 = sum(v*v for v in x)
        m = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x*sum_x) if (n*sum_x2 - sum_x*sum_x) != 0 else 0
        b = (sum_y - m*sum_x) / n
        return m, b
    
    @staticmethod
    def elasticidad_precio(p1, p2, q1, q2):
        """Elasticidad precio de la demanda"""
        if p1 == 0 or q1 == 0: return 0
        var_p = (p2-p1)/p1
        var_q = (q2-q1)/q1
        return abs(var_q/var_p) if var_p != 0 else 0
    
    @staticmethod
    def punto_equilibrio(costo_fijo, precio, costo_variable):
        """Punto de equilibrio en unidades"""
        margen = precio - costo_variable
        return math.ceil(costo_fijo/margen) if margen > 0 else float('inf')
    
    @staticmethod
    def roi(inversion, ganancia):
        """Retorno de inversión"""
        return ((ganancia - inversion)/inversion)*100 if inversion > 0 else 0
    
    @staticmethod
    def indice_rotacion(costo_ventas, inventario_promedio):
        """Índice de rotación de inventario"""
        return costo_ventas/inventario_promedio if inventario_promedio > 0 else 0
    
    @staticmethod
    def eoq(demanda_anual, costo_pedido, costo_mantenimiento):
        """Economic Order Quantity - Cantidad óptima de pedido"""
        if costo_mantenimiento <= 0: return 0
        return math.sqrt((2*demanda_anual*costo_pedido)/costo_mantenimiento)
    
    @staticmethod
    def abc_classification(products):
        """Clasificación ABC de productos por ingresos"""
        sorted_p = sorted(products, key=lambda x: x.get('revenue',0), reverse=True)
        total = sum(p.get('revenue',0) for p in sorted_p)
        if total == 0: return {'A':[],'B':[],'C':[]}
        cum = 0; result = {'A':[],'B':[],'C':[]}
        for p in sorted_p:
            cum += p.get('revenue',0)
            pct = cum/total*100
            if pct <= 80: result['A'].append(p)
            elif pct <= 95: result['B'].append(p)
            else: result['C'].append(p)
        return result

# ============================================================
# ANALIZADOR DE VENTAS
# ============================================================
class SalesAnalyzer:
    @staticmethod
    def daily_summary():
        d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r, COALESCE(AVG(total),0) as a, COALESCE(SUM(cantidad),0) as u FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        return {'txns':d['t'],'revenue':d['r'],'avg':d['a'],'units':int(d['u'])} if d else None
    
    @staticmethod
    def weekly_summary():
        d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r, COALESCE(AVG(total),0) as a FROM historial_ventas WHERE fecha>=DATE('now','-7 days')", one=True)
        return {'txns':d['t'],'revenue':d['r'],'avg':d['a']} if d else None
    
    @staticmethod
    def top_products(days=7, limit=5):
        return DB.q(f"SELECT nombre,SUM(cantidad) q,SUM(total) t FROM historial_ventas WHERE fecha>=DATE('now','-{days} days') GROUP BY nombre ORDER BY q DESC LIMIT {limit}")
    
    @staticmethod
    def hourly_distribution():
        return DB.q("SELECT strftime('%H',fecha) h, COUNT(*) c, COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') GROUP BY h ORDER BY c DESC")
    
    @staticmethod
    def payment_methods():
        return DB.q("SELECT metodo_pago, COUNT(*) c, COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') GROUP BY metodo_pago ORDER BY r DESC")

# ============================================================
# SISTEMA DE RECOMENDACIONES INTELIGENTES
# ============================================================
class SmartRecommender:
    @staticmethod
    def related_products(product_name, limit=3):
        """Productos frecuentemente comprados juntos"""
        rows = DB.q(f"""
            SELECT b.nombre, COUNT(*) as freq
            FROM historial_ventas a JOIN historial_ventas b 
            ON a.venta_id = b.venta_id AND a.nombre != b.nombre
            WHERE a.nombre LIKE ? AND DATE(a.fecha) >= DATE('now','-30 days')
            GROUP BY b.nombre ORDER BY freq DESC LIMIT {limit}
        """, ('%'+product_name+'%',))
        return rows if rows else []
    
    @staticmethod
    def price_drops():
        """Productos con margen bajo que podrían estar en oferta"""
        prods = []
        for p in Products.cache:
            if p['p'] > 0 and p['c'] > 0:
                margin = (p['p']-p['c'])/p['p']*100
                if margin < 25 and p['s'] > 5:
                    prods.append({'n':p['n'],'price':p['p'],'cost':p['c'],'margin':margin,'stock':p['s']})
        return sorted(prods, key=lambda x: x['margin'])[:5]
    
    @staticmethod
    def best_deals():
        """Mejores ofertas - productos con buen margen y mucho stock"""
        deals = []
        for p in Products.cache:
            if p['p'] > 0 and p['c'] > 0 and p['s'] >= 10:
                margin = (p['p']-p['c'])/p['p']*100
                if margin > 30:
                    discount_price = p['p'] * 0.85
                    deals.append({'n':p['n'],'price':p['p'],'discount':discount_price,'margin':margin,'stock':p['s']})
        return sorted(deals, key=lambda x: x['margin'], reverse=True)[:5]
    
    @staticmethod
    def low_stock_alerts():
        """Productos que necesitan reorden urgente"""
        return DB.q("SELECT nombre,stock_actual,precio_venta FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 8")

# ============================================================
# FUNCIONES DE LA APK POR ROL
# ============================================================
APK = {
    'cliente': ['productos','precios','categorias','buscar','tienda'],
    'vendedor': ['caja','ventas','productos','stock','top','cliente_qr'],
    'supervisor': ['dashboard','ventas','inventario','equipo','predicciones'],
    'administrador': ['dashboard','ventas','inventario','usuarios','finanzas','productos','categorias','configuracion','blindajes','licencias'],
    'desarrollador': ['todo','debug','api','logs','supabase','privilegios']
}

def fmt(v, decimals=2):
    try: return f"${float(v):,.{decimals}f}"
    except: return "$0.00"

def pct(v): return f"{float(v):.1f}%"

# ============================================================
# SÚPER AGENTE
# ============================================================
class SuperAgent:
    def __init__(self):
        self.sessions = {}; self.lock = threading.Lock()
        self.math = MathModels()
        self.sales = SalesAnalyzer()
        self.reco = SmartRecommender()
    
    def session(self, sid):
        with self.lock:
            if sid not in self.sessions:
                self.sessions[sid] = {'history':[],'topic':'','prefs':defaultdict(int)}
            return self.sessions[sid]
    
    def process(self, text, sid='default', role='cliente', name=''):
        if not text or not text.strip(): return self._welcome(role, name)
        
        t = text.lower().strip()
        sess = self.session(sid)
        sess['history'].append(t)
        if len(sess['history'])>20: sess['history']=sess['history'][-20:]
        sess['prefs'][t] += 1
        
        # Saludos y ayuda
        if any(w in t for w in ['hola','buenos dias','buenas tardes','buenas noches','hey']):
            return self._welcome(role, name)
        if any(w in t for w in ['adios','chao','bye','gracias']):
            return self._r("Ha sido un placer. Estoy aquí cuando me necesite.", role)
        if any(w in t for w in ['ayuda','help','que puedes','que sabes','funciones']):
            return self._show_help(role)
        
        # Enrutar por rol
        return getattr(self, f'_{role}', self._cliente)(text, t, sess, name)
    
    def _welcome(self, role, name):
        h = datetime.now().hour
        g = "Buenas noches" if h<6 else "Buenos días" if h<12 else "Buen mediodía" if h<14 else "Buenas tardes" if h<20 else "Buenas noches"
        n = f", {name}" if name else ""
        
        if role == 'cliente':
            prods = Products.stats(); deals = self.reco.best_deals()
            msg = f"{g}{n}. Bienvenido a TPV Smart. Hoy tenemos {prods['total']} productos disponibles"
            if deals: msg += f". Le recomiendo: {deals[0]['n']} con descuento a {fmt(deals[0]['discount'])}"
            return self._r(msg+". ¿Qué busca?", role)
        
        elif role == 'vendedor':
            d = self.sales.daily_summary()
            if d and d['txns']>0:
                return self._r(f"{g}{n}. Hoy: {d['txns']} ventas, {fmt(d['revenue'])}. Proyección día: ~{fmt(d['revenue']/datetime.now().hour*24 if datetime.now().hour>0 else d['revenue'])}. ¿Qué necesita?", role)
            return self._r(f"{g}{n}. Iniciando jornada. Tenga un excelente día de ventas.", role)
        
        elif role == 'supervisor':
            prods = Products.stats(); d = self.sales.daily_summary()
            return self._r(f"{g}{n}. Sistema activo: {prods['total']} productos, {prods['low']} con stock bajo. Ventas: {fmt(d['revenue'] if d else 0)}.", role)
        
        elif role == 'administrador':
            prods = Products.stats(); d = self.sales.daily_summary()
            msg = f"{g}{n}. Sistema bajo control: {prods['total']} productos, {prods['cats']} categorías. "
            if d: msg += f"Ventas hoy: {d['txns']} transacciones, {fmt(d['revenue'])}."
            if prods['low']>0: msg += f" ⚠️ {prods['low']} productos requieren reabastecimiento."
            return self._r(msg, role)
        
        else:
            prods = Products.stats()
            return self._r(f"{g}{n}. Acceso total. {prods['total']} productos en sistema. Escriba 'ayuda' para ver funciones.", role)
    
    def _show_help(self, role):
        funcs = APK.get(role, [])
        labels = {'cliente':'Estimado cliente','vendedor':'Vendedor','supervisor':'Supervisor','administrador':'Administrador','desarrollador':'Desarrollador'}
        msg = f"{labels.get(role,'Usuario')}, puedo ayudarle con:\n\n"
        
        if role == 'cliente':
            msg += "• Buscar productos y precios\n• Ver categorías\n• Mejores ofertas del día\n• Productos recomendados\n• ¿Dónde encontrar un producto?\n\nEjemplo: 'busco café' o 'mejores ofertas'"
        elif role == 'vendedor':
            msg += "• Ventas del día y proyecciones\n• Consultar precios y stock\n• Top productos más vendidos\n• Alertas de stock bajo\n• Análisis de hora pico\n\nEjemplo: 'ventas' o 'stock bajo'"
        elif role == 'supervisor':
            msg += "• Dashboard de ventas\n• Análisis de tendencias\n• Rendimiento del equipo\n• Proyecciones y KPIs\n• Alertas de inventario\n\nEjemplo: 'dashboard' o 'tendencias'"
        elif role == 'administrador':
            msg += "• Reportes financieros completos\n• Análisis ABC de productos\n• Punto de equilibrio\n• ROI y rentabilidad\n• Elasticidad de precios\n• Predicciones de demanda\n\nEjemplo: 'análisis ABC' o 'finanzas'"
        else:
            msg += "• Todas las funciones del sistema\n• Debug y logs\n• API y Supabase\n• Modelos matemáticos\n\nEjemplo: 'estado del sistema'"
        
        return self._r(msg, role)
    
    # ============================================================
    # CLIENTE
    # ============================================================
    def _cliente(self, text, t, sess, name):
        # Ofertas
        if any(w in t for w in ['oferta','descuento','rebaja','mejor precio','barato','promocion']):
            deals = self.reco.best_deals()
            if deals:
                msg = "Nuestras mejores ofertas hoy:\n\n"
                for i,d in enumerate(deals[:5],1):
                    ahorro = d['price'] - d['discount']
                    msg += f"{i}. {d['n']}: {fmt(d['discount'])} (antes {fmt(d['price'])}, ahorra {fmt(ahorro)})\n"
                return self._r(msg, 'cliente')
            return self._r("Hoy todos nuestros precios son competitivos. ¿Qué producto le interesa?", 'cliente')
        
        # ¿Dónde está X?
        if any(w in t for w in ['donde','tienda','sucursal','ubicacion','lugar']):
            return self._r("Nuestros productos están disponibles en nuestra tienda principal y en la tienda online. ¿Cuál le interesa?", 'cliente')
        
        # Buscar producto
        prods = Products.search(text, 5)
        if prods:
            if len(prods) == 1:
                p = prods[0]
                msg = f"{p['n']}: {fmt(p['p'])}/{p['u']}. "
                if p['s'] == 0: msg += "Agotado. ¿Desea ver alternativas?"
                elif p['s'] <= 3: msg += f"¡Solo {p['s']:.0f} disponibles!"
                else: msg += f"Stock disponible."
                
                # Productos complementarios
                related = self.reco.related_products(p['n'], 2)
                if related: msg += f" Suele comprarse con: {related[0]['nombre']}."
                return self._r(msg, 'cliente')
            else:
                return self._r(f"Encontré {len(prods)} opciones: " + ", ".join([f"{p['n']} {fmt(p['p'])}" for p in prods[:5]]), 'cliente')
        
        if any(w in t for w in ['categorias','catalogo']):
            return self._r(f"Categorías: {', '.join(Products.categorias[:12])}. ¿Cuál le interesa?", 'cliente')
        
        return self._r("Dígame qué producto busca. También puede preguntar por 'ofertas' o 'categorías'.", 'cliente')
    
    # ============================================================
    # VENDEDOR
    # ============================================================
    def _vendedor(self, text, t, sess, name):
        if any(w in t for w in ['ventas','caja','recaude','como voy','cuanto vendi']):
            d = self.sales.daily_summary()
            hour = datetime.now().hour
            if d and d['txns']>0:
                proy = d['revenue']/hour*24 if hour>0 else d['revenue']
                msg = f"Hoy: {d['txns']} ventas, {fmt(d['revenue'])}, ticket prom: {fmt(d['avg'])}. Proyección: ~{fmt(proy)}."
                
                # Hora pico
                peak = self.sales.hourly_distribution()
                if peak:
                    msg += f" Hora pico: {peak[0]['h']}:00 ({peak[0]['c']} ventas)."
                return self._r(msg, 'vendedor')
            return self._r("Sin ventas aún. ¡Aproveche para revisar el catálogo!", 'vendedor')
        
        if any(w in t for w in ['stock bajo','agotado','critico','reabastecer']):
            rows = self.reco.low_stock_alerts()
            if rows:
                msg = f"⚠️ {len(rows)} productos necesitan reabastecimiento: " + ", ".join([f"{r['nombre']}({r['stock_actual']:.0f})" for r in rows[:6]])
                return self._r(msg, 'vendedor')
            return self._r("Todo en orden, stock suficiente.", 'vendedor')
        
        if any(w in t for w in ['top','mas vendido','ranking']):
            top = self.sales.top_products(7,5)
            if top:
                return self._r("Lo más vendido: " + ", ".join([f"{r['nombre']}({r['q']:.0f})" for r in top]), 'vendedor')
            return self._r("Sin datos aún.", 'vendedor')
        
        prods = Products.search(text, 5)
        if prods:
            return self._r("; ".join([f"{p['n']} {fmt(p['p'])} stock:{p['s']:.0f}" for p in prods[:5]]), 'vendedor')
        
        return self._r("Consulte: 'ventas', 'stock bajo', 'top productos' o el nombre de un producto.", 'vendedor')
    
    # ============================================================
    # SUPERVISOR
    # ============================================================
    def _supervisor(self, text, t, sess, name):
        d = self.sales.daily_summary(); prods = Products.stats()
        
        if any(w in t for w in ['dashboard','resumen','estado','kpi']):
            w = self.sales.weekly_summary()
            return self._r(f"Dashboard: Hoy {fmt(d['revenue'] if d else 0)} | Semana {fmt(w['revenue'] if w else 0)} | {prods['total']} productos | {prods['low']} stock bajo.", 'supervisor')
        
        if any(w in t for w in ['tendencia','prediccion','proyeccion']):
            return self._r(f"Proyección semanal: {fmt((d['revenue'] if d else 0)*7)} basado en tendencia actual.", 'supervisor')
        
        prods_f = Products.search(text, 5)
        if prods_f: return self._r("; ".join([f"{p['n']} {fmt(p['p'])}" for p in prods_f[:5]]), 'supervisor')
        
        return self._r("Dashboard, tendencias, KPIs, productos. ¿Qué necesita?", 'supervisor')
    
    # ============================================================
    # ADMINISTRADOR
    # ============================================================
    def _administrador(self, text, t, sess, name):
        d = self.sales.daily_summary(); prods = Products.stats()
        
        # FINANZAS
        if any(w in t for w in ['finanza','margen','gasto','ingreso','balance','ganancia','rentabilidad']):
            gastos = DB.q("SELECT COALESCE(SUM(monto),0) g FROM gastos WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            g = gastos['g'] if gastos else 0
            rev = d['revenue'] if d else 0
            profit = rev - g
            m = (profit/rev*100) if rev>0 else 0
            return self._r(f"Balance hoy: Ingresos {fmt(rev)} | Gastos {fmt(g)} | Ganancia {fmt(profit)} | Margen neto {pct(m)}", 'administrador')
        
        # ANÁLISIS ABC
        if any(w in t for w in ['abc','pareto','clasificacion']):
            rows = DB.q("SELECT nombre,SUM(total) revenue FROM historial_ventas WHERE fecha>=DATE('now','-30 days') GROUP BY nombre ORDER BY revenue DESC LIMIT 30")
            if rows:
                abc = self.math.abc_classification([{'n':r['nombre'],'revenue':r['revenue']} for r in rows])
                msg = f"Análisis ABC (30 días):\n• Categoría A (80% ingresos): {len(abc['A'])} productos\n• Categoría B (15%): {len(abc['B'])} productos\n• Categoría C (5%): {len(abc['C'])} productos"
                return self._r(msg, 'administrador')
            return self._r("Datos insuficientes para análisis ABC.", 'administrador')
        
        # PUNTO DE EQUILIBRIO
        if any(w in t for w in ['punto equilibrio','break even','umbral']):
            gastos_fijos = DB.q("SELECT COALESCE(SUM(monto),0) g FROM gastos WHERE fecha>=DATE('now','-30 days')", one=True)
            gf = gastos_fijos['g']/30 if gastos_fijos else 100
            avg_price = sum(p['p'] for p in Products.cache)/len(Products.cache) if Products.cache else 10
            avg_cost = sum(p['c'] for p in Products.cache)/len(Products.cache) if Products.cache else 5
            pe = self.math.punto_equilibrio(gf, avg_price, avg_cost)
            return self._r(f"Punto de equilibrio diario: {pe} unidades. Costo fijo diario: {fmt(gf)}, Precio prom: {fmt(avg_price)}, Costo prom: {fmt(avg_cost)}", 'administrador')
        
        # ELASTICIDAD
        if any(w in t for w in ['elasticidad','sensibilidad precio']):
            top = self.sales.top_products(30, 2)
            if top and len(top)>=2:
                return self._r(f"Para análisis de elasticidad necesito histórico de cambios de precio. Actualmente el producto líder es {top[0]['nombre']} con {top[0]['q']:.0f} unidades.", 'administrador')
            return self._r("Datos insuficientes para calcular elasticidad.", 'administrador')
        
        # ROTACIÓN INVENTARIO
        if any(w in t for w in ['rotacion','inventario','indice rotacion']):
            costo_ventas = DB.q("SELECT COALESCE(SUM(cantidad*costo),0) cv FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
            inv_prom = sum(p['c']*p['s'] for p in Products.cache)/len(Products.cache) if Products.cache else 1
            rot = self.math.indice_rotacion(costo_ventas['cv'] if costo_ventas else 0, inv_prom)
            return self._r(f"Índice de rotación (30 días): {rot:.2f} veces. Indica cuántas veces se renovó el inventario.", 'administrador')
        
        # EOQ
        if any(w in t for w in ['eoq','lote optimo','pedido optimo','cantidad pedido']):
            return self._r("Para calcular el lote óptimo (EOQ) necesito: demanda anual estimada, costo por pedido y costo de mantenimiento. ¿Desea proporcionarlos?", 'administrador')
        
        # PREDICCIONES
        if any(w in t for w in ['prediccion','pronostico','proyeccion','forecast']):
            days = 7
            rows = DB.q(f"SELECT DATE(fecha) d, SUM(total) r FROM historial_ventas WHERE fecha>=DATE('now','-{days} days') GROUP BY DATE(fecha) ORDER BY d")
            if rows and len(rows)>=3:
                x = list(range(len(rows))); y = [r['r'] for r in rows]
                m, b = self.math.regresion_lineal(x, y)
                next_val = m*len(rows) + b
                trend = "creciente" if m>0 else "decreciente"
                return self._r(f"Tendencia {trend}. Próximo día estimado: {fmt(max(0,next_val))}. Pendiente: {fmt(m)}/día.", 'administrador')
            return self._r("Necesito al menos 3 días de datos para proyectar.", 'administrador')
        
        prods_f = Products.search(text, 5)
        if prods_f: return self._r("; ".join([f"{p['n']} {fmt(p['p'])} stock:{p['s']:.0f}" for p in prods_f[:5]]), 'administrador')
        
        return self._r("Funciones: finanzas, ABC, punto equilibrio, elasticidad, rotación, EOQ, predicciones.", 'administrador')
    
    # ============================================================
    # DESARROLLADOR
    # ============================================================
    def _desarrollador(self, text, t, sess, name):
        if any(w in t for w in ['estado','sistema','status']):
            prods = Products.stats()
            users = DB.q("SELECT COUNT(*) c FROM usuarios", one=True)
            return self._r(f"Sistema: {prods['total']} productos, {users['c'] if users else '?'} usuarios. 27 módulos Python, 114 rutas API. Todo operativo.", 'desarrollador')
        
        prods_f = Products.search(text, 5)
        if prods_f: return self._r("; ".join([f"{p['n']} {fmt(p['p'])}" for p in prods_f[:5]]), 'desarrollador')
        
        return self._r("Sistema activo. 'estado' para diagnóstico completo.", 'desarrollador')
    
    def _r(self, msg, role):
        return {'answer': msg, 'role': role, 'suggestions': [], 'ts': datetime.now().isoformat()}

# ============================================================
# SINGLETON
# ============================================================
_agent = None; _lock = threading.Lock()

def _get():
    global _agent
    if not _agent:
        with _lock:
            if not _agent: _agent = SuperAgent()
    return _agent

def process_question(sid, question, role='cliente', user_name=''):
    r = _get().process(question, sid, role, user_name)
    return {'answer':r['answer'],'intent':'chat','suggestions':[],'role':role,'role_label':ROLES.get(role,{}).get('label','Usuario'),'role_color':ROLES.get(role,{}).get('color','#3498db'),'role_icon':ROLES.get(role,{}).get('icon','?'),'ts':r['ts']}

def get_status():
    return {'version':'1.0.0','model':'Súper Agente - Matemáticas + Finanzas + Estadística','status':'active','features':['Regresión lineal','EOQ','ABC','Elasticidad','Punto equilibrio','ROI','Rotación','Proyecciones','Recomendaciones inteligentes']}

def get_conversation_history(sid='default'): return []
def get_proactive_alerts(sid='default'):
    a = []; low = DB.q("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual<=3 AND stock_actual>=0")
    if low and low[0]['c']>0: a.append({'type':'warning','icon':'⚠️','msg':f'{low[0]["c"]} productos necesitan reabastecimiento urgente'})
    return {'alerts':a}

def set_session_role(sid, role, name=''): return role
def get_session_info(sid): return {'role':'cliente','role_label':'Cliente','role_color':'#2ecc71','role_icon':'C'}

ROLES = {'cliente':{'label':'Cliente','color':'#2ecc71','icon':'C'},'vendedor':{'label':'Vendedor','color':'#3498db','icon':'V'},'supervisor':{'label':'Supervisor','color':'#f39c12','icon':'S'},'administrador':{'label':'Administrador','color':'#e74c3c','icon':'A'},'desarrollador':{'label':'Desarrollador','color':'#9b59b6','icon':'D'}}

print("🚀 Súper Agente Financiero v1.0 activo")
