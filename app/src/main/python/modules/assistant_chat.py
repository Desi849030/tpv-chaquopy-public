from decorators import login_required
from modules.assistant_helpers import assistant_bp, request, jsonify, session, requiere_login, _ia_module, _process_question, _get_status, _get_proactive_alerts, _set_session_role, _get_session_info, _mem_module, mem_extract, mem_context
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
            except Exception:  # noqa: broad-except - graceful degradation
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

