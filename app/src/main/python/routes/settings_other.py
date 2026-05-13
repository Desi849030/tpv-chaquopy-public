from routes.settings_bp import settings_bp
from routes.settings_helpers import *
from routes.settings_supabase import _sse_clientes, _sse_lock, _sse_broadcast


@settings_bp.route("/api/sse")
@requiere_login
def api_sse():
    u = usuario_actual()
    uid = u["usuario_id"]
    q = _queue.Queue(maxsize=50)
    with _sse_lock:
        _sse_clientes[uid] = q
    def gen():
        yield f"data: {json.dumps({'tipo':'conectado','rol':u['rol']})}\n\n"
        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield msg
                except _queue.Empty:
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            with _sse_lock:
                _sse_clientes.pop(uid, None)
    return Response(stream_with_context(gen()), mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})

# ══════════════════════════════════════════════════════════════
#  DEBUG
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/api/biometric/check', methods=['GET'])
def api_biometric_check():
    try:
        return jsonify({"ok": True, "biometric": check_biometric_availability()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@settings_bp.route('/api/biometric/setup', methods=['POST'])
@requiere_login
def api_biometric_setup():
    u = usuario_actual()
    return jsonify({"ok": True, "setup": quick_login_setup(u.get("username", ""))})

# ══════════════════════════════════════════════════════════════
#  TOKENIZACIÓN PAGO
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/api/payment/tokenize', methods=['POST'])
@requiere_login
def api_payment_tokenize():
    datos = request.get_json(force=True, silent=True) or {}
    amount = float(datos.get("amount", 0))
    method = datos.get("method", "efectivo")
    card_ref = datos.get("card_ref", "")
    if amount <= 0:
        return jsonify({"error": "Monto invalido"}), 400
    record = create_payment_record(amount, method, card_ref)
    return jsonify({"ok": True, "payment": record})

# ══════════════════════════════════════════════════════════════
#  RLS / SUCURSALES
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/api/branch/info', methods=['GET'])
@requiere_login
def api_branch_info():
    branch_id = get_branch_id()
    headers = get_rls_headers()
    return jsonify({"ok": True, "branch_id": branch_id, "rls_enabled": True, "headers": headers})

@settings_bp.route('/api/branch/filter', methods=['POST'])
@requiere_login
def api_branch_filter():
    datos = request.get_json(force=True, silent=True) or {}
    items = datos.get("items", [])
    from supabase_rls import filter_inventory_by_branch
    filtered = filter_inventory_by_branch(items)
    return jsonify({"ok": True, "filtered": filtered, "count": len(filtered)})

# ══════════════════════════════════════════════════════════════
#  IA CHAT SECURE
# ══════════════════════════════════════════════════════════════

@settings_bp.route('/api/ia/chat/secure', methods=['POST'])
@requiere_login
def ia_chat_secure():
    data = request.get_json(force=True, silent=True) or {}
    query = data.get('query', data.get('question', ''))
    role = session.get('usuario', {}).get('rol', 'cliente')
    from ia_agent import process_question
    response = process_question(session.get('usuario', {}).get('usuario_id', '0'), query, role)
    return jsonify(response)
