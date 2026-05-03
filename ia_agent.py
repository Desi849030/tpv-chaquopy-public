"""
ia_agent.py v15.0 - Agente IA Profesional Interactivo
TPV Ultra Smart - 100% On-Device NLP Engine

CAPACIDADES:
- Diálogo multi-turno con memoria contextual
- Comprensión de lenguaje natural avanzada
- Dashboard en tiempo real
- Sugerencias inteligentes adaptativas
- Alertas proactivas automáticas
- Aprendizaje por refuerzo de interacciones
"""
import sqlite3, json, math, re, os, random, threading, time
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from difflib import SequenceMatcher

# ============================================================
# CONFIGURACIÓN DEL ENTORNO
# ============================================================
try:
    IS_ANDROID = hasattr(__import__('sys'), 'getandroidapilevel')
except:
    IS_ANDROID = False

# Rutas de base de datos
DB_PATHS = [
    os.path.join(os.environ.get('TPV_FILES_DIR', ''), 'tpv_datos.db'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db'),
    'tpv_datos.db', 'tpv.db'
]

def get_db_path():
    for path in DB_PATHS:
        if path and os.path.exists(path):
            return path
    return DB_PATHS[0] if DB_PATHS[0] else 'tpv_datos.db'

# ============================================================
# SISTEMA DE PERSONALIDAD DEL AGENTE
# ============================================================
class AgentPersonality:
    """Define la personalidad y tono del agente"""
    
    STYLES = {
        'profesional': {
            'greeting': ['Buen día', 'Saludos', 'A sus órdenes'],
            'emoji': True,
            'formalidad': 'alta'
        },
        'amigable': {
            'greeting': ['¡Hola!', '¡Hey!', '¡Qué tal!'],
            'emoji': True,
            'formalidad': 'media'
        },
        'rapido': {
            'greeting': ['Listo', 'Dale', 'OK'],
            'emoji': False,
            'formalidad': 'baja'
        }
    }
    
    def __init__(self, style='amigable'):
        self.style = style
        self.config = self.STYLES.get(style, self.STYLES['amigable'])
    
    def greet(self, user_name='', time_context=''):
        base = random.choice(self.config['greeting'])
        if time_context:
            base = f"{time_context}, {base.lower()}"
        if user_name:
            base = f"{base} {user_name}"
        return base
    
    def emojify(self, text):
        if not self.config['emoji']:
            return text
        emoji_map = {
            'ventas': '💰', 'producto': '📦', 'stock': '📊',
            'precio': '💵', 'cliente': '👤', 'alerta': '⚠️',
            'ok': '✅', 'error': '❌', 'info': 'ℹ️',
            'dashboard': '📈', 'kpi': '🎯', 'prediccion': '🔮'
        }
        for word, emoji in emoji_map.items():
            if word in text.lower():
                text = f"{emoji} {text}"
                break
        return text

# ============================================================
# MOTOR NLP AVANZADO
# ============================================================
class NLPCore:
    """Procesamiento de Lenguaje Natural central"""
    
    STOP_WORDS = {
        'de','del','la','el','los','las','en','con','y','a','un','una',
        'por','para','al','que','es','se','su','lo','no','si','mi','tu',
        'mas','muy','ya','o','e','u','le','les','me','te','nos','os'
    }
    
    # Intenciones con ejemplos de entrenamiento
    INTENT_TRAINING = {
        'greeting': [
            'hola','buenos dias','buenas tardes','buenas noches','hey',
            'que tal','como estas','saludos','que onda','buen dia'
        ],
        'farewell': [
            'adios','chao','bye','hasta luego','nos vemos','me voy',
            'hasta mañana','gracias por todo','terminamos'
        ],
        'search_product': [
            'cuanto cuesta','precio de','busco','necesito','tienen',
            'hay stock de','donde encuentro','quiero comprar',
            'cuanto vale','me das precio','cuanto sale'
        ],
        'sales_today': [
            'ventas de hoy','cuanto vendi','como van las ventas',
            'ventas del dia','cuanto recaude','cuanto facture',
            'reporte de ventas hoy','ventas acumuladas hoy'
        ],
        'sales_week': [
            'ventas de la semana','ventas semanales','como fue la semana',
            'balance semanal','semana actual'
        ],
        'sales_month': [
            'ventas del mes','ventas mensuales','como fue el mes',
            'balance mensual','mes actual'
        ],
        'top_products': [
            'productos mas vendidos','top productos','que se vende mas',
            'productos populares','best sellers','mas vendido'
        ],
        'stock_low': [
            'stock bajo','productos agotados','que falta','poco stock',
            'inventario critico','reabastecer','que me queda poco'
        ],
        'stock_check': [
            'cuanto stock hay','cuantas unidades','inventario de',
            'revisar stock de','disponibilidad de'
        ],
        'predictions': [
            'predicciones','pronostico','que se va a vender',
            'tendencias','estimacion','proyeccion futura'
        ],
        'kpi_dashboard': [
            'kpis','indicadores','metricas','dashboard','tablero',
            'estadisticas','rendimiento','indicadores clave'
        ],
        'recommendations': [
            'recomendacion','que me sugieres','que deberia hacer',
            'consejo','sugerencia','como mejorar','optimizar'
        ],
        'help': [
            'ayuda','help','que puedes hacer','como funciona',
            'que sabes hacer','capacidades','funcionalidades'
        ],
        'app_info': [
            'version','que eres','quien eres','info sistema',
            'acerca de','informacion'
        ]
    }
    
    def __init__(self):
        self.intent_vectors = {}
        self._train()
    
    def _tokenize(self, text):
        text = str(text).lower().strip()
        text = re.sub(r'[áàäâ]', 'a', text)
        text = re.sub(r'[éèëê]', 'e', text)
        text = re.sub(r'[íìïî]', 'i', text)
        text = re.sub(r'[óòöô]', 'o', text)
        text = re.sub(r'[úùüû]', 'u', text)
        tokens = re.findall(r'\b\w+\b', text)
        return [t for t in tokens if t not in self.STOP_WORDS and len(t) > 1]
    
    def _train(self):
        """Entrenar vectores de intenciones"""
        for intent, examples in self.INTENT_TRAINING.items():
            self.intent_vectors[intent] = []
            for ex in examples:
                self.intent_vectors[intent].append(set(self._tokenize(ex)))
    
    def classify(self, text):
        """Clasificar intención del texto"""
        tokens = set(self._tokenize(text))
        scores = {}
        
        for intent, vectors in self.intent_vectors.items():
            best_score = 0
            for vec in vectors:
                if not vec:
                    continue
                intersection = tokens & vec
                score = len(intersection) / len(vec) if vec else 0
                best_score = max(best_score, score)
            if best_score > 0:
                scores[intent] = best_score
        
        if not scores:
            return 'unknown', 0.0
        
        best = max(scores, key=scores.get)
        confidence = scores[best]
        
        return best, confidence
    
    def extract_product_name(self, text):
        """Extraer nombre de producto del texto"""
        patterns = [
            r'(?:cuanto\s+(?:cuesta|vale|es|esta))\s+(?:el|la|los|las|un|una)?\s*(.+?)(?:\?|$)',
            r'(?:busco|necesito|quiero|dame|tienen?)\s+(?:el|la|los|las)?\s*(.+?)(?:\?|$)',
            r'(?:hay|tienen?)\s+(?:stock\s+de\s+)?(.+?)(?:\?|$)',
            r'(?:precio|stock|info)\s+(?:de(?:l|la)?\s+)?(.+?)(?:\?|$)',
            r'^(.+?)(?:\s+(?:cuanto|precio|stock|vale|cuesta))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower().strip())
            if match:
                name = match.group(1).strip()
                name = re.sub(r'^(el |la |los |las |un |una )', '', name)
                if len(name) >= 2:
                    return name
        return None
    
    def extract_time_period(self, text):
        """Extraer período de tiempo"""
        text_lower = text.lower()
        if any(w in text_lower for w in ['hoy', 'hoy dia', 'hoy mismo']):
            return 'today'
        if any(w in text_lower for w in ['ayer', 'anoche']):
            return 'yesterday'
        if any(w in text_lower for w in ['semana', '7 dias', 'semanal']):
            return 'week'
        if any(w in text_lower for w in ['mes', '30 dias', 'mensual']):
            return 'month'
        if any(w in text_lower for w in ['año', 'ano', 'anual', '12 meses']):
            return 'year'
        return 'today'
    
    def fuzzy_match(self, text1, text2):
        """Coincidencia difusa entre textos"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

# ============================================================
# GESTOR DE DIÁLOGO CON MEMORIA
# ============================================================
class DialogueMemory:
    """Memoria conversacional multi-turno"""
    
    def __init__(self, max_turns=20):
        self.turns = []
        self.context = {}
        self.max_turns = max_turns
        self.topics = []
        self.user_preferences = defaultdict(int)
        self.last_intent = None
    
    def add(self, user_text, intent, response_summary):
        """Añadir turno a la memoria"""
        turn = {
            'timestamp': datetime.now().isoformat(),
            'user': user_text,
            'intent': intent,
            'response': response_summary[:150]
        }
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
        
        self.last_intent = intent
        self.topics.append(intent)
        if len(self.topics) > 10:
            self.topics = self.topics[-10:]
        
        # Actualizar preferencias
        self.user_preferences[intent] += 1
    
    def get_context_str(self, max_chars=200):
        """Obtener resumen del contexto"""
        if not self.turns:
            return ""
        recent = self.turns[-3:]
        return " | ".join([t['user'][:60] for t in recent])
    
    def is_followup(self, text):
        """Detectar si es pregunta de seguimiento"""
        text_lower = text.lower().strip()
        if not self.turns:
            return False
        
        indicators = ['y ', 'tambien ', 'ademas ', 'entonces ', 'y cuanto ', 'y como ']
        if any(text_lower.startswith(ind) for ind in indicators):
            return True
        
        if len(text_lower.split()) <= 3 and self.last_intent:
            return True
        
        return False
    
    def get_related_intent(self):
        """Obtener intención relacionada al contexto"""
        if self.topics:
            return self.topics[-1]
        return None

# ============================================================
# CONECTOR DE BASE DE DATOS
# ============================================================
class DBConnector:
    """Conexión optimizada a SQLite"""
    
    def __init__(self):
        self._conn = None
        self._path = None
        self._lock = threading.Lock()
    
    def connect(self):
        with self._lock:
            path = get_db_path()
            if self._conn and self._path == path:
                try:
                    self._conn.execute("SELECT 1")
                    return self._conn
                except:
                    pass
            
            if os.path.exists(path):
                self._conn = sqlite3.connect(path, timeout=5, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA busy_timeout=3000")
                self._path = path
                return self._conn
        return None
    
    def query(self, sql, params=(), one=False):
        conn = self.connect()
        if not conn:
            return None
        try:
            cursor = conn.execute(sql, params)
            return cursor.fetchone() if one else cursor.fetchall()
        except:
            return None
    
    def close(self):
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except:
                    pass
                self._conn = None

# ============================================================
# BUSCADOR DE PRODUCTOS AVANZADO
# ============================================================
class SmartProductSearch:
    """Búsqueda inteligente con caché"""
    
    def __init__(self):
        self.db = DBConnector()
        self.cache = []
        self.cache_time = None
        self.cache_ttl = 15  # segundos
    
    def _refresh(self):
        now = time.time()
        if self.cache_time and (now - self.cache_time) < self.cache_ttl:
            return
        
        conn = self.db.connect()
        if not conn:
            return
        
        products = []
        try:
            # Productos activos
            rows = conn.execute("""
                SELECT nombre, precio, costo, categoria, 
                       stock_actual, unidad_medida
                FROM productos WHERE activo=1
                ORDER BY nombre
            """).fetchall()
            
            for r in rows:
                products.append({
                    'nombre': r[0] or '',
                    'precio': float(r[1] or 0),
                    'costo': float(r[2] or 0),
                    'categoria': r[3] or 'General',
                    'stock': float(r[4] or 0),
                    'unidad': r[5] or 'Un',
                    'source': 'productos'
                })
            
            # Complementar con inventario_general
            existing = {p['nombre'].lower() for p in products}
            rows2 = conn.execute("""
                SELECT nombre, precio_venta, precio_compra, categoria,
                       stock_actual, unidad_medida
                FROM inventario_general
                ORDER BY nombre
            """).fetchall()
            
            for r in rows2:
                name = (r[0] or '').lower()
                if name not in existing:
                    products.append({
                        'nombre': r[0] or '',
                        'precio': float(r[1] or 0),
                        'costo': float(r[2] or 0),
                        'categoria': r[3] or 'General',
                        'stock': float(r[4] or 0),
                        'unidad': r[5] or 'Un',
                        'source': 'inventario_general'
                    })
            
            self.cache = products
            self.cache_time = now
        except:
            pass
    
    def search(self, query, limit=8, fuzzy=True):
        self._refresh()
        
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower().strip()
        scored = []
        
        for p in self.cache:
            name_lower = p['nombre'].lower()
            score = 0
            
            if query_lower == name_lower:
                score = 100
            elif query_lower in name_lower:
                score = 85
            elif name_lower in query_lower:
                score = 75
            elif fuzzy:
                words = query_lower.split()
                for word in words:
                    if len(word) < 2:
                        continue
                    if word in name_lower:
                        score += 30
                    if word in p['categoria'].lower():
                        score += 15
                    for name_word in name_lower.split():
                        if len(name_word) >= 3:
                            sim = SequenceMatcher(None, word, name_word).ratio()
                            if sim > 0.7:
                                score += int(sim * 25)
            
            if p['stock'] > 0:
                score += 3
            if p['stock'] <= 5 and p['stock'] > 0:
                score -= 5  # Penalizar stock bajo
            
            if score > 0:
                scored.append((score, p))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
    
    def get_stats(self):
        self._refresh()
        total = len(self.cache)
        low_stock = sum(1 for p in self.cache if 0 < p['stock'] <= 5)
        out_stock = sum(1 for p in self.cache if p['stock'] <= 0)
        total_value = sum(p['precio'] * p['stock'] for p in self.cache if p['stock'] > 0)
        return {
            'total_products': total,
            'low_stock': low_stock,
            'out_stock': out_stock,
            'inventory_value': total_value
        }

# ============================================================
# GENERADOR DE RESPUESTAS DINÁMICAS
# ============================================================
class DynamicResponder:
    """Genera respuestas naturales y variadas"""
    
    def __init__(self):
        self.personality = AgentPersonality('amigable')
    
    def time_greeting(self):
        h = datetime.now().hour
        if h < 6: return "🌙 Buenas noches"
        if h < 12: return "☀️ Buenos días"
        if h < 14: return "🌤️ Buen mediodía"
        if h < 20: return "🌅 Buenas tardes"
        return "🌆 Buenas noches"
    
    def greeting(self, user_name=''):
        time_greet = self.time_greeting()
        if user_name:
            return f"{time_greet}, {user_name}! ¿En qué puedo ayudarte hoy?"
        return f"{time_greet}! Soy tu asistente inteligente. ¿Qué necesitas?"
    
    def product_card(self, p):
        """Tarjeta de producto detallada"""
        nombre = p['nombre']
        precio = p['precio']
        stock = p['stock']
        unidad = p['unidad']
        categoria = p['categoria']
        costo = p['costo']
        
        # Calcular margen
        margin = 0
        if precio > 0 and costo >= 0:
            margin = ((precio - costo) / precio) * 100
        
        msg = f"📦 *{nombre}*\n\n"
        msg += f"💰 Precio: ${precio:,.0f} / {unidad}\n"
        msg += f"📊 Stock: {stock:.0f} {unidad}\n"
        msg += f"🏷️ Categoría: {categoria}\n"
        
        if margin > 0:
            msg += f"📈 Margen: {margin:.1f}%\n"
        
        # Alertas
        if stock == 0:
            msg += f"\n❌ *AGOTADO* - Sin stock disponible"
        elif stock <= 3:
            msg += f"\n⚠️ *URGENTE* - Solo quedan {stock:.0f} {unidad}"
        elif stock <= 10:
            msg += f"\n📊 Stock bajo - {stock:.0f} {unidad} restantes"
        
        # Valor del inventario
        if stock > 0:
            value = precio * stock
            if value > 1000:
                msg += f"\n💎 Valor en stock: ${value:,.0f}"
        
        return msg
    
    def product_list(self, products, query, max_show=6):
        """Lista de productos encontrados"""
        count = len(products)
        if count == 0:
            return f"❌ No encontré '{query}'. ¿Podrías intentar con otro nombre o categoría?"
        
        if count == 1:
            return self.product_card(products[0])
        
        msg = f"🔍 Encontré *{count} productos* para '*{query}*':\n\n"
        
        for i, p in enumerate(products[:max_show]):
            stock_icon = "🟢" if p['stock'] > 10 else "🟡" if p['stock'] > 0 else "🔴"
            msg += f"{stock_icon} *{p['nombre']}* - ${p['precio']:,.0f}\n"
            msg += f"   └─ {p['stock']:.0f} {p['unidad']} | {p['categoria']}\n"
        
        if count > max_show:
            msg += f"\n... y {count - max_show} productos más.\n"
        
        msg += "\n💡 Escribe el nombre exacto para ver más detalles."
        return msg
    
    def sales_dashboard(self, data):
        """Dashboard de ventas"""
        if not data or data.get('transactions', 0) == 0:
            return "📊 Aún no hay ventas registradas hoy.\n\n¿Quieres registrar una venta?"
        
        txns = data.get('transactions', 0)
        rev = data.get('revenue', 0)
        avg = data.get('avg_ticket', 0)
        units = data.get('units', 0)
        
        # Determinar estado
        if rev > 5000:
            status = "🔥 ¡Excelente día!"
            emoji = "🟢"
        elif rev > 2000:
            status = "👍 Buen ritmo de ventas"
            emoji = "🟡"
        elif rev > 500:
            status = "📊 Ventas moderadas"
            emoji = "🟠"
        else:
            status = "💤 Día tranquilo"
            emoji = "🔵"
        
        msg = f"📊 *Dashboard de Ventas - Hoy*\n\n"
        msg += f"{emoji} {status}\n\n"
        msg += f"🛒 Transacciones: *{txns}*\n"
        msg += f"💰 Ingresos totales: *${rev:,.0f}*\n"
        msg += f"📈 Ticket promedio: *${avg:,.0f}*\n"
        msg += f"📦 Unidades vendidas: *{units:.0f}*\n"
        
        # Proyección
        hour = datetime.now().hour
        if hour > 0 and rev > 0:
            projected = (rev / hour) * 24 if hour > 0 else rev
            msg += f"\n🔮 Proyección del día: *${projected:,.0f}*\n"
        
        return msg
    
    def inventory_alert(self, products):
        """Alerta de inventario"""
        if not products:
            return "✅ ¡Todo en orden! No hay productos con stock bajo."
        
        critical = [p for p in products if p['stock'] <= 3]
        warning = [p for p in products if 3 < p['stock'] <= 10]
        
        msg = "⚠️ *Alerta de Inventario*\n\n"
        
        if critical:
            msg += f"🔴 *Stock Crítico* ({len(critical)}):\n"
            for p in critical[:5]:
                msg += f"  • {p['nombre']} - {p['stock']:.0f} {p.get('unidad','Un')}\n"
            msg += "\n"
        
        if warning:
            msg += f"🟡 *Stock Bajo* ({len(warning)}):\n"
            for p in warning[:5]:
                msg += f"  • {p['nombre']} - {p['stock']:.0f} {p.get('unidad','Un')}\n"
            msg += "\n"
        
        msg += "💡 Recomiendo reabastecer los productos críticos lo antes posible."
        return msg
    
    def help_menu(self):
        """Menú de ayuda interactivo"""
        msg = "🤖 *Asistente TPV Smart*\n\n"
        msg += "*Puedes preguntarme:*\n\n"
        msg += "📦 *Productos*\n"
        msg += "  • ¿Cuánto cuesta [producto]?\n"
        msg += "  • ¿Hay stock de [producto]?\n"
        msg += "  • Buscar [categoría]\n\n"
        msg += "💰 *Ventas*\n"
        msg += "  • ¿Cómo van las ventas hoy?\n"
        msg += "  • Ventas de la semana\n"
        msg += "  • Top productos\n\n"
        msg += "📊 *Inventario*\n"
        msg += "  • ¿Qué stock tengo?\n"
        msg += "  • Productos agotados\n"
        msg += "  • Stock bajo\n\n"
        msg += "📈 *Análisis*\n"
        msg += "  • Dame los KPIs\n"
        msg += "  • Predicciones de venta\n"
        msg += "  • Recomendaciones\n\n"
        msg += "*Escribe en lenguaje natural, sin comandos.*"
        return msg
    
    def kpi_dashboard(self, sales_data, inventory_stats):
        """Dashboard de KPIs"""
        msg = "📈 *KPI Dashboard*\n\n"
        
        if sales_data:
            msg += "💰 *Ventas Hoy*\n"
            msg += f"  • Transacciones: {sales_data.get('transactions',0)}\n"
            msg += f"  • Ingresos: ${sales_data.get('revenue',0):,.0f}\n"
            msg += f"  • Ticket promedio: ${sales_data.get('avg_ticket',0):,.0f}\n\n"
        
        if inventory_stats:
            msg += "📦 *Inventario*\n"
            msg += f"  • Total productos: {inventory_stats.get('total_products',0)}\n"
            msg += f"  • Stock bajo: {inventory_stats.get('low_stock',0)}\n"
            msg += f"  • Agotados: {inventory_stats.get('out_stock',0)}\n"
            msg += f"  • Valor inventario: ${inventory_stats.get('inventory_value',0):,.0f}\n"
        
        return msg

# ============================================================
# AGENTE PRINCIPAL
# ============================================================
class TPVAIAgent:
    """Agente IA central del TPV"""
    
    def __init__(self):
        self.nlp = NLPCore()
        self.memory = {}  # session_id -> DialogueMemory
        self.searcher = SmartProductSearch()
        self.responder = DynamicResponder()
        self.db = DBConnector()
        self.lock = threading.Lock()
        self.learning_db = []  # Aprendizaje simple
        print("✅ Agente IA v15.0 inicializado")
    
    def get_memory(self, session_id):
        with self.lock:
            if session_id not in self.memory:
                self.memory[session_id] = DialogueMemory()
            return self.memory[session_id]
    
    def process(self, text, session_id='default', role='vendedor', user_name=''):
        """Procesar mensaje del usuario"""
        
        if not text or not text.strip():
            return self._format_response(
                "Por favor, dime qué necesitas. Puedo ayudarte con ventas, productos, inventario y más.",
                'help'
            )
        
        mem = self.get_memory(session_id)
        text_clean = text.strip()
        
        # Detectar seguimiento
        if mem.is_followup(text_clean) and mem.last_intent:
            # Combinar con contexto
            context_intent = mem.last_intent
            intent, confidence = self.nlp.classify(text_clean)
            if confidence < 0.3:
                intent = context_intent
        else:
            intent, confidence = self.nlp.classify(text_clean)
        
        # Procesar según intención
        response = self._handle_intent(intent, text_clean, role, user_name)
        
        # Guardar en memoria
        mem.add(text_clean, intent, response.get('answer', '')[:150])
        
        # Añadir sugerencias si no tiene
        if 'suggestions' not in response:
            response['suggestions'] = self._generate_suggestions(intent, mem)
        
        return self._format_response(response.get('answer', ''), intent, response.get('suggestions', []))
    
    def _handle_intent(self, intent, text, role, user_name):
        """Manejar cada tipo de intención"""
        
        if intent == 'greeting':
            return {
                'answer': self.responder.greeting(user_name),
                'suggestions': ['ventas de hoy', 'stock bajo', 'buscar producto']
            }
        
        elif intent == 'farewell':
            return {
                'answer': '¡Hasta luego! Estoy aquí cuando me necesites. 👋',
                'suggestions': []
            }
        
        elif intent == 'search_product':
            product_name = self.nlp.extract_product_name(text) or text
            products = self.searcher.search(product_name)
            return {
                'answer': self.responder.product_list(products, product_name),
                'suggestions': ['ventas de hoy', 'stock bajo', 'otro producto']
            }
        
        elif intent in ['sales_today', 'sales_week', 'sales_month']:
            period = 'today'
            if 'week' in intent:
                period = 'week'
            elif 'month' in intent:
                period = 'month'
            
            data = self._get_sales_data(period)
            return {
                'answer': self.responder.sales_dashboard(data),
                'suggestions': ['top productos', 'stock bajo', 'predicciones']
            }
        
        elif intent == 'top_products':
            top = self._get_top_products()
            if top:
                msg = "🏆 *Top 5 Productos Más Vendidos*\n\n"
                for i, p in enumerate(top, 1):
                    msg += f"{i}. *{p['nombre']}* - {p['cantidad']:.0f} uds | ${p['total']:,.0f}\n"
                answer = msg
            else:
                answer = "No hay suficientes datos para mostrar el top de productos."
            return {
                'answer': answer,
                'suggestions': ['ventas de hoy', 'stock bajo']
            }
        
        elif intent in ['stock_low', 'stock_check']:
            low_stock = self._get_low_stock()
            return {
                'answer': self.responder.inventory_alert(low_stock),
                'suggestions': ['reabastecer', 'ver todos los productos', 'ventas de hoy']
            }
        
        elif intent == 'kpi_dashboard':
            sales = self._get_sales_data('today')
            stats = self.searcher.get_stats()
            return {
                'answer': self.responder.kpi_dashboard(sales, stats),
                'suggestions': ['ventas de hoy', 'stock bajo', 'predicciones']
            }
        
        elif intent == 'predictions':
            sales = self._get_sales_data('today')
            stats = self.searcher.get_stats()
            answer = "🔮 *Predicciones y Análisis*\n\n"
            if sales and sales.get('revenue', 0) > 0:
                projected = sales['revenue'] * 7
                answer += f"📈 Proyección semanal: *${projected:,.0f}*\n"
                answer += f"📊 Basado en el ritmo actual de ventas\n\n"
            if stats:
                answer += f"📦 Productos activos: {stats['total_products']}\n"
                answer += f"⚠️ Necesitan reabastecimiento: {stats['low_stock']}\n"
            return {
                'answer': answer,
                'suggestions': ['ventas de hoy', 'stock bajo', 'top productos']
            }
        
        elif intent == 'recommendations':
            low = self._get_low_stock()
            sales = self._get_sales_data('today')
            answer = "💡 *Recomendaciones Inteligentes*\n\n"
            if low:
                answer += "📦 *Reabastecer urgente:*\n"
                for p in low[:3]:
                    answer += f"  • {p['nombre']} - stock: {p['stock']:.0f}\n"
            if sales and sales.get('revenue', 0) > 0:
                answer += f"\n💰 Ventas hoy: ${sales['revenue']:,.0f}\n"
            answer += "\n✅ Sugiero revisar el inventario y hacer un pedido pronto."
            return {
                'answer': answer,
                'suggestions': ['ventas de hoy', 'stock bajo', 'predicciones']
            }
        
        elif intent == 'help':
            return {
                'answer': self.responder.help_menu(),
                'suggestions': ['ventas de hoy', 'buscar producto', 'stock bajo']
            }
        
        elif intent == 'app_info':
            return {
                'answer': "🤖 *TPV Ultra Smart v15.0*\n\nSoy un asistente IA 100% local con:\n• Comprensión de lenguaje natural\n• Búsqueda inteligente de productos\n• Dashboard de ventas en tiempo real\n• Alertas de inventario proactivas\n• Memoria conversacional\n\n*Pregúntame lo que necesites.*",
                'suggestions': ['ayuda', 'ventas de hoy']
            }
        
        else:
            # Intento final: buscar como producto
            products = self.searcher.search(text)
            if products:
                return {
                    'answer': self.responder.product_list(products, text),
                    'suggestions': ['ventas de hoy', 'stock bajo']
                }
            return {
                'answer': self.responder.help_menu(),
                'suggestions': ['ventas de hoy', 'buscar producto', 'stock bajo']
            }
    
    def _get_sales_data(self, period='today'):
        """Obtener datos de ventas"""
        date_filters = {
            'today': "DATE(fecha) = DATE('now','localtime')",
            'yesterday': "DATE(fecha) = DATE('now','localtime','-1 day')",
            'week': "fecha >= DATE('now','localtime','-7 days')",
            'month': "fecha >= DATE('now','localtime','-30 days')",
            'year': "fecha >= DATE('now','localtime','-365 days')"
        }
        
        date_filter = date_filters.get(period, date_filters['today'])
        
        row = self.db.query(
            f"""SELECT COUNT(*) as txns, COALESCE(SUM(total),0) as rev,
                       COALESCE(AVG(total),0) as avg_ticket,
                       COALESCE(SUM(cantidad),0) as units
                FROM historial_ventas WHERE {date_filter}""",
            one=True
        )
        
        if row:
            return {
                'transactions': row['txns'],
                'revenue': row['rev'],
                'avg_ticket': row['avg_ticket'],
                'units': int(row['units'])
            }
        return {'transactions': 0, 'revenue': 0, 'avg_ticket': 0, 'units': 0}
    
    def _get_low_stock(self):
        """Obtener productos con stock bajo"""
        rows = self.db.query(
            """SELECT nombre, stock_actual, unidad_medida
               FROM inventario_general
               WHERE stock_actual <= 10 AND stock_actual >= 0
               ORDER BY stock_actual ASC LIMIT 10"""
        )
        if not rows:
            rows = self.db.query(
                """SELECT nombre, stock_actual, unidad_medida
                   FROM productos
                   WHERE stock_actual <= 10 AND stock_actual >= 0
                   ORDER BY stock_actual ASC LIMIT 10"""
            )
        if not rows:
            return []
        return [
            {'nombre': r['nombre'], 'stock': r['stock_actual'], 'unidad': r['unidad_medida'] or 'Un'}
            for r in rows
        ]
    
    def _get_top_products(self, limit=5):
        """Obtener productos más vendidos"""
        rows = self.db.query(
            f"""SELECT nombre, SUM(cantidad) as qty, SUM(total) as total
                FROM historial_ventas
                WHERE fecha >= DATE('now','localtime','-7 days') AND nombre IS NOT NULL
                GROUP BY nombre ORDER BY qty DESC LIMIT {limit}"""
        )
        if not rows:
            return []
        return [
            {'nombre': r['nombre'], 'cantidad': r['qty'], 'total': r['total']}
            for r in rows
        ]
    
    def _generate_suggestions(self, intent, memory):
        """Generar sugerencias contextuales"""
        base_suggestions = {
            'greeting': ['ventas de hoy', 'stock bajo', 'buscar producto'],
            'search_product': ['ventas de hoy', 'stock bajo', 'otro producto'],
            'sales_today': ['top productos', 'stock bajo', 'predicciones'],
            'sales_week': ['ventas de hoy', 'top productos', 'predicciones'],
            'stock_low': ['reabastecer', 'ver todos', 'ventas de hoy'],
            'kpi_dashboard': ['ventas de hoy', 'predicciones', 'recomendaciones'],
            'predictions': ['ventas de hoy', 'top productos', 'recomendaciones'],
            'recommendations': ['ventas de hoy', 'stock bajo', 'predicciones'],
            'help': ['ventas de hoy', 'buscar producto', 'stock bajo'],
            'app_info': ['ayuda', 'ventas de hoy'],
            'farewell': []
        }
        
        suggestions = base_suggestions.get(intent, ['ventas de hoy', 'ayuda', 'buscar producto'])
        
        # Personalizar según preferencias del usuario
        if memory.user_preferences:
            top_intent = max(memory.user_preferences, key=memory.user_preferences.get)
            if top_intent == 'sales_today':
                suggestions.insert(0, 'ventas de hoy')
            elif top_intent == 'search_product':
                suggestions.insert(0, 'buscar producto')
        
        return suggestions[:4]
    
    def _format_response(self, answer, intent, suggestions=None):
        """Formatear respuesta final"""
        return {
            'answer': self.responder.personality.emojify(answer),
            'intent': intent,
            'suggestions': suggestions or [],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_proactive_alerts(self):
        """Generar alertas proactivas automáticas"""
        alerts = []
        low_stock = self._get_low_stock()
        
        if low_stock:
            critical = [p for p in low_stock if p['stock'] <= 3]
            if critical:
                alerts.append({
                    'type': 'critical',
                    'icon': '🔴',
                    'title': 'Stock Crítico',
                    'message': f'{len(critical)} productos necesitan reabastecimiento urgente',
                    'products': [p['nombre'] for p in critical[:3]]
                })
            elif len(low_stock) > 5:
                alerts.append({
                    'type': 'warning',
                    'icon': '🟡',
                    'title': 'Stock Bajo',
                    'message': f'{len(low_stock)} productos con stock bajo'
                })
        
        # Alerta de rendimiento
        sales = self._get_sales_data('today')
        if sales and sales['revenue'] > 10000:
            alerts.append({
                'type': 'success',
                'icon': '🟢',
                'title': '¡Excelente día!',
                'message': f'Ventas superiores a ${sales["revenue"]:,.0f}'
            })
        
        return alerts

# ============================================================
# API PÚBLICA COMPATIBLE
# ============================================================
_agent = None
_lock = threading.Lock()

def _get_agent():
    global _agent
    if _agent is None:
        with _lock:
            if _agent is None:
                _agent = TPVAIAgent()
    return _agent

def process_question(sid, question, role='vendedor', user_name=''):
    agent = _get_agent()
    result = agent.process(question, sid, role, user_name)
    
    return {
        'answer': result['answer'],
        'intent': result.get('intent', 'unknown'),
        'suggestions': result.get('suggestions', []),
        'role': role,
        'role_label': ROLES.get(role, {}).get('label', 'Usuario'),
        'role_color': ROLES.get(role, {}).get('color', '#3498db'),
        'role_icon': ROLES.get(role, {}).get('icon', '?'),
        'ts': result.get('timestamp', datetime.now().isoformat())
    }

def get_status():
    agent = _get_agent()
    return {
        'version': '15.0.0',
        'model': 'NLP Multi-Intent + Fuzzy Search + Dialogue Memory',
        'status': 'active',
        'features': [
            'Diálogo multi-turno con memoria',
            'Comprensión de lenguaje natural',
            'Búsqueda difusa de productos',
            'Dashboard de ventas en tiempo real',
            'Alertas proactivas de inventario',
            'Sugerencias inteligentes adaptativas',
            'Personalidad dinámica'
        ],
        'stats': agent.searcher.get_stats()
    }

def get_conversation_history(session_id='default'):
    agent = _get_agent()
    mem = agent.get_memory(session_id)
    return [{
        'user': t['user'],
        'intent': t['intent'],
        'response': t['response'],
        'ts': t['timestamp']
    } for t in mem.turns[-10:]]

def get_proactive_alerts(session_id='default'):
    agent = _get_agent()
    return {'alerts': agent.get_proactive_alerts()}

def set_session_role(sid, role, user_name=''):
    return role

def get_session_info(sid):
    agent = _get_agent()
    mem = agent.get_memory(sid)
    return {
        'role': 'vendedor',
        'role_label': 'Vendedor',
        'role_color': '#3498db',
        'role_icon': 'V',
        'turns': len(mem.turns),
        'context': mem.get_context_str()
    }

ROLES = {
    'vendedor': {'label': 'Vendedor', 'color': '#3498db', 'icon': 'V'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'supervisor': {'label': 'Supervisor', 'color': '#f39c12', 'icon': 'S'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
    'cliente': {'label': 'Cliente', 'color': '#2ecc71', 'icon': 'C'}
}

print("🚀 ia_agent.py v15.0 - Agente IA Profesional Interactivo listo")
