"""AgentMaster - Agente IA del TPV Ultra Smart v8.0
Integra: memoria avanzada, ReAct reasoning, handlers por rol,
fuzzy match, skills, role guidance, metricas, guide manager y state."""
import json, random, time, logging
from datetime import datetime
from ia.nlp_engine import NLPEngine
from ia.tool_system import TOOLS
from ia.humanizer import Humanizer

# --- Modulos avanzados con importacion segura ---
# Memoria avanzada (SQLite persistente)
try:
    from ia.memory_advanced import (
        extract_and_save, get_enriched_context, get_summary as mem_summary,
        cleanup as mem_cleanup, recall, search as mem_search,
        forget as mem_forget, save as mem_save, init as mem_init
    )
    _HAS_ADV_MEMORY = True
except Exception:
    _HAS_ADV_MEMORY = False

# Motor ReAct para razonamiento complejo
try:
    from ia.react_core import ReActEngine
    _HAS_REACT = True
except Exception:
    _HAS_REACT = False

# Handlers especializados por rol
try:
    from ia.handlers import (
        handle_cliente, handle_vendedor, handle_supervisor,
        handle_admin, handle_dev
    )
    _HAS_HANDLERS = True
except Exception:
    _HAS_HANDLERS = False

if not _HAS_HANDLERS:
    try:
        from ia.handlers_cliente import handle_cliente
        from ia.handlers_staff import handle_vendedor, handle_supervisor, handle_admin, handle_dev
        _HAS_HANDLERS = True
    except Exception:
        _HAS_HANDLERS = False

# Fuzzy match para busqueda de productos
try:
    from ia.fuzzy_match import fuzzy_score, best_match, quick_search, contains_frustration
    _HAS_FUZZY = True
except Exception:
    _HAS_FUZZY = False

# Skills (enriquecimiento de respuestas por dominio)
try:
    from ia.skills import get_registry as get_skill_registry
    _HAS_SKILLS = True
except Exception:
    _HAS_SKILLS = False

# Role guidance (misiones y guias por rol)
try:
    from ia.role_guidance import ROLE_MISSIONS, SCREEN_GUIDES
    _HAS_ROLE_GUIDANCE = True
except Exception:
    _HAS_ROLE_GUIDANCE = False

# Guide manager (guia contextual)
try:
    from ia.guide_manager import GuideManager
    _HAS_GUIDE = True
except Exception:
    _HAS_GUIDE = False

# Metricas financieras y analiticas
try:
    from ia.metrics import F, M
    _HAS_METRICS = True
except Exception:
    _HAS_METRICS = False

# State management (sesiones de agente persistentes)
try:
    from ia.state import create_session, get_session, update_step, complete_session, get_active_sessions
    _HAS_STATE = True
except Exception:
    _HAS_STATE = False

logger = logging.getLogger(__name__)


