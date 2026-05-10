"""Rutas de estado, supabase, SSE, debug, biometric, payment, branch, IA"""
import json, os, time, threading, webbrowser, queue as _queue
import urllib.request
from datetime import datetime
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    cargar_estado, guardar_estado, agregar_log, crear_tablas,
    obtener_info_db, DB_FILE,
)
from supabase_sync import (
    obtener_config_actual, actualizar_config,
    cargar_desde_supabase, guardar_en_supabase,
    sincronizar_todo, sincronizar_subida, probar_conexion,
    verificar_tablas_supabase, setup_supabase, obtener_sql_completo,
    guardar_historial_diario, obtener_historial_diario,
    obtener_historial_detalle, TABLAS_SQL,
)
import supabase_sync as _sb
from biometric_auth import check_biometric_availability, quick_login_setup
from payment_tokenizer import create_payment_record
from supabase_rls import get_branch_id, get_rls_headers

settings_bp = Blueprint('settings', __name__)

# ══════════════════════════════════════════════════════════════
#  ESTADO TPV
# ══════════════════════════════════════════════════════════════

@settings_bp.route("/api/state", methods=["GET"])
@requiere_login
def get_state():
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin estado local"}), 404
    return jsonify({"ok": True, "estado": estado})

@settings_bp.route("/api/state", methods=["POST"])
@requiere_login
def save_state():
    try:
        estado = request.get_json(force=True)
        if not isinstance(estado, dict):
            return jsonify({"error": "JSON invalido"}), 400
        guardar_estado(estado)
        if _sb.SUPABASE_OK:
            threading.Thread(target=sincronizar_subida, args=(estado,), daemon=True).start()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  STATUS / PING / HEALTH
# ══════════════════════════════════════════════════════════════

