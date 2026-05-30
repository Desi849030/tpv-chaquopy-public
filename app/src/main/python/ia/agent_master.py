"""AgentMaster - Agente IA del TPV"""
import json, random
from datetime import datetime
from ia.nlp_engine import NLPEngine
from ia.tool_system import TOOLS
from ia.humanizer import Humanizer

class AgentMaster:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS
        self.sessions = {}
        
        self.role_icons = {
            'desarrollador': '🔧', 'administrador': '📊', 
            'supervisor': '👁️', 'vendedor': '💼',
            'cajero': '💵', 'cliente': '🛍️'
        }
        
        self.privilegios = {
            'desarrollador': ['sistema', 'seguridad', 'usuarios', 'privilegios', 'bd', 'logs', 'ventas', 'inventario', 'productos', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'administrador': ['ventas', 'inventario', 'productos', 'usuarios', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'supervisor': ['ventas', 'productos', 'reportes', 'metricas', 'catalogo'],
            'vendedor': ['ventas', 'catalogo', 'clientes'],
            'cajero': ['ventas', 'catalogo']
        }
    
    def process(self, text, role='vendedor', user_name=''):
        session_id = f"sess_{random.randint(100000,999999)}"
        icon = self.role_icons.get(role, '🤖')
        poderes = self.privilegios.get(role, ['catalogo', 'ventas'])
        
        # NLP real + fallback a keywords
        intent, conf = self.nlp.predict_intent(text) if text else (None, 0)
        # Fallback: si NLP no detecta, usar keywords
        if not intent or conf < 0.6:
            tl = text.lower() if text else ''
            if any(kw in tl for kw in ['recomiendame','recomendar','sugerir']):
                intent, conf = ('RECOMMEND', 0.7)
            elif any(kw in tl for kw in ['stock','inventario','critico','agotado']):
                intent, conf = ('STOCK', 0.7)
            elif any(kw in tl for kw in ['finanza','balance','ganancia','margen']):
                intent, conf = ('FINANCE', 0.7)
            elif any(kw in tl for kw in ['venta','cuanto vendi','caja']):
                intent, conf = ('SALES', 0.7)
            elif any(kw in tl for kw in ['hola','buenos dias','saludos']):
                intent, conf = ('GREETING', 0.7)
        intent_str = str(intent) if intent else ''
        
        tools = []
        text_low = text.lower()
        for tname, tinfo in self.tools.items():
            if role in tinfo.get('roles', []):
                if any(kw in text_low for kw in tinfo.get('keywords', [])):
                    tools.append({'name': tname, 'icon': tinfo.get('icon', '🔧'), 'desc': tinfo.get('desc', '')})
        
        # Humanizar respuesta
        # Intentar herramienta automática primero
        resp = self._respond(text, intent_str, role, user_name, icon, poderes, tools)
        try:
            resp = self.humanizer.enhance(resp, role)
        except:
            pass
        
        # Guardar en memoria simple
        self.sessions[session_id] = {"text": text, "role": role, "time": datetime.now().isoformat()}
        
        return {
            'response': resp,
            'intent': str(intent),
            'confidence': conf,
            'role': role,
            'privilegios': poderes,
            'tools': tools,
            'session_id': session_id
        }
    
    def _respond(self, text, intent, role, name, icon, poderes, tools):
        nombre = name or role.capitalize()
        
        if 'GREETING' in intent or not text:
            priv = ', '.join(poderes[:6])
            return f"{icon} ¡Hola {nombre}! Bienvenido al TPV.\n\nTu rol: {role}\nAcceso a: {priv}\nProductos: 12 | Ventas hoy: $3,250\n\n¿En qué puedo ayudarte?"
        
        if 'FINANCE' in intent:
            if 'ventas' in poderes or 'reportes' in poderes:
                return f"{icon} Balance Financiero:\n💰 Ventas hoy: $3,250 (12 transacciones)\n📊 Ventas mes: $45,230\n📈 Margen: 28%\n💵 Ganancia hoy: $890\n\nTop: Arroz Premium $637.50"
            return f"{icon} No tienes acceso a finanzas con tu rol actual."
        
        if 'STOCK' in intent:
            if 'inventario' in poderes:
                return f"{icon} Inventario:\n📦 Total: 12 productos | ✅ Stock: 10\n🔴 Críticos: Jabón Líquido (25u), Pan Integral (20u)\n🟡 Atención: Huevos (35u)\n🟢 Óptimo: Arroz, Leche, Refresco"
            return f"{icon} Stock bajo: Jabón Líquido (25u) y Pan Integral (20u)."
        
        if 'SALES' in intent:
            if 'ventas' in poderes:
                return f"{icon} Ventas Hoy:\n🛒 12 transacciones | $3,250\n📊 Promedio: $270.83\n⭐ Top: Arroz Premium (5)\n💳 Efectivo: 65% | Tarjeta: 35%"
            return f"{icon} Hoy: 12 ventas por $3,250. ¿Registramos una nueva?"
        
        if 'RECOMMEND' in intent or 'OFFERS' in intent:
            return f"{icon} Recomendaciones:\n⭐ Estrella: Arroz Premium (40% margen)\n📈 Tendencia: Café Molido (+15%)\n🏷️ Oferta ideal: Frijoles (50% margen)\n🎯 Oportunidad: Combo Despensa $79.25"
        
        if tools:
            tlist = '\n'.join([f"  {t['icon']} {t['name']}: {t['desc'][:80]}" for t in tools[:4]])
            return f"{icon} Herramientas disponibles:\n\n{tlist}"
        
        return f"{icon} Como {role}, puedes: {', '.join(poderes[:5])}.\n\n¿Qué necesitas?"

agent = AgentMaster()
