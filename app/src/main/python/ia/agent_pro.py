"""Agente IA Pro v3 — Conectado a datos REALES de la BD
Fallback cuando AgentMaster no está disponible."""
import random, logging
from datetime import datetime
from ia.nlp_engine import NLPEngine
from ia.tool_system import TOOLS, suggest_tools
from ia.humanizer import Humanizer

logger = logging.getLogger(__name__)

# Helpers para obtener datos reales
def _datos_reales():
    """Obtiene métricas reales de la BD."""
    try:
        from ia.db_utils import q
        d = q("SELECT COUNT(*) t, COALESCE(SUM(total),0) r, COALESCE(AVG(total),0) a "
              "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        p = q("SELECT COUNT(*) n FROM productos WHERE activo=1", one=True)
        sb = q("SELECT COUNT(*) n FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0", one=True)
        return {
            'ventas_hoy': d['t'] if d else 0,
            'ingresos_hoy': d['r'] if d else 0,
            'promedio': d['a'] if d else 0,
            'productos': p['n'] if p else 0,
            'stock_bajo': sb['n'] if sb else 0,
        }
    except Exception:
        return {'ventas_hoy': 0, 'ingresos_hoy': 0, 'promedio': 0,
                'productos': 0, 'stock_bajo': 0}

def _fmt(n):
    """Formatea número como moneda."""
    try:
        return f"${n:,.2f}"
    except Exception:
        return f"${n}"


class AgentPro:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS

        self.personalities = {
            'desarrollador': {'name': 'Neo', 'emoji': '🧠'},
            'administrador': {'name': 'Athena', 'emoji': '🦉'},
            'supervisor': {'name': 'Ares', 'emoji': '⚔️'},
            'vendedor': {'name': 'Hermes', 'emoji': '💚'},
            'cajero': {'name': 'Iris', 'emoji': '💵'},
        }

    def process(self, text, role='cliente', user_name=''):
        session_id = f"sess_{random.randint(100000, 999999)}"
        p = self.personalities.get(role, {'name': 'Asistente', 'emoji': '🤖'})
        e = p['emoji']

        # Detectar intención
        intent, confidence = self.nlp.predict_intent(text) if text else (None, 0)
        intent_str = str(intent) if intent else ''

        # Buscar herramientas relevantes
        tools = suggest_tools(text, role) if text else []

        # Obtener datos reales
        datos = _datos_reales()

        # Generar respuesta con datos REALES
        if 'GREETING' in intent_str:
            saludo = self.humanizer.time_greeting()
            nombre = user_name or role
            resp = (f"{e} {saludo} {nombre}! Soy {p['name']}, tu asistente. "
                    f"Tienes {datos['productos']} productos activos"
                    f"{f' y {datos['stock_bajo']} con stock bajo' if datos['stock_bajo'] else ''}. "
                    f"¿En qué te ayudo?")

        elif 'FINANCE' in intent_str:
            resp = (f"{e} Balance del día:\n"
                    f"💰 Ingresos: {_fmt(datos['ingresos_hoy'])}\n"
                    f"🛒 Ventas: {datos['ventas_hoy']} transacciones\n"
                    f"📊 Ticket promedio: {_fmt(datos['promedio'])}\n"
                    f"📦 Productos activos: {datos['productos']}\n"
                    f"⚠️ Stock bajo: {datos['stock_bajo']}")

        elif 'STOCK' in intent_str:
            try:
                from ia.db_utils import q
                criticos = q("SELECT nombre, stock_actual FROM inventario_general "
                             "WHERE stock_actual<=5 ORDER BY stock_actual LIMIT 8")
                if criticos:
                    lst = '\n'.join(f"  {'🔴' if r['stock_actual']<=2 else '🟡'} "
                                    f"{r['nombre']}: {int(r['stock_actual'])} uds"
                                    for r in criticos)
                    resp = f"{e} Stock que necesita atención:\n{lst}"
                else:
                    resp = f"{e} ✅ Todo el inventario está en niveles saludables."
            except Exception:
                resp = f"{e} {datos['stock_bajo']} productos con stock bajo."

        elif 'SALES' in intent_str:
            resp = (f"{e} Ventas de hoy:\n"
                    f"🛒 {datos['ventas_hoy']} transacciones\n"
                    f"💰 Total: {_fmt(datos['ingresos_hoy'])}\n"
                    f"📊 Promedio: {_fmt(datos['promedio'])}")

        elif 'RECOMMEND' in intent_str or 'OFFERS' in intent_str:
            try:
                from ia.metrics import F
                top = F.top(dias=7, lim=3)
                if top:
                    lst = '\n'.join(f"  ⭐ {t['nombre']}: {int(t['q'])} uds ({_fmt(t['t'])})"
                                    for t in top)
                    resp = f"{e} Recomendaciones basadas en ventas reales:\n{lst}"
                else:
                    resp = f"{e} Aún no hay suficientes ventas para recomendaciones. ¡A vender!"
            except Exception:
                resp = f"{e} Consulta el Dashboard para ver tendencias."

        elif 'GOODBYE' in intent_str:
            resp = f"{e} ¡Hasta luego{', ' + user_name if user_name else ''}! 👋"

        elif 'HELP' in intent_str:
            resp = (f"{e} Soy {p['name']}. Puedo ayudarte con:\n"
                    f"💰 Finanzas y balances\n📦 Inventario y stock\n"
                    f"🛒 Ventas y reportes\n⭐ Recomendaciones\n"
                    f"📊 Métricas y KPIs\n\n¿Qué necesitas?")

        elif tools:
            tools_list = '\n'.join(f"  {t['icon']} {t['name']}: {t['desc'][:60]}" for t in tools[:4])
            resp = f"{e} Herramientas relevantes:\n\n{tools_list}\n\n¿Profundizamos en alguna?"

        else:
            resp = self.humanizer.human_help(role)
            resp = f"{e} {resp}"

        # Humanizar
        resp = self.humanizer.enhance(resp, role)

        return {
            'response': resp,
            'intent': intent_str,
            'confidence': confidence,
            'role': role,
            'tools': tools[:4],
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
        }


agent = AgentPro()
print("🧠 AgentPro v3 cargado — datos REALES de BD")
