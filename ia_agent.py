"""
ia_agent.py - TPV Smart v14.0 - Agente IA Profesional NLP
100% On-Device, sin dependencias externas
"""
import sqlite3, json, math, re, os, random, threading
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher

# ============================================================
# DETECCIÓN DE ENTORNO (Android vs Desktop)
# ============================================================
try:
    IS_ANDROID = hasattr(__import__('sys'), 'getandroidapilevel')
except:
    IS_ANDROID = False

if IS_ANDROID:
    DB_PATH = os.path.join(os.environ.get('TPV_FILES_DIR', '.'), 'tpv_datos.db')
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')

# ============================================================
# MOTOR NLP - TF-IDF + Cosine Similarity
# ============================================================
class NLPEngine:
    def __init__(self):
        self.vocabulary = set()
        self.idf = {}
        self.stop_words = {
            'de','del','la','el','los','las','en','con','y','a','un','una',
            'por','para','al','que','es','se','su','lo','no','si','mi','tu',
            'mas','muy','ya','o','e','u','the','a','an','is','are','was'
        }
    
    def tokenize(self, text):
        text = str(text).lower().strip()
        text = re.sub(r'[áàäâ]', 'a', text)
        text = re.sub(r'[éèëê]', 'e', text)
        text = re.sub(r'[íìïî]', 'i', text)
        text = re.sub(r'[óòöô]', 'o', text)
        text = re.sub(r'[úùüû]', 'u', text)
        tokens = re.findall(r'\b\w+\b', text)
        return [t for t in tokens if t not in self.stop_words and len(t) > 1]
    
    def cosine_similarity(self, text1, text2):
        tokens1 = set(self.tokenize(text1))
        tokens2 = set(self.tokenize(text2))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(intersection) / len(union) if union else 0.0

# ============================================================
# CLASIFICADOR DE INTENCIONES
# ============================================================
class IntentClassifier:
    def __init__(self):
        self.nlp = NLPEngine()
        self.intents = {
            'greeting': ['hola','buenos dias','buenas tardes','hey','que tal','saludos'],
            'search_product': ['cuanto cuesta','precio de','busco','necesito','tienen','hay stock'],
            'sales_query': ['ventas','cuanto vendi','recaude','facture','caja','reporte'],
            'inventory_query': ['stock','inventario','quedan','agotado','reabastecer'],
            'predictions': ['prediccion','pronostico','tendencia','preveer','estimacion'],
            'analytics': ['kpis','indicadores','metricas','dashboard','analisis'],
            'help': ['ayuda','help','que puedes hacer','como funciona']
        }
    
    def predict(self, text):
        tokens = self.nlp.tokenize(text)
        scores = {}
        for intent, keywords in self.intents.items():
            score = sum(1 for kw in keywords if kw in text.lower())
            if score > 0:
                scores[intent] = score
        
        if not scores:
            # Buscar por similitud
            for intent, keywords in self.intents.items():
                for kw in keywords:
                    sim = self.nlp.cosine_similarity(text, kw)
                    if sim > 0.3:
                        scores[intent] = scores.get(intent, 0) + sim
        
        if scores:
            best = max(scores, key=scores.get)
            confidence = min(1.0, scores[best] / 5.0)
            return best, confidence
        return 'unknown', 0.0

# ============================================================
# BUSCADOR DE PRODUCTOS CON FUZZY MATCHING
# ============================================================
class ProductSearcher:
    def __init__(self):
        self.cache = []
        self.cache_time = None
    
    def _get_db(self):
        for path in [DB_PATH, 'tpv_datos.db', 'tpv.db']:
            if os.path.exists(path):
                return sqlite3.connect(path, timeout=2)
        return None
    
    def _refresh_cache(self):
        now = datetime.now()
        if self.cache_time and (now - self.cache_time).seconds < 30:
            return
        
        conn = self._get_db()
        if not conn:
            return
        
        try:
            conn.row_factory = sqlite3.Row
            products = []
            
            # Buscar en tabla productos
            try:
                rows = conn.execute("""
                    SELECT nombre, precio, costo, categoria, stock_actual, unidad_medida
                    FROM productos WHERE activo=1
                """).fetchall()
                for r in rows:
                    products.append({
                        'nombre': r['nombre'] or '',
                        'precio': r['precio'] or 0,
                        'costo': r['costo'] or 0,
                        'categoria': r['categoria'] or 'General',
                        'stock': r['stock_actual'] or 0,
                        'unidad': r['unidad_medida'] or 'Un'
                    })
            except:
                pass
            
            # Buscar en inventario_general
            try:
                rows = conn.execute("""
                    SELECT nombre, precio_venta, precio_compra, categoria, stock_actual, unidad_medida
                    FROM inventario_general
                """).fetchall()
                for r in rows:
                    if not any(p['nombre'] == r['nombre'] for p in products):
                        products.append({
                            'nombre': r['nombre'] or '',
                            'precio': r['precio_venta'] or 0,
                            'costo': r['precio_compra'] or 0,
                            'categoria': r['categoria'] or 'General',
                            'stock': r['stock_actual'] or 0,
                            'unidad': r['unidad_medida'] or 'Un'
                        })
            except:
                pass
            
            self.cache = products
            self.cache_time = now
        finally:
            conn.close()
    
    def search(self, query, limit=8):
        self._refresh_cache()
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower()
        results = []
        
        for p in self.cache:
            name_lower = p['nombre'].lower()
            score = 0
            
            # Coincidencia exacta
            if query_lower == name_lower:
                score = 100
            elif query_lower in name_lower:
                score = 80
            elif name_lower in query_lower:
                score = 70
            else:
                # Coincidencia por palabras
                for word in query_lower.split():
                    if len(word) < 2: continue
                    if word in name_lower:
                        score += 25
                    else:
                        # Fuzzy matching
                        for name_word in name_lower.split():
                            sim = SequenceMatcher(None, word, name_word).ratio()
                            if sim > 0.7:
                                score += sim * 20
            
            if score > 0:
                results.append((score, p))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

