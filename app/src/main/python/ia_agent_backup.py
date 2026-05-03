"""
ia_agent.py v1.0 - TPV Smart - Agente IA Dinámico
100% On-Device | NLP Engine | Memoria Conversacional
"""
import sqlite3, json, math, re, os, random, threading, time
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher

IS_ANDROID = False

def _db_path():
    paths = ['tpv_datos.db', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')]
    for p in paths:
        if os.path.exists(p): return p
    return 'tpv_datos.db'

class NLP:
    STOP = {'de','del','la','el','los','las','en','con','y','a','un','una','por','para','al','que','es','se','su','lo','no','si','mi','tu','mas','muy','ya','o','e','u'}
    INTENTS = {
        'greeting': ['hola','buenos dias','buenas tardes','hey','que tal','saludos'],
        'search_product': ['cuanto cuesta','precio de','busco','necesito','hay stock','tienen','donde encuentro','dame','quiero','vendeme'],
        'sales': ['ventas','cuanto vendi','recaude','facture','caja','reporte','ingresos'],
        'inventory': ['stock','inventario','quedan','agotado','reabastecer','faltante'],
        'predictions': ['prediccion','pronostico','tendencia','preveer','estimacion','proyeccion'],
        'kpi': ['kpis','indicadores','metricas','dashboard','analisis','rendimiento'],
        'top': ['top','mas vendido','productos populares','best seller','ranking'],
        'recommendations': ['recomienda','sugerencia','que hacer','optimizar','mejorar'],
        'help': ['ayuda','help','que puedes','como funciona','capacidades'],
        'farewell': ['adios','chao','bye','hasta luego','nos vemos']
    }
    
    @classmethod
    def tokenize(cls, text):
        text = re.sub(r'[áàäâ]','a',re.sub(r'[éèëê]','e',re.sub(r'[íìïî]','i',re.sub(r'[óòöô]','o',re.sub(r'[úùüû]','u',text.lower())))))
        return [t for t in re.findall(r'\b\w+\b', text) if t not in cls.STOP and len(t)>1]
    
    @classmethod
    def classify(cls, text):
        tokens = set(cls.tokenize(text))
        best, best_score = 'search_product', 0
        for intent, examples in cls.INTENTS.items():
            score = sum(1 for ex in examples if any(w in text.lower() for w in ex.split()))
            if score > best_score: best, best_score = intent, score
        # Si menciona un producto, es búsqueda
        if best_score == 0: best = 'search_product'
        return best, min(best_score/3, 1.0)

class Memory:
    def __init__(self):
        self.turns = []; self.context = {}; self.last_intent = None; self.prefs = defaultdict(int)
    def add(self, q, intent, r):
        self.turns.append({'q':q,'intent':intent,'r':r[:100]})
        if len(self.turns)>15: self.turns=self.turns[-15:]
        self.last_intent=intent; self.prefs[intent]+=1

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
    cache = []; cache_t = 0
    
    @classmethod
    def refresh(cls):
        if cls.cache and time.time()-cls.cache_t < 15: return
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
                        if len(nw)>=3 and SequenceMatcher(None,w,nw).ratio()>0.75: s += 20
            if p['s'] > 0: s += 3
            if s > 0: scored.append((s, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored[:limit]]
    
    @classmethod
    def stats(cls):
        cls.refresh()
        return {'total':len(cls.cache),'low':sum(1 for p in cls.cache if 0<p['s']<=5),'out':sum(1 for p in cls.cache if p['s']<=0)}

class R:
    @staticmethod
    def greeting(name=''):
        h = datetime.now().hour
        g = "Buenas noches" if h<6 else "Buenos días" if h<12 else "Buenas tardes" if h<20 else "Buenas noches"
        return f"{g}, {name}! Soy tu asistente TPV. Dime un producto y te doy precio, stock y más." if name else f"{g}! Dime un producto y te muestro todo: precio, stock, margen y recomendaciones."

    @staticmethod
    def product_card(p, related=None):
        """Tarjeta de producto DINÁMICA con toda la info"""
        nombre = p['n']; precio = p['p']; stock = p['s']; unidad = p['u']; cat = p['cat']; costo = p['c']
        
        msg = f"📦 *{nombre}*\n"
        msg += f"━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 *Precio:* ${precio:,.0f} / {unidad}\n"
        
        # Stock con icono
        if stock == 0:
            msg += f"📊 *Stock:* ❌ AGOTADO\n"
        elif stock <= 3:
            msg += f"📊 *Stock:* ⚠️ {stock:.0f} {unidad} (¡CRÍTICO!)\n"
        elif stock <= 10:
            msg += f"📊 *Stock:* 🟡 {stock:.0f} {unidad} (bajo)\n"
        else:
            msg += f"📊 *Stock:* 🟢 {stock:.0f} {unidad}\n"
        
        msg += f"🏷️ *Categoría:* {cat}\n"
        
        # Margen de ganancia
        if precio > 0 and costo > 0:
            margen = ((precio - costo) / precio) * 100
            ganancia = precio - costo
            msg += f"📈 *Margen:* {margen:.1f}%\n"
            msg += f"💵 *Ganancia/unidad:* ${ganancia:,.0f}\n"
        
        # Valor total del inventario
        if stock > 0:
            valor_total = precio * stock
            msg += f"💎 *Valor en stock:* ${valor_total:,.0f}\n"
        
        # Precio por mayor (sugerencia automática)
        if stock >= 10:
            precio_mayor = precio * 0.9
            msg += f"\n💡 *Al por mayor (10+):* ${precio_mayor:,.0f} c/u (10% desc)\n"
        
        # Productos relacionados
        if related:
            msg += f"\n📦 *También te puede interesar:*\n"
            for r in related[:3]:
                msg += f"  • {r['n']} - ${r['p']:,.0f}\n"
        
        # Alerta de reorden
        if stock <= 5 and stock > 0:
            msg += f"\n⚠️ *Recomendación:* Reordenar este producto pronto."
        
        return msg

    @staticmethod
    def product_list(prods, query):
        if not prods:
            # Buscar sugerencias
            sugerencias = ProductSearch.search(query[:3], 3) if len(query)>=3 else []
            if sugerencias:
                msg = f"❌ No encontré '{query}'.\n\n📦 *Productos similares:*\n"
                for s in sugerencias:
                    msg += f"  • {s['n']} - ${s['p']:,.0f}\n"
                return msg
            return f"❌ No encontré '{query}'.\n\n💡 Prueba con: café, leche, pan, gaseosa, arroz, azúcar"
        
        if len(prods) == 1:
            # Producto único: tarjeta completa con relacionados
            related = ProductSearch.search(prods[0]['cat'], 4)
            related = [r for r in related if r['n'] != prods[0]['n']]
            return R.product_card(prods[0], related)
        
        # Lista múltiple con precios
        msg = f"🔍 *{len(prods)} productos* para '{query}':\n"
        msg += f"━━━━━━━━━━━━━━━━━━\n"
        for p in prods:
            icon = "🟢" if p['s']>10 else "🟡" if p['s']>0 else "🔴"
            msg += f"\n{icon} *{p['n']}*\n"
            msg += f"   💰 ${p['p']:,.0f} | 📦 {p['s']:.0f}{p['u']} | 🏷️ {p['cat']}\n"
        msg += f"\n💡 Escribe el nombre exacto para ver todos los detalles."
        return msg

    @staticmethod
    def sales_dashboard(d):
        if not d or d.get('txns',0)==0:
            return "📊 Aún no hay ventas hoy.\n\n💡 Pregúntame por un producto: 'precio del café'"
        return f"📊 *Ventas Hoy*\n━━━━━━━━━━━━━━━━━━\n🛒 {d['txns']} ventas\n💰 ${d['rev']:,.0f}\n📈 Ticket prom: ${d['avg']:,.0f}\n📦 {d['units']} unidades\n\n💡 'top productos' para ver los más vendidos"

    @staticmethod
    def inventory_alert(prods):
        if not prods: return "✅ Todos los productos tienen stock normal.\n\n💡 'precio de [producto]' para consultar."
        msg = "⚠️ *Stock Bajo*\n━━━━━━━━━━━━━━━━━━\n"
        for p in prods[:8]: msg += f"• {p['n']} - {p['s']:.0f} {p.get('u','Un')} | ${p.get('p',0):,.0f}\n"
        return msg

    @staticmethod
    def help_menu():
        return """🤖 *TPV Smart v1.0*

📦 *Productos:*
  • "precio del café"
  • "¿hay leche?"
  • Solo escribe el nombre

💰 *Ventas:*
  • "ventas de hoy"
  • "top productos"

📊 *Inventario:*
  • "stock bajo"
  • "¿qué hay?"

🔮 *Predicciones y más:*
  • "recomendaciones"
  • "predicciones"

✨ Escribe en lenguaje natural!"""

class Agent:
    def __init__(self):
        self.memories = {}; self.lock = threading.Lock()
        print("✅ Agente IA v1.0 dinámico listo")
    
    def mem(self, sid):
        with self.lock:
            if sid not in self.memories: self.memories[sid] = Memory()
            return self.memories[sid]
    
    def process(self, text, sid='default', role='vendedor', name=''):
        if not text or not text.strip(): return self._fmt("Dime un producto o pregunta. Ej: 'café', 'ventas de hoy', 'stock bajo'", 'help')
        
        mem = self.mem(sid)
        intent, conf = NLP.classify(text)
        
        # SIEMPRE intentar buscar productos primero (respuesta dinámica)
        prods = ProductSearch.search(text, 8)
        
        if intent == 'greeting':
            ans = R.greeting(name); sug = ['café','ventas de hoy','stock bajo','precio del pan']
        
        elif intent == 'search_product' or (prods and len(prods) > 0):
            ans = R.product_list(prods, text)
            sug = ['ventas de hoy','stock bajo','recomendaciones'] + [p['n'] for p in prods[:2]]
        
        elif intent in ['sales','kpi']:
            d = DB.q("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r, COALESCE(AVG(total),0) as a, COALESCE(SUM(cantidad),0) as u FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            data = {'txns':d['t'],'rev':d['r'],'avg':d['a'],'units':int(d['u'])} if d else None
            ans = R.sales_dashboard(data); sug = ['top productos','stock bajo','predicciones']
        
        elif intent == 'top':
            rows = DB.q("SELECT nombre,SUM(cantidad) q,SUM(total) t FROM historial_ventas WHERE fecha>=DATE('now','-7 days') GROUP BY nombre ORDER BY q DESC LIMIT 5")
            if rows:
                ans = "🏆 *Top 5 Semana*\n━━━━━━━━━━━━━━━━━━\n"+"\n".join([f"{i}. *{r['nombre']}* - {r['q']:.0f}uds ${r['t']:,.0f}" for i,r in enumerate(rows,1)])
            else: ans = "No hay datos. ¡Empieza a vender!"
            sug = ['ventas de hoy','stock bajo']
        
        elif intent == 'inventory':
            rows = DB.q("SELECT nombre,stock_actual,unidad_medida,precio_venta FROM inventario_general WHERE stock_actual<=10 ORDER BY stock_actual LIMIT 10")
            if not rows: rows = DB.q("SELECT nombre,stock_actual,unidad_medida,precio FROM productos WHERE stock_actual<=10 ORDER BY stock_actual LIMIT 10")
            prods_inv = [{'n':r['nombre'],'s':r['stock_actual'],'u':r['unidad_medida'] or 'Un','p':r[3] if len(r)>3 else 0} for r in rows] if rows else []
            ans = R.inventory_alert(prods_inv); sug = ['reabastecer','ventas de hoy']
        
        elif intent == 'predictions':
            d = DB.q("SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            rev = d['r'] if d else 0
            ans = f"🔮 *Predicciones*\n━━━━━━━━━━━━━━━━━━\n📈 Proyección semanal: ${rev*7:,.0f}\n📊 Basado en ritmo actual"
            stats = ProductSearch.stats()
            if stats['low']>0: ans += f"\n⚠️ {stats['low']} productos necesitan stock"
            sug = ['ventas de hoy','stock bajo','top productos']
        
        elif intent == 'recommendations':
            low = DB.q("SELECT nombre,stock_actual,precio_venta FROM inventario_general WHERE stock_actual<=5 LIMIT 5")
            ans = "💡 *Recomendaciones*\n━━━━━━━━━━━━━━━━━━\n"
            if low:
                ans += "📦 *Reabastecer:*\n"+"\n".join([f"  • {r['nombre']} ({r['stock_actual']:.0f}uds) - ${r['precio_venta']:,.0f}" for r in low])
            else: ans += "✅ Inventario en orden."
            ans += "\n\n💡 También puedes preguntar: 'precio de [producto]'"
            sug = ['ventas de hoy','stock bajo','predicciones']
        
        elif intent == 'help':
            ans = R.help_menu(); sug = ['café','ventas de hoy','stock bajo','precio del pan']
        
        elif intent == 'farewell':
            ans = "¡Hasta luego! Cuando quieras consultar precios, aquí estoy. 👋"; sug = []
        
        else:
            ans = R.help_menu(); sug = ['café','ventas de hoy','stock bajo']
        
        mem.add(text, intent, ans)
        return self._fmt(ans, intent, sug)
    
    def _fmt(self, ans, intent, sug=None):
        return {'answer':ans,'intent':intent,'suggestions':sug or [],'ts':datetime.now().isoformat()}
    
    def alerts(self):
        a = []
        low = DB.q("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual<=3")
        if low and low[0]['c']>0: a.append({'type':'critical','icon':'🔴','msg':f'{low[0]["c"]} productos críticos'})
        return a

_agent = None
_lock = threading.Lock()

def _get():
    global _agent
    if not _agent:
        with _lock:
            if not _agent: _agent = Agent()
    return _agent

def process_question(sid, question, role='vendedor', user_name=''):
    r = _get().process(question, sid, role, user_name)
    return {'answer':r['answer'],'intent':r['intent'],'suggestions':r['suggestions'],'role':role,'role_label':ROLES.get(role,{}).get('label','Usuario'),'role_color':ROLES.get(role,{}).get('color','#3498db'),'role_icon':ROLES.get(role,{}).get('icon','?'),'ts':r['ts']}

def get_status():
    s = ProductSearch.stats()
    return {'version':'1.0.0','model':'NLP Dinámico + Fuzzy Search + Memory','status':'active','features':['Precios automáticos','Sugerencias relacionadas','Stock en tiempo real','Margen de ganancia','Precio por mayor'],'stats':s}

def get_conversation_history(sid='default'):
    return [{'user':t['q'],'intent':t['intent'],'response':t['r'],'ts':''} for t in _get().mem(sid).turns[-10:]]

def get_proactive_alerts(sid='default'):
    return {'alerts':_get().alerts()}

def set_session_role(sid, role, name=''): return role
def get_session_info(sid): return {'role':'vendedor','role_label':'Vendedor','role_color':'#3498db','role_icon':'V'}

ROLES = {'vendedor':{'label':'Vendedor','color':'#3498db','icon':'V'},'administrador':{'label':'Administrador','color':'#e74c3c','icon':'A'},'supervisor':{'label':'Supervisor','color':'#f39c12','icon':'S'},'desarrollador':{'label':'Desarrollador','color':'#9b59b6','icon':'D'},'cliente':{'label':'Cliente','color':'#2ecc71','icon':'C'}}

print("🚀 ia_agent.py v1.0 dinámico cargado")
