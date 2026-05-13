from routes.assistant_helpers import assistant_bp, request, jsonify, requiere_login, _mem_module, mem_save, mem_recall, mem_search, mem_forget, mem_summary
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
