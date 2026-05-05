# -*- coding: utf-8 -*-
"""ia_assistant_routes.py - TPV Smart v1.1 - Compatible con ia_agent.py"""
from flask import Blueprint, request, jsonify, session

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
    print("[IA Routes v1.1] ia_agent.py cargado correctamente")
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

try:
    from app import requiere_login
except ImportError:
    def requiere_login(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('usuario'):
                return jsonify({'error': 'No autorizado'}), 401
            return f(*args, **kwargs)
        return decorated

@assistant_bp.route('/ping')
def ping():
    try:
        if not _ia_module:
            return jsonify({'status': 'error', 'ia_module': False})
        info = _get_status()
        return jsonify({'status': 'ok', 'ia_module': True, 'version': info.get('version', '?')})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@assistant_bp.route('/chat', methods=['POST'])
@requiere_login
def chat():
    if not _ia_module:
        return jsonify({'answer': 'Error: modulo IA no disponible.', 'suggestions': ['ayuda']})
    data = request.get_json(silent=True) or {}
    q = data.get('question', '').strip()
    sid = data.get('session_id', 'default')
    role = session.get('usuario', {}).get('rol', data.get('role', 'vendedor'))
    user_name = session.get('usuario', {}).get('nombre', data.get('user_name', ''))
    if not q:
        return jsonify({'answer': 'Escribe algo para ayudarte.', 'suggestions': ['ventas de hoy', 'ayuda']})
    try:
        result = _process_question(sid, q, role=role, user_name=user_name)
        result.setdefault('suggestions', [])
        return jsonify(result)
    except Exception as e:
        return jsonify({'answer': f'Error: {str(e)[:100]}', 'suggestions': ['ayuda']})

@assistant_bp.route('/role', methods=['POST'])
@requiere_login
def set_role():
    if not _ia_module:
        return jsonify({'error': 'Modulo IA no disponible'}), 500
    data = request.get_json(silent=True) or {}
    return jsonify(_set_session_role(data.get('session_id','default'), data.get('role','vendedor'), data.get('user_name','')))

@assistant_bp.route('/alerts', methods=['GET'])
@requiere_login
def alerts():
    try:
        if not _ia_module:
            return jsonify({'alerts': []})
        return jsonify(_get_proactive_alerts(request.args.get('session_id', 'default')))
    except:
        return jsonify({'alerts': []})

@assistant_bp.route('/status')
def status():
    try:
        if not _ia_module:
            return jsonify({'version': '15.0.0', 'error': 'Module not loaded'})
        result = _get_status()
        result['current_role'] = session.get('usuario', {}).get('rol', 'vendedor')
        result['current_user'] = session.get('usuario', {}).get('nombre', '')
        return jsonify(result)
    except Exception as e:
        return jsonify({'version': '15.0.0', 'error': str(e)})

print("[ia_assistant_routes.py v1.1] Listo")
