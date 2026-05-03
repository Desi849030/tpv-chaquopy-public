"""
ia_agent.py v1.0 - TPV Smart - Agente IA Profesional
100% On-Device | NLP Engine | Memoria Conversacional
Compatible con ia_assistant_routes.py
"""
import sqlite3, json, math, re, os, random, threading, time
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher

# ── Detección de entorno ──
IS_ANDROID = False
try:
    import sys
    IS_ANDROID = hasattr(sys, 'getandroidapilevel')
except: pass

# ── Ruta de base de datos ──
def _db_path():
    paths = [
        'tpv_datos.db',
        os.path.join(os.environ.get('TPV_FILES_DIR', ''), 'tpv_datos.db'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')
    ]
    for p in paths:
        if p and os.path.exists(p):
            return p
    return 'tpv_datos.db'

# ── NLP Engine ──
class NLP:
    STOP = {'de','del','la','el','los','las','en','con','y','a','un','una',
            'por','para','al','que','es','se','su','lo','no','si','mi','tu',
            'mas','muy','ya','o','e','u'}
    
    INTENTS = {
        'greeting': ['hola','buenos dias','buenas tardes','hey','que tal','saludos','buen dia'],
        'search_product': ['cuanto cuesta','precio de','busco','necesito','hay stock','tienen','donde encuentro'],
        'sales': ['ventas','cuanto vendi','recaude','facture','caja','reporte','ingresos'],
        'inventory': ['stock','inventario','quedan','agotado','reabastecer','faltante','disponible'],
        'predictions': ['prediccion','pronostico','tendencia','preveer','estimacion','proyeccion'],
        'kpi': ['kpis','indicadores','metricas','dashboard','analisis','rendimiento','estadisticas'],
        'top': ['top','mas vendido','productos populares','best seller','ranking','lider'],
        'recommendations': ['recomienda','sugerencia','que hacer','optimizar','mejorar','consejo'],
        'help': ['ayuda','help','que puedes','como funciona','capacidades','funcionalidades'],
        'farewell': ['adios','chao','bye','hasta luego','nos vemos','me voy']
    }
    
    @classmethod
    def tokenize(cls, text):
        text = text.lower().strip()
        text = re.sub(r'[áàäâ]','a',text)
        text = re.sub(r'[éèëê]','e',text)
        text = re.sub(r'[íìïî]','i',text)
        text = re.sub(r'[óòöô]','o',text)
        text = re.sub(r'[úùüû]','u',text)
        tokens = re.findall(r'\b\w+\b', text)
        return [t for t in tokens if t not in cls.STOP and len(t)>1]
    
    @classmethod
    def classify(cls, text):
        text_lower = text.lower()
        best, best_score = 'unknown', 0
        
        for intent, examples in cls.INTENTS.items():
            score = 0
            for ex in examples:
                if ex in text_lower:
                    score += 1
            if score > best_score:
                best, best_score = intent, score
        
        return best, min(best_score/3.0, 1.0)
    
    @classmethod
    def extract_product(cls, text):
        patterns = [
            r'(?:cuanto\s+(?:cuesta|vale|es|esta))\s+(?:el|la|los|las|un|una)?\s*(.+?)(?:\?|$)',
            r'(?:busco|necesito|quiero|hay\s+stock\s+de|tienen?)\s+(?:el|la|los|las|un|una)?\s*(.+?)(?:\?|$)',
            r'(?:precio|stock|info)\s+(?:de(?:l|la)?\s+)?(.+?)(?:\?|$)',
            r'^(.+?)(?:\s+(?:cuanto|precio|stock|vale|cuesta))',
        ]
        for pat in patterns:
            m = re.search(pat, text.lower().strip())
            if m:
                name = m.group(1).strip()
                name = re.sub(r'^(el|la|los|las|un|una)\s+', '', name)
                if len(name) >= 2:
                    return name
        return text

# ── Memoria conversacional ──
class Memory:
    def __init__(self):
        self.turns = []
        self.context = {}
        self.last_intent = None
        self.prefs = defaultdict(int)
    
    def add(self, question, intent, response):
        self.turns.append({
            'q': question,
            'intent': intent,
            'r': response[:100]
        })
        if len(self.turns) > 15:
            self.turns = self.turns[-15:]
        self.last_intent = intent
        self.prefs[intent] += 1
    
    def is_followup(self, text):
        if not self.turns:
            return False
        if len(text.split()) <= 3:
            return True
        if any(text.lower().startswith(w) for w in ['y ','tambien ','ademas ','entonces ','y cuanto ']):
            return True
        return False

# ── Conexión a base de datos ──
class DB:
    _conn = None
    
    @classmethod
    def get(cls):
        try:
            if cls._conn:
                cls._conn.execute("SELECT 1")
                return cls._conn
        except:
            pass
        
        path = _db_path()
        if os.path.exists(path):
            try:
                cls._conn = sqlite3.connect(path, timeout=3, check_same_thread=False)
                cls._conn.row_factory = sqlite3.Row
                cls._conn.execute("PRAGMA journal_mode=WAL")
                return cls._conn
            except:
                pass
        return None
    
    @classmethod
    def query(cls, sql, params=(), one=False):
        conn = cls.get()
        if not conn:
            return None
        try:
            cur = conn.execute(sql, params)
            return cur.fetchone() if one else cur.fetchall()
        except:
            return None

# ── Buscador de productos ──
class ProductSearch:
    cache = []
    cache_time = 0
    
    @classmethod
    def refresh(cls):
        if cls.cache and time.time() - cls.cache_time < 20:
            return
        
        conn = DB.get()
        if not conn:
            return
        
        products = []
        try:
            rows = conn.execute("""
                SELECT nombre, precio, costo, categoria, 
                       stock_actual, unidad_medida
                FROM productos WHERE activo=1
                ORDER BY nombre
            """).fetchall()
            
            for r in rows:
                products.append({
                    'n': r[0] or '',
                    'p': float(r[1] or 0),
                    'c': float(r[2] or 0),
                    'cat': r[3] or 'General',
                    's': float(r[4] or 0),
                    'u': r[5] or 'Un'
                })
            
            existing_names = {p['n'].lower() for p in products}
            
            rows2 = conn.execute("""
                SELECT nombre, precio_venta, precio_compra, categoria,
                       stock_actual, unidad_medida
                FROM inventario_general
                ORDER BY nombre
            """).fetchall()
            
            for r in rows2:
                name = (r[0] or '').lower()
                if name not in existing_names:
                    products.append({
                        'n': r[0] or '',
                        'p': float(r[1] or 0),
                        'c': float(r[2] or 0),
                        'cat': r[3] or 'General',
                        's': float(r[4] or 0),
                        'u': r[5] or 'Un'
                    })
            
            cls.cache = products
            cls.cache_time = time.time()
        except:
            pass
    
    @classmethod
    def search(cls, query, limit=8):
        cls.refresh()
        q = query.lower().strip()
        
        if len(q) < 2:
            return []
        
        scored = []
        for p in cls.cache:
            score = 0
            nl = p['n'].lower()
            
            if q == nl:
                score = 100
            elif q in nl:
                score = 85
            elif nl in q:
                score = 75
            else:
                for word in q.split():
                    if len(word) < 2:
                        continue
                    if word in nl:
                        score += 30
                    elif word in p['cat'].lower():
                        score += 15
                    for nw in nl.split():
                        if len(nw) >= 3:
                            sim = SequenceMatcher(None, word, nw).ratio()
                            if sim > 0.7:
                                score += int(sim * 20)
            
            if p['s'] > 0:
                score += 3
            if 0 < p['s'] <= 3:
                score -= 5
            
            if score > 0:
                scored.append((score, p))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
    
    @classmethod
    def stats(cls):
        cls.refresh()
        total = len(cls.cache)
        low = sum(1 for p in cls.cache if 0 < p['s'] <= 5)
        out = sum(1 for p in cls.cache if p['s'] <= 0)
        value = sum(p['p'] * p['s'] for p in cls.cache if p['s'] > 0)
        return {
            'total_products': total,
            'low_stock': low,
            'out_stock': out,
            'inventory_value': value
        }

# ── Generador de respuestas ──
class R:
    @staticmethod
    def time_greeting():
        h = datetime.now().hour
        if h < 6: return "🌙 Buenas noches"
        if h < 12: return "☀️ Buenos días"
        if h < 14: return "🌤️ Buen mediodía"
        if h < 20: return "🌅 Buenas tardes"
        return "🌆 Buenas noches"
    
    @staticmethod
    def greeting(name=''):
        g = R.time_greeting()
        if name:
            return f"{g}, {name}! ¿En qué puedo ayudarte hoy?"
        return f"{g}! Soy tu asistente TPV Smart. ¿Qué necesitas?"
    
    @staticmethod
    def product_card(p):
        nombre = p['n']
        precio = p['p']
        stock = p['s']
        unidad = p['u']
        categoria = p['cat']
        costo = p['c']
        
        msg = f"📦 *{nombre}*\n\n"
        msg += f"💰 Precio: ${precio:,.0f} / {unidad}\n"
        msg += f"📊 Stock: {stock:.0f} {unidad}\n"
        msg += f"🏷️ Categoría: {categoria}\n"
        
        if precio > 0 and costo > 0:
            margen = ((precio - costo) / precio) * 100
            msg += f"📈 Margen: {margen:.1f}%\n"
        
        if stock == 0:
            msg += "\n❌ *AGOTADO* - Sin stock"
        elif stock <= 3:
            msg += f"\n⚠️ *CRÍTICO* - Solo {stock:.0f} {unidad}"
        elif stock <= 10:
            msg += f"\n📊 Stock bajo - {stock:.0f} {unidad}"
        
        if stock > 0 and precio > 0:
            valor = precio * stock
            if valor > 1000:
                msg += f"\n💎 Valor en stock: ${valor:,.0f}"
        
        return msg
    
    @staticmethod
    def product_list(products, query):
        if not products:
            return f"❌ No encontré '{query}'.\n\nPrueba con otro nombre o categoría."
        
        if len(products) == 1:
            return R.product_card(products[0])
        
        msg = f"🔍 Encontré *{len(products)} productos* para '*{query}*':\n"
        
        for p in products[:6]:
            if p['s'] > 10:
                icon = "🟢"
            elif p['s'] > 0:
                icon = "🟡"
            else:
                icon = "🔴"
            msg += f"\n{icon} *{p['n']}* - ${p['p']:,.0f}\n"
            msg += f"   └─ {p['s']:.0f} {p['u']} | {p['cat']}\n"
        
        if len(products) > 6:
            msg += f"\n... y {len(products) - 6} más.\n"
        
        msg += "\n💡 Escribe el nombre exacto para más detalles."
        return msg
    
    @staticmethod
    def sales_dashboard(data):
        if not data or data.get('txns', 0) == 0:
            return "📊 Aún no hay ventas registradas hoy.\n\n¿Quieres registrar una venta o ver el inventario?"
        
        txns = data.get('txns', 0)
        rev = data.get('rev', 0)
        avg = data.get('avg', 0)
        units = data.get('units', 0)
        
        if rev > 5000:
            emoji, status = "🟢", "¡Excelente día!"
        elif rev > 2000:
            emoji, status = "🟡", "Buen ritmo de ventas"
        elif rev > 500:
            emoji, status = "🟠", "Ventas moderadas"
        else:
            emoji, status = "🔵", "Día tranquilo"
        
        msg = f"📊 *Dashboard de Ventas - Hoy*\n\n"
        msg += f"{emoji} {status}\n\n"
        msg += f"🛒 Transacciones: *{txns}*\n"
        msg += f"💰 Ingresos totales: *${rev:,.0f}*\n"
        msg += f"📈 Ticket promedio: *${avg:,.0f}*\n"
        msg += f"📦 Unidades vendidas: *{units:.0f}*\n"
        
        h = datetime.now().hour
        if h > 0 and rev > 0:
            proy = (rev / h) * 24
            msg += f"\n🔮 Proyección del día: *${proy:,.0f}*\n"
        
        return msg
    
    @staticmethod
    def inventory_alert(products):
        if not products:
            return "✅ Todo en orden - no hay productos con stock bajo."
        
        critical = [p for p in products if p['s'] <= 3]
        warning = [p for p in products if 3 < p['s'] <= 10]
        
        msg = "⚠️ *Alerta de Inventario*\n\n"
        
        if critical:
            msg += f"🔴 *CRÍTICO* ({len(critical)}):\n"
            for p in critical[:5]:
                msg += f"  • {p['n']} - {p['s']:.0f} {p.get('u','Un')}\n"
            msg += "\n"
        
        if warning:
            msg += f"🟡 *BAJO* ({len(warning)}):\n"
            for p in warning[:5]:
                msg += f"  • {p['n']} - {p['s']:.0f} {p.get('u','Un')}\n"
            msg += "\n"
        
        msg += "💡 Recomiendo reabastecer los productos críticos pronto."
        return msg
    
    @staticmethod
    def help_menu():
        msg = "🤖 *Asistente TPV Smart v1.0*\n\n"
        msg += "*Puedes preguntarme:*\n\n"
        msg += "📦 *Productos*\n  • ¿Cuánto cuesta [producto]?\n  • ¿Hay stock de [producto]?\n  • Buscar [nombre/categoría]\n\n"
        msg += "💰 *Ventas*\n  • ¿Cómo van las ventas hoy?\n  • Ventas de la semana\n  • Top productos más vendidos\n\n"
        msg += "📊 *Inventario*\n  • ¿Qué stock tengo?\n  • Productos agotados\n  • Stock bajo o crítico\n\n"
        msg += "📈 *Análisis*\n  • Dame los KPIs del día\n  • Predicciones de venta\n  • Recomendaciones inteligentes\n\n"
        msg += "*Escribe en lenguaje natural, sin comandos.*"
        return msg

# ── Agente principal ──
class Agent:
    def __init__(self):
        self.memories = {}
        self.lock = threading.Lock()
        print("✅ Agente IA v1.0 inicializado")
    
    def _mem(self, sid):
        with self.lock:
            if sid not in self.memories:
                self.memories[sid] = Memory()
            return self.memories[sid]
    
    def process(self, text, sid='default', role='vendedor', user_name=''):
        if not text or not text.strip():
            return self._fmt("Dime qué necesitas saber.", 'help')
        
        mem = self._mem(sid)
        intent, confidence = NLP.classify(text)
        
        if mem.is_followup(text) and mem.last_intent and confidence < 0.3:
            intent = mem.last_intent
        
        if intent == 'greeting':
            ans = R.greeting(user_name)
            sug = ['ventas de hoy', 'stock bajo', 'buscar producto']
        
        elif intent == 'search_product':
            pname = NLP.extract_product(text)
            prods = ProductSearch.search(pname)
            ans = R.product_list(prods, pname)
            sug = ['ventas de hoy', 'stock bajo', 'otro producto']
        
        elif intent in ('sales', 'kpi'):
            d = DB.query("""
                SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r,
                       COALESCE(AVG(total),0) as a, COALESCE(SUM(cantidad),0) as u
                FROM historial_ventas
                WHERE DATE(fecha)=DATE('now','localtime')
            """, one=True)
            data = {'txns': d['t'], 'rev': d['r'], 'avg': d['a'], 'units': int(d['u'])} if d else None
            ans = R.sales_dashboard(data)
            sug = ['top productos', 'stock bajo', 'predicciones']
        
        elif intent == 'top':
            rows = DB.query("""
                SELECT nombre, SUM(cantidad) q, SUM(total) t
                FROM historial_ventas
                WHERE fecha >= DATE('now','-7 days') AND nombre IS NOT NULL
                GROUP BY nombre ORDER BY q DESC LIMIT 5
            """)
            if rows:
                ans = "🏆 *Top 5 - Más Vendidos (Semana)*\n\n"
                for i, r in enumerate(rows, 1):
                    ans += f"{i}. *{r['nombre']}* - {r['q']:.0f} uds | ${r['t']:,.0f}\n"
            else:
                ans = "No hay suficientes datos para el ranking."
            sug = ['ventas de hoy', 'stock bajo']
        
        elif intent == 'inventory':
            rows = DB.query("""
                SELECT nombre, stock_actual, unidad_medida
                FROM inventario_general
                WHERE stock_actual <= 10 AND stock_actual >= 0
                ORDER BY stock_actual ASC LIMIT 10
            """)
            if not rows:
                rows = DB.query("""
                    SELECT nombre, stock_actual, unidad_medida
                    FROM productos
                    WHERE stock_actual <= 10 AND stock_actual >= 0
                    ORDER BY stock_actual ASC LIMIT 10
                """)
            prods = [{'n': r['nombre'], 's': r['stock_actual'], 'u': r['unidad_medida'] or 'Un'} for r in rows] if rows else []
            ans = R.inventory_alert(prods)
            sug = ['reabastecer', 'ventas de hoy']
        
        elif intent == 'predictions':
            d = DB.query("""
                SELECT COALESCE(SUM(total),0) r
                FROM historial_ventas
                WHERE DATE(fecha)=DATE('now','localtime')
            """, one=True)
            rev = d['r'] if d else 0
            ans = f"🔮 *Predicciones Inteligentes*\n\n"
            ans += f"📈 Proyección semanal: *${rev*7:,.0f}*\n"
            ans += f"📊 Basado en ritmo de ventas actual\n\n"
            
            stats = ProductSearch.stats()
            ans += f"📦 Productos activos: {stats['total_products']}\n"
            if stats['low_stock'] > 0:
                ans += f"⚠️ Necesitan reabastecimiento: {stats['low_stock']}\n"
            if stats['out_stock'] > 0:
                ans += f"❌ Agotados: {stats['out_stock']}\n"
            
            sug = ['ventas de hoy', 'stock bajo', 'top productos']
        
        elif intent == 'recommendations':
            low = DB.query("""
                SELECT nombre, stock_actual, precio_venta
                FROM inventario_general
                WHERE stock_actual <= 5 AND stock_actual > 0
                ORDER BY stock_actual ASC LIMIT 5
            """)
            
            ans = "💡 *Recomendaciones Inteligentes*\n\n"
            
            if low:
                ans += "📦 *Reabastecer urgente:*\n"
                for r in low:
                    ans += f"  • {r['nombre']} - {r['stock_actual']:.0f} uds | ${r['precio_venta']:,.0f}\n"
            else:
                ans += "✅ Inventario en orden.\n"
            
            d = DB.query("""
                SELECT COALESCE(SUM(total),0) r
                FROM historial_ventas
                WHERE DATE(fecha)=DATE('now','localtime')
            """, one=True)
            if d and d['r'] > 0:
                ans += f"\n💰 Ventas hoy: ${d['r']:,.0f}\n"
            
            ans += "\n💡 Revisa el inventario y haz pedidos pronto."
            sug = ['ventas de hoy', 'stock bajo', 'predicciones']
        
        elif intent == 'help':
            ans = R.help_menu()
            sug = ['ventas de hoy', 'buscar producto', 'stock bajo']
        
        elif intent == 'farewell':
            ans = "¡Hasta luego! Estoy aquí cuando me necesites. 👋"
            sug = []
        
        else:
            prods = ProductSearch.search(text)
            if prods:
                ans = R.product_list(prods, text)
                sug = ['ventas de hoy', 'stock bajo']
            else:
                ans = R.help_menu()
                sug = ['ventas de hoy', 'ayuda']
        
        mem.add(text, intent, ans)
        return self._fmt(ans, intent, sug)
    
    def _fmt(self, answer, intent, suggestions=None):
        return {
            'answer': answer,
            'intent': intent,
            'suggestions': suggestions or [],
            'ts': datetime.now().isoformat()
        }
    
    def alerts(self):
        alerts = []
        low = DB.query("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual <= 3 AND stock_actual >= 0")
        if low and low[0]['c'] > 0:
            alerts.append({
                'type': 'critical',
                'icon': '🔴',
                'title': 'Stock Crítico',
                'msg': f'{low[0]["c"]} productos necesitan reabastecimiento urgente'
            })
        
        d = DB.query("SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if d and d['r'] > 10000:
            alerts.append({
                'type': 'success',
                'icon': '🟢',
                'title': '¡Excelente día!',
                'msg': f'Ventas superiores a ${d["r"]:,.0f}'
            })
        
        return alerts

# ── Singleton ──
_agent = None
_lock = threading.Lock()

def _get():
    global _agent
    if _agent is None:
        with _lock:
            if _agent is None:
                _agent = Agent()
    return _agent

# ── API Pública (compatible con ia_assistant_routes.py) ──
def process_question(sid, question, role='vendedor', user_name=''):
    r = _get().process(question, sid, role, user_name)
    return {
        'answer': r['answer'],
        'intent': r['intent'],
        'suggestions': r['suggestions'],
        'role': role,
        'role_label': ROLES.get(role, {}).get('label', 'Usuario'),
        'role_color': ROLES.get(role, {}).get('color', '#3498db'),
        'role_icon': ROLES.get(role, {}).get('icon', '?'),
        'ts': r['ts']
    }

def get_status():
    stats = ProductSearch.stats()
    return {
        'version': '1.0.0',
        'model': 'NLP + Fuzzy Search + Dialogue Memory',
        'status': 'active',
        'features': [
            'Diálogo multi-turno con memoria',
            'Comprensión de lenguaje natural',
            'Búsqueda difusa de productos',
            'Dashboard de ventas en vivo',
            'Alertas proactivas de inventario',
            'Sugerencias inteligentes adaptativas'
        ],
        'stats': stats
    }

def get_conversation_history(session_id='default'):
    mem = _get()._mem(session_id)
    return [{
        'q': t['q'],
        'a': t['r'],
        'intent': t['intent'],
        'ts': ''
    } for t in mem.turns[-10:]]

def get_proactive_alerts(session_id='default'):
    return {'alerts': _get().alerts()}

def set_session_role(sid, role, user_name=''):
    return role

def get_session_info(sid):
    mem = _get()._mem(sid)
    return {
        'role': 'vendedor',
        'role_label': 'Vendedor',
        'role_color': '#3498db',
        'role_icon': 'V',
        'turns': len(mem.turns)
    }

ROLES = {
    'vendedor': {'label': 'Vendedor', 'color': '#3498db', 'icon': 'V'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'supervisor': {'label': 'Supervisor', 'color': '#f39c12', 'icon': 'S'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
    'cliente': {'label': 'Cliente', 'color': '#2ecc71', 'icon': 'C'}
}

print("🚀 ia_agent.py v1.0 cargado correctamente")
