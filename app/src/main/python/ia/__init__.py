# -*- coding: utf-8 -*-
"""
Módulo IA - Agente Proactivo v8.0
Desarrollado para TPV Ultra Smart

Modulos conectados:
  - agent_master: Agente principal (integra todos los modulos)
  - agent_pro: Agente proactivo con personalidades
  - nlp_engine: Clasificador de intenciones (TF-IDF + Softmax)
  - tool_system: Catalogo de herramientas con permisos por rol
  - humanizer: Lenguaje humano profesional + blindaje UTF-8
  - memory: Memoria basica (historial en dict)
  - memory_core: Memoria persistente SQLite (core)
  - memory_advanced: Memoria avanzada (extraccion auto, contexto enriquecido)
  - react_core: Motor ReAct para razonamiento multi-paso
  - handlers: Handlers especializados por rol (re-export)
  - handlers_base: Funciones compartidas (_fm, _follow, _get_sug, greet, etc.)
  - handlers_cliente: Handler para rol cliente
  - handlers_staff: Handlers para vendedor, supervisor, admin, dev
  - skills: Skills por dominio (finance, inventory, sales, customer, analytics)
  - fuzzy_match: Coincidencia difusa sin dependencias
  - role_guidance: Misiones y guias por rol
  - guide_manager: Motor de guia contextual
  - metrics: Utilidades financieras y analiticas (F, M)
  - state: Estado persistente del agente (SQLite)
  - catalog: Catalogo de productos (acceso a BD)
  - db_utils: Utilidades de BD y formateo
  - normalizer: Normalizacion de texto para matching difuso
  - guardrails / guardrails_v2: Guardrails de seguridad
  - anti_slop: Anti-repeticion
  - context_memory: Contexto de conversacion
  - session_context: Contexto de sesion
  - intent_engine: Motor de intenciones avanzado
  - proactive_agent: Agente proactivo
  - proactive_routes: Rutas del agente proactivo
  - react_categories: Categorias del motor ReAct
  - react_plans: Planes predefinidos del motor ReAct
  - react_templates: Templates del motor ReAct
"""
__version__ = '8.0.0'
__author__ = 'TPV Team'

# --- Imports seguros con fallbacks ---
# Cada import esta envuelto en try/except para que un modulo fallado
# no rompa todo el sistema. Los modulos se cargan bajo demanda.

# Agentes principales
try:
    from ia.agent_master import AgentMaster, agent as master_agent
except Exception:
    AgentMaster = None
    master_agent = None

try:
    from ia.agent_pro import AgentPro, agent as pro_agent
except Exception:
    AgentPro = None
    pro_agent = None

# NLP y herramientas
try:
    from ia.nlp_engine import NLPEngine
except Exception:
    NLPEngine = None

try:
    from ia.tool_system import TOOLS, get_tools_for_role, suggest_tools, get_help_menu, check_permission
except Exception:
    TOOLS = {}
    get_tools_for_role = None
    suggest_tools = None
    get_help_menu = None
    check_permission = None

try:
    from ia.humanizer import Humanizer
except Exception:
    Humanizer = None

# Memoria
try:
    from ia.memory import Memory
except Exception:
    Memory = None

try:
    from ia.memory_core import init as mem_init, save as mem_save, recall as mem_recall, search as mem_search, forget as mem_forget, get_summary as mem_summary
except Exception:
    mem_init = None
    mem_save = None
    mem_recall = None
    mem_search = None
    mem_forget = None
    mem_summary = None

try:
    from ia.memory_advanced import extract_and_save, get_enriched_context, cleanup as mem_cleanup
except Exception:
    extract_and_save = None
    get_enriched_context = None
    mem_cleanup = None

# ReAct
try:
    from ia.react_core import ReActEngine
except Exception:
    ReActEngine = None

# Handlers
try:
    from ia.handlers import handle_cliente, handle_vendedor, handle_supervisor, handle_admin, handle_dev
except Exception:
    handle_cliente = None
    handle_vendedor = None
    handle_supervisor = None
    handle_admin = None
    handle_dev = None

try:
    from ia.handlers_base import _fm, _follow, _get_sug, greet, handle_products, handle_stock, say_goodbye, handle_unknown
except Exception:
    _fm = None
    _follow = None
    _get_sug = None
    greet = None
    handle_products = None
    handle_stock = None
    say_goodbye = None
    handle_unknown = None

# Skills
try:
    from ia.skills import SkillRegistry, get_registry as get_skill_registry
except Exception:
    SkillRegistry = None
    get_skill_registry = None

# Fuzzy match
try:
    from ia.fuzzy_match import fuzzy_score, best_match, quick_search, contains_frustration
except Exception:
    fuzzy_score = None
    best_match = None
    quick_search = None
    contains_frustration = None

# Role guidance y guia contextual
try:
    from ia.role_guidance import ROLE_MISSIONS, SCREEN_GUIDES
except Exception:
    ROLE_MISSIONS = {}
    SCREEN_GUIDES = {}

try:
    from ia.guide_manager import GuideManager
except Exception:
    GuideManager = None

# Metricas
try:
    from ia.metrics import F, M
except Exception:
    F = None
    M = None

# State management
try:
    from ia.state import create_session, get_session, update_step, complete_session, get_active_sessions
except Exception:
    create_session = None
    get_session = None
    update_step = None
    complete_session = None
    get_active_sessions = None

# Catalogo y DB utils
try:
    from ia.catalog import Catalog
except Exception:
    Catalog = None

try:
    from ia.db_utils import q, fmt_money, pct
except Exception:
    q = None
    fmt_money = None
    pct = None

# Normalizer
try:
    from ia.normalizer import normalize, normalize_preserve, contains_any, extract_entities
except Exception:
    normalize = None
    normalize_preserve = None
    contains_any = None
    extract_entities = None


def get_agent():
    """Devuelve el agente principal disponible (master > pro)."""
    if master_agent is not None:
        return master_agent
    if pro_agent is not None:
        return pro_agent
    return None


def get_all_module_status():
    """Devuelve el estado de todos los modulos IA disponibles."""
    modules = {}
    for name, obj in [
        ('agent_master', AgentMaster),
        ('agent_pro', AgentPro),
        ('nlp_engine', NLPEngine),
        ('tool_system', TOOLS if TOOLS else None),
        ('humanizer', Humanizer),
        ('memory', Memory),
        ('memory_core', mem_init),
        ('memory_advanced', extract_and_save),
        ('react_core', ReActEngine),
        ('handlers', handle_cliente),
        ('skills', SkillRegistry),
        ('fuzzy_match', fuzzy_score),
        ('role_guidance', ROLE_MISSIONS if ROLE_MISSIONS else None),
        ('guide_manager', GuideManager),
        ('metrics', F),
        ('state', create_session),
        ('catalog', Catalog),
        ('db_utils', q),
        ('normalizer', normalize),
    ]:
        modules[name] = obj is not None
    return modules
