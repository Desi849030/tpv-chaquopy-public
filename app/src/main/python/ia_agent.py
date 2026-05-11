"""ia_agent.py v2.0 - TPV Smart - Gestor Total Conversacional (modular)

Arquitectura:
  ia/db_utils.py   -> BD + formatos
  ia/catalog.py    -> P (productos) + O (ofertas)
  ia/metrics.py    -> M (matematicas) + F (finanzas)
  ia/handlers.py   -> Handlers por rol (cliente, vendedor, supervisor, admin, dev)
  ia_agent.py      -> Agent orchestrator + entry points
"""
import threading
from datetime import datetime
from reasoning_engine import ReActEngine

from ia.nlp_engine import NLPEngine
from ia.guardrails import Guardrails
from ia.session_context import SessionContext
from ia.humanizer import Humanizer

# --- Optional modules (graceful degradation) ---
try:
    from ia.normalizer import normalize, contains_any, extract_entities
    _HAS_NORM = True
except Exception:
    _HAS_NORM = False

try:
    from ia.intent_engine import detect_intents as _detect_intents, get_suggestions as _get_suggestions
    _HAS_INTENT = True
except Exception:
    _HAS_INTENT = False

try:
    from ia.context_memory import get_context as _get_ctx
    _HAS_CTX = True
except Exception:
    _HAS_CTX = False

try:
    from ia.skills import get_registry as _get_skills_registry
    _HAS_SKILLS = True
except Exception:
    _HAS_SKILLS = False

try:
    from ia.memory import (save as _mem_save, recall as _mem_recall,
                           search as _mem_search, extract_and_save as _mem_extract,
                           get_enriched_context as _mem_context)
    _HAS_MEM = True
except Exception:
    _HAS_MEM = False

try:
    from ia.anti_slop import refine as _anti_slop
    _HAS_ANTI_SLOP = True
except Exception:
    _HAS_ANTI_SLOP = False

# --- Import modular components ---
from ia.catalog import P, O
from ia.handlers import (
    greet, help_text, _follow, _get_sug, _fm,
    handle_cliente, handle_vendedor, handle_supervisor,
    handle_admin, handle_dev,
)
from ia.db_utils import q