# ============================================================
# GENERADOR DE RESPUESTAS
# ============================================================
class ResponseGenerator:
    @staticmethod
    def greeting(user_name=''):
        name = f" {user_name}" if user_name else ""
        return random.choice([
            f"¡Hola{name}! Soy tu asistente TPV Smart. ¿En qué puedo ayudarte?",
            f"¡Buen día{name}! Estoy listo para asistirte con lo que necesites.",
            f"¿Qué tal{name}? Dime qué necesitas saber."
        ])
    
    @staticmethod
    def product_single(p):
        nombre = p.get('nombre', 'N/A')
        precio = f"${p.get('precio', 0):,.0f}"
        stock = p.get('stock', 0)
        unidad = p.get('unidad', 'Un')
        categoria = p.get('categoria', 'General')
        
        msg = f"📦 **{nombre}**\n\n"
        msg += f"💰 Precio: {precio}\n"
        msg += f"📊 Stock: {stock} {unidad}\n"
        msg += f"🏷️ Categoría: {categoria}\n"
        
        if stock == 0:
            msg += f"\n⚠️ **Producto agotado**"
        elif stock <= 3:
            msg += f"\n⚠️ Stock crítico - solo {stock} unidades"
        elif stock <= 10:
            msg += f"\n📊 Stock bajo"
        
        return msg
    
    @staticmethod
    def product_multiple(products, query):
        msg = f"🔍 Encontré {len(products)} productos para '{query}':\n\n"
        for p in products[:8]:
            msg += f"• **{p['nombre']}** - ${p['precio']:,.0f} ({p['stock']} uds)\n"
        msg += "\n¿Necesitas más detalles de alguno?"
        return msg
    
    @staticmethod
    def sales_today(data):
        return f"""📊 Ventas de hoy:

• {data['txns']} transacciones
• Ingresos: ${data['revenue']:,.0f}
• Ticket promedio: ${data['avg']:,.0f}
• Unidades vendidas: {data['units']}"""
    
    @staticmethod
    def inventory_low(products):
        if not products:
            return "✅ No hay productos con stock crítico."
        
        msg = "⚠️ Productos con stock bajo:\n\n"
        for p in products[:8]:
            msg += f"• **{p['nombre']}** - {p['stock']} unidades\n"
        msg += "\nTe recomiendo reabastecerlos pronto."
        return msg
    
    @staticmethod
    def help():
        return """🤖 Puedo ayudarte con:

🔍 **Buscar productos:**
  "¿Cuánto cuesta el café?"
  "¿Hay stock de leche?"

💰 **Consultar ventas:**
  "¿Cómo van las ventas hoy?"
  "¿Cuánto vendí esta semana?"

📦 **Revisar inventario:**
  "¿Qué productos tienen poco stock?"
  "Muéstrame el inventario"

📊 **Análisis:**
  "Dame los KPIs del día"
  "¿Qué se vende más?"

¿Qué necesitas saber?"""

