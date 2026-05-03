"""
ia_agent.py v1.0 - TPV Smart - Asistente Virtual
Responde de forma natural según el rol del usuario
"""
import sqlite3, json, math, re, os, random, threading, time
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher

def _db_path():
    paths = ['tpv_datos.db', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')]
    for p in paths:
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

class ProductSearch:
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
        return {'total':len(cls.cache),'low':sum(1 for p in cls.cache if 0<p['s']<=5)}

class Agent:
    def __init__(self):
        self.memories = {}; self.lock = threading.Lock()
    
    def mem(self, sid):
        with self.lock:
            if sid not in self.memories: self.memories[sid] = []
            return self.memories[sid]
    
    def process(self, text, sid='default', role='cliente', name=''):
        if not text or not text.strip():
            return self._respond("¡Hola! ¿En qué puedo ayudarte? Puedes preguntarme por productos, precios o lo que necesites.", role)
        
        text_lower = text.lower().strip()
        mem = self.mem(sid)
        mem.append(text)
        if len(mem) > 10: mem.pop(0)
        
        # Saludos
        if any(w in text_lower for w in ['hola','buenos dias','buenas tardes','buenas noches','hey','que tal']):
            return self._greeting(role, name)
        
        # Despedidas
        if any(w in text_lower for w in ['adios','chao','bye','gracias','nos vemos']):
            return self._respond("¡Hasta luego! Estoy aquí cuando me necesites.", role)
        
        # Ayuda
        if any(w in text_lower for w in ['ayuda','help','que puedes','como funciona']):
            return self._help(role)
        
        # CLIENTE - Solo productos, precios y tienda
        if role == 'cliente':
            return self._handle_cliente(text, text_lower)
        
        # VENDEDOR - Ventas del día, productos, stock
        elif role == 'vendedor':
            return self._handle_vendedor(text, text_lower)
        
        # ADMIN/SUPERVISOR/DESARROLLADOR - Todo
        else:
            return self._handle_admin(text, text_lower, role)
    
    def _greeting(self, role, name):
        h = datetime.now().hour
        saludo = "Buenas noches" if h<6 else "Buenos días" if h<12 else "Buenas tardes" if h<20 else "Buenas noches"
        nombre = f" {name}" if name else ""
        
        if role == 'cliente':
            return self._respond(f"{saludo}{nombre}. Soy el asistente virtual de la tienda. Puedes preguntarme precios, productos disponibles o información de la tienda.", role)
        elif role == 'vendedor':
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            if d and d['t'] > 0:
                return self._respond(f"{saludo}{nombre}. Hoy llevamos {d['t']} ventas por ${d['r']:,.0f}. ¿Necesitas algo más?", role)
            return self._respond(f"{saludo}{nombre}. Aún no hay ventas hoy. ¿En qué te ayudo?", role)
        else:
            stats = ProductSearch.stats()
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            rev = d['r'] if d else 0
            return self._respond(f"{saludo}{nombre}. Tenemos {stats['total']} productos, {stats['low']} con stock bajo. Ventas hoy: ${rev:,.0f}. ¿Qué necesitas?", role)
    
    def _help(self, role):
        if role == 'cliente':
            return self._respond("Puedo mostrarte nuestros productos y precios. Solo dime qué buscas, por ejemplo: ¿cuánto cuesta el café? o ¿tienen leche?", role)
        elif role == 'vendedor':
            return self._respond("Puedo ayudarte con: ventas de hoy, consultar precios, ver stock bajo, productos más vendidos. Dime qué necesitas.", role)
        else:
            return self._respond("Tienes acceso completo. Puedes consultar: ventas, inventario, stock crítico, predicciones, KPIs, reportes. Dime qué necesitas.", role)
    
    def _handle_cliente(self, text, text_lower):
        # Buscar producto
        prods = ProductSearch.search(text, 5)
        if prods:
            if len(prods) == 1:
                p = prods[0]
                msg = f"{p['n']} cuesta ${p['p']:,.0f} por {p['u']}."
                if p['s'] == 0:
                    msg += f" Lamentablemente está agotado en este momento."
                elif p['s'] <= 5:
                    msg += f" Quedan pocas unidades."
                else:
                    msg += f" Tenemos {p['s']:.0f} {p['u']} disponibles."
                # Productos relacionados
                related = [r for r in ProductSearch.search(p['cat'], 4) if r['n'] != p['n']]
                if related:
                    msg += f" También tenemos {related[0]['n']} a ${related[0]['p']:,.0f} y {related[1]['n'] if len(related)>1 else ''}."
                    if len(related)>1: msg = msg.replace(" y .", ".")
            else:
                msg = f"Tenemos {len(prods)} productos que coinciden: "
                msg += ", ".join([f"{p['n']} (${p['p']:,.0f})" for p in prods[:5]])
                msg += ". ¿Cuál te interesa?"
            return self._respond(msg, 'cliente')
        
        # Categorías
        cats = ProductSearch.categorias
        if any(w in text_lower for w in ['categorias','catalogo','que tienen','que venden','productos']):
            return self._respond(f"Trabajamos con {len(cats)} categorías: {', '.join(cats[:8])}. ¿Qué categoría te interesa?", 'cliente')
        
        return self._respond("Cuéntame qué producto buscas y te digo el precio y disponibilidad.", 'cliente')
    
    def _handle_vendedor(self, text, text_lower):
        # Ventas
        if any(w in text_lower for w in ['ventas','caja','recaude','facture','reporte']):
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r, COALESCE(AVG(total),0) as a FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            if d and d['t'] > 0:
                return self._respond(f"Hoy llevas {d['t']} ventas, ${d['r']:,.0f} recaudados. Ticket promedio: ${d['a']:,.0f}.", 'vendedor')
            return self._respond("Aún no hay ventas registradas hoy.", 'vendedor')
        
        # Stock bajo
        if any(w in text_lower for w in ['stock bajo','agotado','critico','poco stock','reabastecer']):
            rows = DB.q("SELECT nombre,stock_actual,precio_venta FROM inventario_general WHERE stock_actual<=5 ORDER BY stock_actual LIMIT 6")
            if not rows: rows = DB.q("SELECT nombre,stock_actual,precio FROM productos WHERE stock_actual<=5 ORDER BY stock_actual LIMIT 6")
            if rows:
                msg = "Productos con stock bajo: "
                msg += "; ".join([f"{r['nombre']} ({r['stock_actual']:.0f}uds)" for r in rows])
                return self._respond(msg, 'vendedor')
            return self._respond("No hay productos con stock bajo. Todo en orden.", 'vendedor')
        
        # Top productos
        if any(w in text_lower for w in ['top','mas vendido','popular','ranking']):
            rows = DB.q("SELECT nombre,SUM(cantidad) q FROM historial_ventas WHERE fecha>=DATE('now','-7 days') GROUP BY nombre ORDER BY q DESC LIMIT 5")
            if rows:
                msg = "Lo más vendido esta semana: "
                msg += ", ".join([f"{r['nombre']} ({r['q']:.0f}uds)" for r in rows])
                return self._respond(msg, 'vendedor')
            return self._respond("Aún no hay datos de ventas esta semana.", 'vendedor')
        
        # Buscar producto
        prods = ProductSearch.search(text, 5)
        if prods:
            if len(prods) == 1:
                p = prods[0]
                msg = f"{p['n']}: ${p['p']:,.0f} - Stock: {p['s']:.0f} {p['u']}"
                if p['c'] > 0 and p['p'] > 0:
                    margen = ((p['p']-p['c'])/p['p'])*100
                    msg += f" - Margen: {margen:.1f}%"
            else:
                msg = f"Encontré {len(prods)}: "
                msg += "; ".join([f"{p['n']} ${p['p']:,.0f}" for p in prods[:5]])
            return self._respond(msg, 'vendedor')
        
        return self._respond("Dime un producto para ver su precio y stock, o consulta 'ventas', 'stock bajo' o 'top productos'.", 'vendedor')
    
    def _handle_admin(self, text, text_lower, role):
        # Ventas
        if any(w in text_lower for w in ['ventas','caja','recaude','reporte']):
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r, COALESCE(AVG(total),0) as a FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            if d and d['t'] > 0:
                return self._respond(f"Ventas de hoy: {d['t']} transacciones, ${d['r']:,.0f} ingresos. Ticket promedio ${d['a']:,.0f}.", role)
            return self._respond("Sin ventas hoy.", role)
        
        # Stock / Inventario
        if any(w in text_lower for w in ['stock','inventario','agotado']):
            stats = ProductSearch.stats()
            rows = DB.q("SELECT nombre,stock_actual FROM inventario_general WHERE stock_actual<=5 ORDER BY stock_actual LIMIT 8")
            msg = f"Inventario: {stats['total']} productos, {stats['low']} con stock bajo."
            if rows:
                msg += " Críticos: " + ", ".join([f"{r['nombre']}({r['stock_actual']:.0f})" for r in rows[:5]])
            return self._respond(msg, role)
        
        # KPIs / Dashboard
        if any(w in text_lower for w in ['kpi','dashboard','metrica','indicador','estado']):
            stats = ProductSearch.stats()
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            msg = f"Estado del sistema: {stats['total']} productos activos, {stats['low']} con stock bajo. "
            msg += f"Ventas hoy: {d['t']} transacciones, ${d['r']:,.0f}." if d else "Sin ventas hoy."
            return self._respond(msg, role)
        
        # Predicciones
        if any(w in text_lower for w in ['prediccion','pronostico','proyeccion']):
            d = DB.q("SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            rev = d['r'] if d else 0
            return self._respond(f"Proyección semanal estimada: ${rev*7:,.0f} basado en el ritmo actual de ventas.", role)
        
        # Buscar producto
        prods = ProductSearch.search(text, 5)
        if prods:
            if len(prods) == 1:
                p = prods[0]
                msg = f"{p['n']}: ${p['p']:,.0f} - Stock {p['s']:.0f} {p['u']} - {p['cat']}"
                if p['c'] > 0: msg += f" - Margen {((p['p']-p['c'])/p['p']*100):.1f}%"
            else:
                msg = f"Resultados: " + "; ".join([f"{p['n']} ${p['p']:,.0f}" for p in prods[:5]])
            return self._respond(msg, role)
        
        return self._respond("Puedes consultar: ventas, inventario, KPIs, predicciones o buscar un producto específico.", role)
    
    def _respond(self, msg, role):
        return {'answer': msg, 'role': role, 'suggestions': [], 'ts': datetime.now().isoformat()}

_agent = None
_lock = threading.Lock()

def _get():
    global _agent
    if not _agent:
        with _lock:
            if not _agent: _agent = Agent()
    return _agent

def process_question(sid, question, role='cliente', user_name=''):
    r = _get().process(question, sid, role, user_name)
    return {
        'answer': r['answer'],
        'intent': 'chat',
        'suggestions': [],
        'role': role,
        'role_label': ROLES.get(role, {}).get('label', 'Usuario'),
        'role_color': ROLES.get(role, {}).get('color', '#3498db'),
        'role_icon': ROLES.get(role, {}).get('icon', '?'),
        'ts': r['ts']
    }

def get_status():
    s = ProductSearch.stats()
    return {'version':'1.0.0','model':'Asistente Virtual Natural','status':'active','stats':s}

def get_conversation_history(sid='default'):
    return []

def get_proactive_alerts(sid='default'):
    return {'alerts': []}

def set_session_role(sid, role, name=''): return role
def get_session_info(sid): return {'role':'cliente','role_label':'Cliente','role_color':'#2ecc71','role_icon':'C'}

ROLES = {
    'vendedor': {'label': 'Vendedor', 'color': '#3498db', 'icon': 'V'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'supervisor': {'label': 'Supervisor', 'color': '#f39c12', 'icon': 'S'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
    'cliente': {'label': 'Cliente', 'color': '#2ecc71', 'icon': 'C'}
}

print("🚀 ia_agent.py v1.0 - Asistente natural por roles")