# ====================================================================
# ROLES REGISTRY
# ====================================================================
ROLES = {
    'cliente':      {'label': 'Cliente',      'color': '#2ecc71', 'icon': 'C'},
    'vendedor':     {'label': 'Vendedor',     'color': '#3498db', 'icon': 'V'},
    'supervisor':   {'label': 'Supervisor',   'color': '#f39c12', 'icon': 'S'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
}


# ====================================================================
# AGENT CLASS (slim orchestrator)
# ====================================================================
class Agent:
    def __init__(self):
        self.ses = {}
        self.lk = threading.Lock()
        self.nlp = NLPEngine()
        self.guard = Guardrails()
        self.memory = SessionContext()
        self.humanizer = Humanizer()
        self._mem_ok = _HAS_MEM
        self._as_ok = _HAS_ANTI_SLOP
        self._sk_ok = _HAS_SKILLS
        self._skills = _get_skills_registry() if _HAS_SKILLS else None

    def _get_mem(self, sid):
        """Get or create session memory."""
        with self.lk:
            if sid not in self.ses:
                self.ses[sid] = {'h': [], 't': '', 'p': '', 'n': ''}
            return self.ses[sid]

    def process(self, text, sid='0', role='cliente', name=''):
        """Main entry point - process user message and return response."""
        if not text or not text.strip():
            return self._r(greet(role, name), role, 'GREETING')

        t = text.lower().strip()
        m = self._get_mem(sid)
        m['h'].append(t)
        if len(m['h']) > 20:
            m['h'] = m['h'][-20:]

        # === AGENTIC PIPELINE ===
        # 1. Intent detection
        intents = []
        sug = []
        try:
            if _HAS_INTENT:
                intents = _detect_intents(t, role)
                if intents:
                    sug = _get_sug(intents[0]['intent'], role)
        except:
            pass

        # 2. Contextual memory: resolve references
        ctx = None
        try:
            if _HAS_CTX:
                ctx = _get_ctx(sid)
                ref = ctx.resolve_reference(text)
                if ref.get('query') and len(t.split()) <= 5 and not P.search(t, 1):
                    t = ref['query']
        except:
            pass

        primary = intents[0]['intent'] if intents else 'GENERAL'

        # SALUDOS
        if primary == 'GREETING':
            if ctx:
                ctx.add_turn(text, '', primary)
            return self._r(greet(role, name), role, primary, sug)

        # DESPEDIDAS
        if primary == 'FAREWELL':
            return self._r('Ha sido un placer. Estoy aqui cuando me necesite.',
                           role, primary, sug)

        # AYUDA
        if primary == 'HELP':
            return self._r(help_text(role), role, primary, sug)

        # FRUSTRACION
        if primary == 'FRUSTRATION':
            return self._r('Detecto que algo no va bien. Estoy aqui para ayudarle. Que problema tiene?',
                           role, primary, ['ayuda'])

        # === DISPATCH POR ROL ===
        if role == 'cliente':
            result = handle_cliente(self, t, m)
        elif role == 'vendedor':
            result = handle_vendedor(self, t, m)
        elif role == 'supervisor':
            result = handle_supervisor(self, t, m)
        elif role == 'administrador':
            result = handle_admin(self, t, name)
        else:
            result = handle_dev(self, t, name)

        # Update contextual memory
        if ctx:
            ctx.add_turn(text, result, primary)
            try:
                prods = P.search(text, 1)
                if prods:
                    ctx.last_product = prods[0]['n']
            except:
                pass

        # Proactive: low stock alert
        try:
            if ctx and ctx.last_product:
                lp = ctx.last_product.lower()
                for p in P.cache:
                    if p['n'].lower() == lp and 0 < p['s'] <= 3:
                        result += ('\n\n[!] Alerta: ' + p['n'] +
                                   ' tiene solo ' + str(int(p['s'])) + ' unidades.')
                        break
        except:
            pass

        return self._r(result, role, primary, sug)

    def _r(self, msg, role, intent='GENERAL', suggestions=None):
        """Build standard response dict."""
        msg = self.humanizer.sanitize_text(msg)
        if suggestions is None:
            suggestions = []
        return {
            'answer': msg,
            'role': role,
            'suggestions': suggestions,
            'intent': intent,
            'ts': datetime.now().isoformat(),
        }


# ====================================================================
# MODULE-LEVEL ENTRY POINTS
# ====================================================================
_agent = None
_lk = threading.Lock()


def _get():
    """Get singleton Agent instance."""
    global _agent
    if not _agent:
        with _lk:
            if not _agent:
                _agent = Agent()
    return _agent


def process_question(sid, question, role='cliente', user_name='', user_session=None):
    """Public API: process a question and return formatted response.
    Tries agentic (ReAct) first, falls back to classic handlers."""
    ts = datetime.now().isoformat()
    rl = ROLES.get(role, {}).get('label', 'Usuario')
    rc = ROLES.get(role, {}).get('color', '#3498db')
    ri = ROLES.get(role, {}).get('icon', '?')

    # --- AGENTIC FIRST: ReAct with tools ---
    try:
        # Try to get Flask app for agentic mode (works in production)
        _app = None
        try:
            from flask import current_app
            _app = current_app._get_current_object()
        except Exception:
            pass
        agentic = _agentic_gateway(question, user_id=sid, flask_app=_app)
        if agentic and agentic.get('response'):
            return {
                'answer': agentic['response'],
                'intent': 'agentic',
                'suggestions': [],
                'role': role,
                'role_label': rl,
                'role_color': rc,
                'role_icon': ri,
                'ts': ts,
                'mode': 'agentic',
                'tools_used': agentic.get('tools_used', []),
                'reasoning_log': agentic.get('reasoning_log', []),
            }
    except Exception:
        pass

    # --- CLASSIC FALLBACK: role-based handlers ---
    r = _get().process(question, sid, role, user_name)
    return {
        'answer': r['answer'],
        'intent': r.get('intent', 'chat'),
        'suggestions': r.get('suggestions', []),
        'role': role,
        'role_label': rl,
        'role_color': rc,
        'role_icon': ri,
        'ts': r['ts'],
    }


def get_status():
    """Get IA system status."""
    P.refresh()
    return {
        'versión': '2.0.0',
        'model': 'Gestor Total Conversacional (modular)',
        'status': 'active',
        'features': ['ABC', 'Regresion', 'EOQ', 'Punto Equilibrio',
                     'Rotacion', 'Ofertas', 'Gastos', 'Comisiones',
                     'Predicciones'],
        'modules': ['ia.db_utils', 'ia.catalog', 'ia.metrics', 'ia.handlers'],
    }


def get_conversation_history(sid='0'):
    return []


def get_proactive_alerts(sid='0'):
    a = []
    low = q("SELECT COUNT(*) c FROM inventario_general "
            "WHERE stock_actual<=3 AND stock_actual>=0", one=True)
    if low and low['c'] > 0:
        a.append({
            'type': 'warning',
            'icon': '!',
            'msg': f'{low["c"]} productos necesitan reabastecimiento urgente'
        })
    return {'alerts': a}


def set_session_role(sid, role, name=''):
    return role


def get_session_info(sid):
    return {'role': 'cliente', 'role_label': 'Cliente',
            'role_color': '#2ecc71', 'role_icon': 'C'}


# ====================================================================
# AGENTIC GATEWAY
# ====================================================================
def _agentic_gateway(message, user_id="default", flask_app=None):
    """Gateway: decide si usar razonamiento agentic o respuesta clasica."""
    try:
        kwargs = {"user_id": user_id}
        if flask_app:
            kwargs["flask_app"] = flask_app
        engine = ReActEngine(**kwargs)
        result = engine.reason(message)
        if result.get("tools_used") or result.get("tool_used"):
            return {
                "response": result.get("response", ""),
                "mode": "agentic",
                "reasoning_log": result.get("reasoning_log", []),
                "tools_used": result.get("tools_used", []),
                "session_id": result.get("session_id"),
            }
    except Exception:
        pass
    return None


print("Gestor Total Conversacional v2.0 modular activo")
