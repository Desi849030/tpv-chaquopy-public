# -*- coding: utf-8 -*-
"""AgentMaster - Agente IA del TPV Ultra Smart v8.0
Integra: memoria avanzada, handlers por rol, fuzzy match, skills, metricas."""

import json, random, time, logging
from datetime import datetime
from ia.nlp_engine import NLPEngine
from ia.tool_system import TOOLS
from ia.humanizer import Humanizer

# --- Modulos avanzados con importacion segura ---
try:
    from ia.memory_advanced import (
        extract_and_save, get_enriched_context, get_summary as mem_summary,
        cleanup as mem_cleanup, recall, search as mem_search,
        forget as mem_forget, save as mem_save, init as mem_init
    )
    _HAS_ADV_MEMORY = True
except Exception:
    _HAS_ADV_MEMORY = False

try:
    from ia.react_core import ReActEngine
    _HAS_REACT = True
except Exception:
    _HAS_REACT = False

try:
    from ia.handlers import (
        handle_cliente, handle_vendedor, handle_supervisor,
        handle_admin, handle_dev
    )
    _HAS_HANDLERS = True
except Exception:
    try:
        from ia.handlers_cliente import handle_cliente
        from ia.handlers_staff import handle_vendedor, handle_supervisor, handle_admin, handle_dev
        _HAS_HANDLERS = True
    except Exception:
        _HAS_HANDLERS = False

try:
    from ia.fuzzy_match import fuzzy_score, best_match, quick_search, contains_frustration
    _HAS_FUZZY = True
except Exception:
    _HAS_FUZZY = False

try:
    from ia.skills import get_registry as get_skill_registry
    _HAS_SKILLS = True
except Exception:
    _HAS_SKILLS = False

try:
    from ia.metrics import F, M
    _HAS_METRICS = True
except Exception:
    _HAS_METRICS = False

logger = logging.getLogger(__name__)


class AgentMaster:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS
        self.sessions = {}

        # Memoria avanzada
        self.adv_memory_ok = _HAS_ADV_MEMORY
        if self.adv_memory_ok:
            try:
                mem_init()
            except Exception:
                self.adv_memory_ok = False

        # Motor ReAct
        self.react_engine = None
        if _HAS_REACT:
            try:
                self.react_engine = ReActEngine()
            except Exception:
                pass

        # Skills
        self.skill_registry = None
        if _HAS_SKILLS:
            try:
                self.skill_registry = get_skill_registry()
            except Exception:
                pass

        # Metricas
        self._usage_metrics = {
            'total_queries': 0,
            'by_role': {},
            'start_time': datetime.now().isoformat(),
            'errors': 0,
        }

        # Mapa de roles a iconos
        self.role_icons = {
            'desarrollador': '🔧',
            'administrador': '📊',
            'supervisor': '👁️',
            'vendedor': '💼',
            'cajero': '💵',
            'cliente': '🛍️',
        }

    def process(self, text, role='cliente', name='', **kwargs):
        """Punto de entrada principal - procesa mensaje y devuelve respuesta."""
        if not text or not text.strip():
            return {
                "response": self.humanizer.enhance(
                    self._greet(role, name), role
                ),
                "intent": "GREETING",
                "confidence": 1.0,
                "tools": [],
                "ui_action": None,
            }

        t = text.lower().strip()
        start = time.time()
        response = ""
        intent = "GENERAL"
        tools_used = []
        confidence = 0.85
        ui_action = None

        # Detectar acciones de UI
        if role in ('vendedor', 'cajero'):
            if any(w in t for w in ['cobrar', 'pagar', 'carrito', 'venta']):
                ui_action = "OPEN_CART"
        if role in ('administrador', 'desarrollador'):
            if any(w in t for w in ['dashboard', 'graficos', 'panel']):
                ui_action = "OPEN_DASHBOARD"
        if any(w in t for w in ['catalogo', 'productos', 'inventario']):
            ui_action = "OPEN_CATALOG"

        # Detectar intents simples
        if any(w in t for w in ['hola', 'buenos', 'buenas', 'hey', 'saludos']):
            intent = "GREETING"
            response = self.humanizer.enhance(self._greet(role, name), role)
            return {"response": response, "intent": intent, "confidence": 1.0,
                    "tools": [], "ui_action": ui_action}

        if any(w in t for w in ['gracias', 'adios', 'hasta luego', 'chao']):
            intent = "FAREWELL"
            closer = self.humanizer.get_closer(role)
            return {"response": closer, "intent": intent, "confidence": 1.0,
                    "tools": [], "ui_action": None}

        if any(w in t for w in ['ayuda', 'qué puedes', 'opciones', 'menu']):
            intent = "HELP"
            response = self.humanizer.human_help(role)
            return {"response": response, "intent": intent, "confidence": 1.0,
                    "tools": [], "ui_action": None}

        # Dispatch por rol
        if _HAS_HANDLERS:
            try:
                if role == 'cliente':
                    response = handle_cliente(self, t, {})
                elif role == 'vendedor':
                    response = handle_vendedor(self, t, name)
                elif role == 'supervisor':
                    response = handle_supervisor(self, t, name)
                elif role == 'administrador':
                    response = handle_admin(self, t, name)
                elif role == 'desarrollador':
                    response = handle_dev(self, t, name)
                else:
                    response = handle_cliente(self, t, {})
            except Exception as e:
                logger.error("Handler error: %s", e)
                response = f"Ocurrió un error al procesar tu solicitud: {e}"
        else:
            response = "El motor de handlers no está disponible."

        # Humanizar
        response = self.humanizer.enhance(response, role)

        # Métricas
        elapsed = (time.time() - start) * 1000
        self._usage_metrics['total_queries'] += 1
        self._usage_metrics['by_role'][role] = self._usage_metrics['by_role'].get(role, 0) + 1

        return {
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "tools": tools_used,
            "ui_action": ui_action,
            "response_time_ms": round(elapsed, 1),
        }

    def _greet(self, role, name):
        h = datetime.now().hour
        if h < 12:
            saludo = "Buenos días"
        elif h < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        icon = self.role_icons.get(role, '👋')
        n = name or role

        if role == 'cliente':
            return f"{saludo} {icon} ¡Bienvenido! Soy el asistente de la tienda. Puedo ayudarte a buscar productos, ver precios y ofertas."
        elif role == 'vendedor':
            return f"{saludo} {n} {icon} Listo para vender. Pregúntame por ventas de hoy, stock o precios."
        elif role == 'administrador':
            return f"{saludo} Admin {n} {icon} Sistemas operativos. Pídeme balance, gastos, rendimiento o inventario."
        elif role == 'supervisor':
            return f"{saludo} {n} {icon} Panel de supervisión activo. Dashboard, ABC, tendencias."
        elif role == 'desarrollador':
            return f"{saludo} {n} {icon} Root Access concedido. Telemetría, DB, logs, métricas."
        else:
            return f"{saludo} {icon} ¿En qué te ayudo?"

    def get_status(self):
        return {
            'active': True,
            'handlers': _HAS_HANDLERS,
            'fuzzy': _HAS_FUZZY,
            'memory': self.adv_memory_ok,
            'skills': _HAS_SKILLS,
            'react': self.react_engine is not None,
            'metrics': self._usage_metrics,
        }


# ══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL - Esto es lo que importa agent_chat_bp.py
# ══════════════════════════════════════════════════════════════
agent = AgentMaster()
