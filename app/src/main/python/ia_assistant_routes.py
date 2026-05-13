# -*- coding: utf-8 -*-
"""ia_assistant_routes.py - TPV Smart v1.2 - Compatible con ia_agent.py + memoria persistente"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from decorators import requiere_login

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/ia')

_ia_module = False
_process_question = None
_get_status = None
_get_proactive_alerts = None
_set_session_role = None
_get_session_info = None

try:
    from ia_agent import (
        process_question, get_status, get_proactive_alerts,
        set_session_role, get_session_info
    )
    _process_question = process_question
    _get_status = get_status
    _get_proactive_alerts = get_proactive_alerts
    _set_session_role = set_session_role
    _get_session_info = get_session_info
    _ia_module = True
    # logging: ia_agent ok
except Exception as e:
    try:
        from ia_assistant import (
            process_question, get_status, get_proactive_alerts,
            set_session_role, get_session_info
        )
        _process_question = process_question
        _get_status = get_status
        _get_proactive_alerts = get_proactive_alerts
        _set_session_role = set_session_role
        _get_session_info = get_session_info
        _ia_module = True
    except Exception as e2:
        _ia_module = False

# Importar requiere_login
try:
    from app import requiere_login
except ImportError:
    def requiere_login(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('usuario'):
                return jsonify({'error': 'No autorizado'}), 401
            return f(*args, **kwargs)
        return decorated

# Importar memoria persistente
_mem_module = False
try:
    from ia.memory import (save as mem_save, recall as mem_recall,
        search as mem_search, forget as mem_forget, get_summary as mem_summary,
        extract_and_save as mem_extract, get_enriched_context as mem_context)
    _mem_module = True
    # logging: memoria ok
except Exception:
    _mem_module = False


@requiere_login
@assistant_bp.route('/ping')
def ping():
    try:
        if not _ia_module:
            return jsonify({'status': 'error', 'ia_module': False})
        info = _get_status()
        return jsonify({'status': 'ok', 'ia_module': True, 'version': info.get('version', '?')})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})



@requiere_login
@assistant_bp.route("/public-chat", methods=["POST"])
def public_chat():
    try:
        if not _ia_module:
            return jsonify({"answer": "IA no disponible.", "suggestions": ["productos", "precios"]})
        data = request.get_json(force=True, silent=True) or {}
        q = data.get("question", "").strip()
        if not q:
            return jsonify({"answer": "Escribe algo para ayudarte.", "suggestions": ["productos", "precios", "ofertas"]})
        result = _process_question("public", q, role="cliente", user_name="Cliente", user_session={})
        return jsonify(result)
    except Exception as e:
        return jsonify({"answer": f"Error: {e}", "suggestions": ["productos"]})

@requiere_login
@assistant_bp.route('/chat', methods=['POST'])
def chat():
    if not _ia_module:
        return jsonify({'answer': 'Error: modulo IA no disponible.', 'suggestions': ['ayuda']})
    data = request.get_json(silent=True) or {}
    q = data.get('question', '').strip()
    sid = data.get('session_id', 'default')
    role = data.get('role', session.get('usuario', {}).get('rol', 'cliente'))
    user_name = data.get('user_name', session.get('usuario', {}).get('nombre', ''))
    if not q:
        return jsonify({'answer': 'Escribe algo para ayudarte.', 'suggestions': ['ventas de hoy', 'ayuda']})
    try:
        # Enriquecer contexto con memoria persistente
        if _mem_module:
            mem_ctx = mem_context(sid, q)
            # Se podria inyectar contexto extra en el futuro
            data['_memory'] = mem_ctx

        user_session = session.get("usuario", {})
        result = _process_question(sid, q, role=role, user_name=user_name, user_session=user_session)

        # Extraer y guardar datos clave de esta conversacion
        if _mem_module:
            try:
                mem_extract(sid, q, result.get('intent', 'chat'),
                           result.get('answer', '')[:200], role)
            except Exception:
                pass

        result.setdefault('suggestions', [])
        return jsonify(result)
    except Exception as e:
        return jsonify({'answer': f'Error: {str(e)[:100]}', 'suggestions': ['ayuda']})


@requiere_login
@assistant_bp.route('/role', methods=['POST'])
def set_role():
    if not _ia_module:
        return jsonify({'error': 'Modulo IA no disponible'}), 500
    data = request.get_json(silent=True) or {}
    return jsonify(_set_session_role(data.get('session_id', 'default'), data.get('role', 'cliente'), data.get('user_name', '')))


@requiere_login
@assistant_bp.route('/alerts', methods=['GET'])
def alerts():
    try:
        if not _ia_module:
            return jsonify({'alerts': []})
        return jsonify(_get_proactive_alerts(request.args.get('session_id', 'default')))
    except Exception:
        return jsonify({'alerts': []})


@requiere_login
@assistant_bp.route('/status')
def status():
    try:
        if not _ia_module:
            return jsonify({'version': '15.0.0', 'error': 'Module not loaded'})
        result = _get_status()
        result['current_role'] = session.get('usuario', {}).get('rol', 'cliente')
        result['current_user'] = session.get('usuario', {}).get('nombre', '')
        result['memory_enabled'] = _mem_module
        return jsonify(result)
    except Exception as e:
        return jsonify({'version': '15.0.0', 'error': str(e)})


# ═══════════════════════════════════════════════════════════
#  RUTAS DE MEMORIA PERSISTENTE
# ═══════════════════════════════════════════════════════════

@requiere_login
@assistant_bp.route('/memory/recall', methods=['POST'])
def memory_recall():
    if not _mem_module:
        return jsonify({'memories': [], 'error': 'Modulo memoria no disponible'}), 503
    data = request.get_json(silent=True) or {}
    sid = data.get('session_id', 'default')
    cat = data.get('category')
    key = data.get('key')
    results = mem_recall(sid, category=cat, key=key)
    return jsonify({'ok': True, 'memories': results, 'count': len(results)})


@requiere_login
@assistant_bp.route('/memory/search', methods=['POST'])
def memory_search():
    if not _mem_module:
        return jsonify({'results': [], 'error': 'Modulo memoria no disponible'}), 503
    data = request.get_json(silent=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query requerida'}), 400
    sid = data.get('session_id', 'default')
    cat = data.get('category')
    results = mem_search(query, session_id=sid, category=cat)
    return jsonify({'ok': True, 'results': results, 'count': len(results)})


@requiere_login
@assistant_bp.route('/memory/save', methods=['POST'])
def memory_save():
    if not _mem_module:
        return jsonify({'error': 'Modulo memoria no disponible'}), 503
    data = request.get_json(silent=True) or {}
    sid = data.get('session_id', 'default')
    cat = data.get('category', 'general')
    key = data.get('key', '')
    value = data.get('value', '')
    if not key or not value:
        return jsonify({'error': 'key y value son requeridos'}), 400
    ok = mem_save(sid, cat, key, value, metadata=data.get('metadata'),
                  confidence=data.get('confidence', 1.0),
                  expires_days=data.get('expires_days'))
    return jsonify({'ok': ok})


@requiere_login
@assistant_bp.route('/memory/forget', methods=['POST'])
def memory_forget():
    if not _mem_module:
        return jsonify({'error': 'Modulo memoria no disponible'}), 503
    data = request.get_json(silent=True) or {}
    sid = data.get('session_id', 'default')
    ok = mem_forget(sid, category=data.get('category'), key=data.get('key'))
    return jsonify({'ok': ok})


@requiere_login
@assistant_bp.route('/memory/summary', methods=['GET'])
def memory_summary():
    if not _mem_module:
        return jsonify({'summary': {}, 'error': 'Modulo memoria no disponible'}), 503
    sid = request.args.get('session_id', 'default')
    summary = mem_summary(sid)
    return jsonify({'ok': True, 'summary': summary})


# logging: assistant ok
