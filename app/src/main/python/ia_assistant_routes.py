# -*- coding: utf-8 -*-
"""
ia_assistant_routes.py - TPV Smart v13.0.0
Rutas Flask del asistente IA. Encoding seguro.

FIX v9.0:
  - Preload ia_assistant at MODULE LEVEL
  - Health check includes DB path verification
  - Better error messages
"""
from flask import Blueprint, request, jsonify, session

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/ia')

# PRELOAD ia_assistant at module level - critical fix for first-request timeout
_ia_module = False
_process_question = None
_get_status = None
_get_proactive_alerts = None
_set_session_role = None
_get_session_info = None
_sessions = None

try:
    from ia_assistant import (
        process_question, get_status, get_proactive_alerts,
        set_session_role, get_session_info, _sessions as _sess
    )
    _process_question = process_question
    _get_status = get_status
    _get_proactive_alerts = get_proactive_alerts
    _set_session_role = set_session_role
    _get_session_info = get_session_info
    _sessions = _sess
    _ia_module = True
except Exception as _e:
    _ia_module = False
    print("[IA Assistant v9.0] ERROR al cargar modulo: %s" % _e)


@assistant_bp.route('/ping')
def ping():
    """Ping rapido para verificar que el modulo IA esta vivo."""
    try:
        if not _ia_module:
            return jsonify({'status': 'error', 'ia_module': False, 'error': 'Module not loaded'})
        info = _get_status()
        return jsonify({'status': 'ok', 'ia_module': True, 'version': info.get('version', '?')})
    except Exception as e:
        return jsonify({'status': 'error', 'ia_module': False, 'error': str(e)})


@assistant_bp.route('/chat', methods=['POST'])
def chat():
    if not _ia_module:
        return jsonify({
            'answer': 'Error: modulo IA no disponible. Reinicia la app.',
            'error': True, 'suggestions': []
        })

    data = request.get_json(silent=True) or {}
    q = data.get('question', '').strip()
    sid = data.get('session_id', 'default')

    role_from_session = session.get('usuario', {}).get('rol', None)
    role_from_param = data.get('role', None)
    role = role_from_session or role_from_param or 'vendedor'
    user_name = session.get('usuario', {}).get('nombre', data.get('user_name', ''))

    if not q:
        return jsonify({
            'answer': 'Escribe algo para que pueda ayudarte.',
            'error': True, 'suggestions': ['ayuda', 'ventas de hoy', 'resumen']
        })

    try:
        result = _process_question(sid, q, role=role, user_name=user_name)
        if not result or not result.get('answer'):
            result = result or {}
            result['answer'] = result.get('answer') or 'No pude generar una respuesta. Intenta de nuevo.'
            result.setdefault('suggestions', [])
        if 'suggestions' not in result:
            result['suggestions'] = []
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'answer': 'Error interno: ' + str(e)[:100],
            'error': str(e), 'intent': 'error',
            'suggestions': ['ayuda', 'ventas de hoy', 'resumen']
        })


@assistant_bp.route('/role', methods=['POST'])
def set_role():
    if not _ia_module:
        return jsonify({'error': 'Modulo IA no disponible'}), 500

    data = request.get_json(silent=True) or {}
    sid = data.get('session_id', 'default')
    role = data.get('role', 'vendedor')
    user_name = data.get('user_name', '')

    if role not in ['desarrollador', 'administrador', 'supervisor', 'vendedor', 'cliente']:
        role = 'vendedor'

    actual_role = _set_session_role(sid, role, user_name)
    info = _get_session_info(sid)
    return jsonify(info)


@assistant_bp.route('/alerts', methods=['GET'])
def alerts():
    try:
        if not _ia_module:
            return jsonify({'alerts': [], 'error': 'Module not loaded'}), 200
        sid = request.args.get('session_id', 'default')
        result = _get_proactive_alerts(sid)
        return jsonify(result)
    except Exception as e:
        return jsonify({'alerts': [], 'error': str(e)}), 200


@assistant_bp.route('/status')
def status():
    try:
        if not _ia_module:
            return jsonify({
                'version': '13.0.0', 'error': 'Module not loaded',
                'current_role': session.get('usuario', {}).get('rol', 'vendedor'),
                'current_user': session.get('usuario', {}).get('nombre', '')
            }), 200
        result = _get_status()
        current_role = session.get('usuario', {}).get('rol', 'vendedor')
        current_user = session.get('usuario', {}).get('nombre', '')
        result['active_sessions'] = len(_sessions) if _sessions else 0
        result['current_role'] = current_role
        result['current_user'] = current_user
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'version': '13.0.0', 'error': str(e),
            'current_role': session.get('usuario', {}).get('rol', 'vendedor'),
            'current_user': session.get('usuario', {}).get('nombre', '')
        }), 200