@settings_bp.route("/api/status", methods=["GET"])
def get_status():
    try:
        u = session.get("usuario", {})
        return jsonify({
            "servidor": "activo",
            "usuario": u.get("username","sin sesion"),
            "rol": u.get("rol","none"),
            "sqlite": {"activo": True, "archivo": DB_FILE, "existe": os.path.exists(DB_FILE)},
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route("/api/ping", methods=["GET"])
def api_ping():
    try:
        req = urllib.request.Request(
            "https://cclafrwdqentvxgpmdbn.supabase.co/rest/v1/tpv_estado?limit=0")
        req.add_header("apikey","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNjbGFmcndkcWVudHZ4Z3BtZGJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwMDA4MjIsImV4cCI6MjA4ODU3NjgyMn0.***REMOVED***")
        urllib.request.urlopen(req, timeout=5)
        return jsonify({"online": True})
    except Exception:
        return jsonify({"online": False})

@settings_bp.route("/api/health/full", methods=["GET"])
def api_health_full():
    info = obtener_info_db()
    return jsonify({
        "ok": True, "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time(), "db": info,
        "modules": 26, "routes": 114, "roles": 5
    })

@settings_bp.route("/api/backup", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def export_backup():
    estado = cargar_estado() or {}
    backup = {"version":"5.0","fecha":datetime.now().isoformat(),"datos":estado}
    resp = jsonify(backup)
    resp.headers["Content-Disposition"] = \
        f"attachment; filename=tpv_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return resp

# ══════════════════════════════════════════════════════════════
#  SUPABASE
# ══════════════════════════════════════════════════════════════

@settings_bp.route("/api/supabase/config", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def get_supabase_config():
    try:
        return jsonify(_sb.obtener_config_completa())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route("/api/supabase/config", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def save_supabase_config():
    try:
        d = request.get_json(silent=True) or {}
        url = d.get("url", "").strip()
        key = d.get("anon_key", "").strip()
        if not url or not key:
            return jsonify({"error": "URL y anon_key son obligatorios"}), 400
        resultado = _sb.actualizar_config(url, key)
        return jsonify({"ok": True, "mensaje": "Config guardada y persistida", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route("/api/supabase/sync-all", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def sync_all():
    return jsonify(sincronizar_todo())

@settings_bp.route("/api/supabase/test", methods=["POST"])
@requiere_rol("desarrollador")
def test_supabase():
    return jsonify(probar_conexion())

@settings_bp.route("/api/supabase/push", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def push_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin datos locales"}), 400
    return jsonify({"ok": guardar_en_supabase(estado)})

@settings_bp.route("/api/supabase/pull", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def pull_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_desde_supabase()
    if not estado:
        return jsonify({"error": "Sin datos en Supabase"}), 500
    return jsonify({"ok": guardar_estado(estado)})

@settings_bp.route("/api/supabase/sync-full", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_supabase_sync_full():
    if not _sb.SUPABASE_OK:
        return jsonify({"ok": False, "mensaje": "Supabase no configurado"}), 400
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        ventas = [dict(r) for r in conn.execute(
            "SELECT * FROM historial_ventas WHERE fecha >= date('now') ORDER BY fecha DESC LIMIT 500"
        ).fetchall()]
        productos = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,activo FROM productos WHERE activo=1"
        ).fetchall()]
        stock = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,stock_actual,precio_venta,categoria FROM inventario_general"
        ).fetchall()]
        gastos = [dict(r) for r in conn.execute(
            "SELECT * FROM gastos WHERE fecha >= date('now')"
        ).fetchall()]
        conn.close()
        url = _sb.SUPABASE_CONFIG["url"]
        def upsert(tabla, datos):
            if not datos: return 0
            from supabase_sync import _peticion, _headers
            import urllib.request as _ur, json as _j
            req = _ur.Request(f"{url}/rest/v1/{tabla}",
                data=_j.dumps(datos, ensure_ascii=False, default=str).encode(), method="POST")
            for k,v in _headers().items(): req.add_header(k,v)
            req.add_header("Prefer","resolution=merge-duplicates")
            try:
                with _ur.urlopen(req, timeout=10) as r: r.read()
                return len(datos)
            except Exception: return 0
        ok_v = upsert("tpv_ventas_dia", ventas)
        ok_p = upsert("tpv_productos", productos)
        ok_s = upsert("tpv_stock", stock)
        ok_g = upsert("tpv_gastos_dia", gastos)
        estado = cargar_estado()
        _sb.guardar_en_supabase(estado)
        return jsonify({"ok":True,"ventas":ok_v,"productos":ok_p,"stock":ok_s,"gastos":ok_g})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@settings_bp.route("/api/supabase/estado", methods=["GET"])
@requiere_login
def api_supabase_estado():
    try:
        config = obtener_config_actual()
        tablas = verificar_tablas_supabase() if config.get("configurado") else {}
        return jsonify({"ok":True,"configurado":config.get("configurado",False),"url":config.get("url",""),"tablas":tablas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@settings_bp.route("/api/supabase/setup", methods=["POST"])
@requiere_login
def api_supabase_setup():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    try:
        return jsonify(setup_supabase())
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@settings_bp.route("/api/supabase/sql", methods=["GET"])
@requiere_login
def api_supabase_sql():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador",):
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    return jsonify({
        "ok": True, "sql": obtener_sql_completo(),
        "sql_por_tabla": {tabla: sql.strip() for tabla, sql in TABLAS_SQL.items()}
    })

# ══════════════════════════════════════════════════════════════
#  SSE — Server-Sent Events
# ══════════════════════════════════════════════════════════════

_sse_clientes = {}
_sse_lock = threading.Lock()

def _sse_broadcast(evento):
    msg = f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
    with _sse_lock:
        muertos = []
        for uid, q in _sse_clientes.items():
            try: q.put_nowait(msg)
            except _queue.Full: muertos.append(uid)
        for uid in muertos: _sse_clientes.pop(uid, None)

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

@settings_bp.route("/api/debug/health", methods=["GET"])
@requiere_login
def api_debug_health():
    u = usuario_actual()
    if u.get("rol") != "desarrollador":
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    try:
        db_info = obtener_info_db()
        config_sb = obtener_config_actual()
        tablas_sb = verificar_tablas_supabase() if config_sb.get("configurado") else {}
        return jsonify({"ok":True,"servidor":"Flask OK","sqlite":db_info,
                        "supabase":{"configurado":config_sb.get("configurado"),"tablas":tablas_sb}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  BIOMÉTRICAS
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