# ============================================================
# AGENTE PRINCIPAL
# ============================================================
class TPVAIAgent:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.searcher = ProductSearcher()
        self.generator = ResponseGenerator()
        self.sessions = {}
        self.lock = threading.Lock()
    
    def process(self, text, session_id='default', role='vendedor', user_name=''):
        if not text or not text.strip():
            return {
                'answer': 'Dime qué necesitas saber.',
                'suggestions': ['ventas de hoy', 'stock bajo', 'ayuda']
            }
        
        # Clasificar intención
        intent, confidence = self.classifier.predict(text)
        
        # Procesar según intención
        if intent == 'greeting':
            answer = self.generator.greeting(user_name)
            suggestions = ['ventas de hoy', 'buscar producto', 'ayuda']
        
        elif intent == 'search_product':
            # Extraer nombre del producto
            product_name = re.sub(r'(cuanto cuesta|precio de|busco|necesito|hay stock de|tienen)\s+', '', text.lower())
            product_name = product_name.strip()
            products = self.searcher.search(product_name)
            
            if not products:
                answer = f"No encontré '{product_name}'. ¿Podrías intentar con otro nombre?"
            elif len(products) == 1:
                answer = self.generator.product_single(products[0])
            else:
                answer = self.generator.product_multiple(products, product_name)
            suggestions = ['ventas de hoy', 'stock bajo', 'ayuda']
        
        elif intent == 'sales_query':
            try:
                conn = self.searcher._get_db()
                if conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute("""
                        SELECT COUNT(*) as txns,
                               COALESCE(SUM(total),0) as rev,
                               COALESCE(AVG(total),0) as avg,
                               COALESCE(SUM(cantidad),0) as units
                        FROM historial_ventas
                        WHERE DATE(fecha) = DATE('now','localtime')
                    """).fetchone()
                    conn.close()
                    
                    if row and row['txns'] > 0:
                        answer = self.generator.sales_today({
                            'txns': row['txns'],
                            'revenue': row['rev'],
                            'avg': row['avg'],
                            'units': int(row['units'])
                        })
                    else:
                        answer = "No hay ventas registradas hoy."
                else:
                    answer = "No puedo acceder a la base de datos."
            except Exception as e:
                answer = f"Error al consultar ventas: {e}"
            suggestions = ['top productos', 'stock bajo', 'predicciones']
        
        elif intent == 'inventory_query':
            try:
                conn = self.searcher._get_db()
                if conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute("""
                        SELECT nombre, stock_actual
                        FROM inventario_general
                        WHERE stock_actual <= 5
                        ORDER BY stock_actual ASC
                        LIMIT 10
                    """).fetchall()
                    conn.close()
                    
                    products = [{'nombre': r['nombre'], 'stock': r['stock_actual']} for r in rows]
                    answer = self.generator.inventory_low(products)
                else:
                    answer = "No puedo acceder al inventario."
            except Exception as e:
                answer = f"Error: {e}"
            suggestions = ['reabastecer', 'ver todos los productos']
        
        elif intent == 'help':
            answer = self.generator.help()
            suggestions = ['ventas de hoy', 'buscar producto']
        
        else:
            # Intentar buscar como producto
            products = self.searcher.search(text)
            if products:
                if len(products) == 1:
                    answer = self.generator.product_single(products[0])
                else:
                    answer = self.generator.product_multiple(products, text)
            else:
                answer = self.generator.help()
            suggestions = ['ventas de hoy', 'ayuda']
        
        return {
            'answer': answer,
            'intent': intent,
            'confidence': confidence,
            'suggestions': suggestions,
            'role': role,
            'ts': datetime.now().isoformat()
        }

# ============================================================
# API PÚBLICA (compatible con ia_assistant_routes.py)
# ============================================================
_agent = None
_agent_lock = threading.Lock()

def _get_agent():
    global _agent
    if _agent is None:
        with _agent_lock:
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
        'role_label': 'Vendedor' if role == 'vendedor' else role.title(),
        'role_color': '#3498db',
        'role_icon': 'V',
        'ts': result.get('ts', datetime.now().isoformat())
    }

def get_status():
    return {
        'version': '14.0.0',
        'model': 'NLP + Fuzzy Search + Intent Classification',
        'status': 'active',
        'features': ['Clasificación de intenciones', 'Búsqueda difusa', 'Respuestas contextuales']
    }

def get_conversation_history(session_id='default'):
    return []

def set_session_role(sid, role, user_name=''):
    return role

def get_session_info(sid):
    return {'role': 'vendedor', 'role_label': 'Vendedor', 'role_color': '#3498db', 'role_icon': 'V'}

def get_proactive_alerts(sid):
    return {'alerts': []}

ROLES = {
    'vendedor': {'label': 'Vendedor', 'color': '#3498db', 'icon': 'V'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'supervisor': {'label': 'Supervisor', 'color': '#f39c12', 'icon': 'S'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
    'cliente': {'label': 'Cliente', 'color': '#2ecc71', 'icon': 'C'}
}

print("✅ ia_agent.py v14.0 cargado correctamente")