class AgentMaster:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS
        # Memoria basica (fallback si memoria avanzada no esta disponible)
        self.sessions = {}

        # Inicializar memoria avanzada
        self.adv_memory_ok = _HAS_ADV_MEMORY
        if self.adv_memory_ok:
            try:
                mem_init()
                logger.info("[AgentMaster] Memoria avanzada (SQLite) activa")
            except Exception as e:
                self.adv_memory_ok = False
                logger.warning("[AgentMaster] Memoria avanzada no disponible: %s", e)

        # Motor ReAct
        self.react_engine = None
        if _HAS_REACT:
            try:
                self.react_engine = ReActEngine()
                logger.info("[AgentMaster] Motor ReAct cargado (%d herramientas)",
                            self.react_engine.get_status().get('tools_loaded', 0))
            except Exception as e:
                logger.warning("[AgentMaster] ReAct no disponible: %s", e)

        # Skills registry
        self.skill_registry = None
        if _HAS_SKILLS:
            try:
                self.skill_registry = get_skill_registry()
                logger.info("[AgentMaster] Skills registry activo (%d skills)",
                            len(self.skill_registry.skills))
            except Exception as e:
                logger.warning("[AgentMaster] Skills no disponible: %s", e)

        # Guide manager (se inicializa por rol al procesar)
        self._guide_managers = {}

        # Metricas de uso del IA (contador en memoria)
        self._usage_metrics = {
            'total_queries': 0,
            'by_role': {},
            'by_intent': {},
            'by_hour': {},
            'start_time': datetime.now().isoformat(),
            'errors': 0,
            'avg_response_time_ms': 0,
            '_total_time_ms': 0
        }

        # Mapa de roles a iconos
        self.role_icons = {
            'desarrollador': '🔧', 'administrador': '📊',
            'supervisor': '👁️', 'vendedor': '💼',
            'cajero': '💵', 'cliente': '🛍️'
        }

        # Privilegios por rol
        self.privilegios = {
            'desarrollador': ['sistema', 'seguridad', 'usuarios', 'privilegios', 'bd', 'logs', 'ventas', 'inventario', 'productos', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'administrador': ['ventas', 'inventario', 'productos', 'usuarios', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'supervisor': ['ventas', 'productos', 'reportes', 'metricas', 'catalogo'],
            'vendedor': ['ventas', 'catalogo', 'clientes'],
            'cajero': ['ventas', 'catalogo']
        }

        # Handlers por rol
        self._role_handlers = {}
        if _HAS_HANDLERS:
            self._role_handlers = {
                'cliente': handle_cliente,
                'vendedor': handle_vendedor,
                'supervisor': handle_supervisor,
                'administrador': handle_admin,
                'desarrollador': handle_dev,
            }

        logger.info("[AgentMaster] v8.0 inicializado - Memoria:%s ReAct:%s Handlers:%s Fuzzy:%s Skills:%s RoleGuide:%s Metrics:%s State:%s",
                    self.adv_memory_ok, _HAS_REACT, _HAS_HANDLERS, _HAS_FUZZY,
                    _HAS_SKILLS, _HAS_ROLE_GUIDANCE, _HAS_METRICS, _HAS_STATE)

    # ----------------------------------------------------------------
    # Metodo principal: procesar mensaje del usuario
    # ----------------------------------------------------------------
# Este es un parche rápido para inyectar en agent_master.py
def _patched_process(self, text, role='cliente', name='', sid=None, **kwargs):
    # Si envían sid como argumento nombrado en kwargs, lo atrapamos sin romper
    import time
    start_time = time.time()
    
    response = ""
    intent = "GENERAL"
    tools_used = []
    confidence = 0.8
    ui_action = None

    # Detectar acciones de UI embebidas en el texto
    t_lower = text.lower()
    if role in ['vendedor', 'cajero'] and any(w in t_lower for w in ['cobrar', 'pagar', 'carrito', 'venta']):
        ui_action = "OPEN_CART"
    elif role in ['administrador', 'desarrollador'] and any(w in t_lower for w in ['dashboard', 'graficos', 'panel']):
        ui_action = "OPEN_DASHBOARD"
    elif any(w in t_lower for w in ['catalogo', 'inventario', 'productos']):
        ui_action = "OPEN_CATALOG"

    # Enviar al handler correspondiente
    if role == 'cliente':
        from ia.handlers_cliente import handle_cliente
        response = handle_cliente(self, text, {})
    elif role == 'vendedor':
        from ia.handlers_staff import handle_vendedor
        response = handle_vendedor(self, text, name)
    elif role == 'administrador':
        from ia.handlers_staff import handle_admin
        response = handle_admin(self, text, name)
    elif role == 'supervisor':
        from ia.handlers_staff import handle_supervisor
        response = handle_supervisor(self, text, name)
    elif role == 'desarrollador':
        from ia.handlers_staff import handle_dev
        response = handle_dev(self, text, name)
    else:
        from ia.handlers_cliente import handle_cliente
        response = handle_cliente(self, text, {})

    # Humanizar
    response = self.humanizer.enhance(response, role)

    return {
        "response": response,
        "intent": intent,
        "confidence": confidence,
        "tools": tools_used,
        "ui_action": ui_action
    }
