from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from functools import wraps
from database import (cargar_estado, guardar_estado, obtener_info_db, obtener_conexion, agregar_log,
                      guardar_historial_diario_local, obtener_historial_diario_local, obtener_historial_detalle_local)
from datetime import datetime
import json, queue, threading
import supabase_sync as _sb

sys_bp = Blueprint('system', __name__, url_prefix='/api')

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            u = session.get("usuario")
            if not u or u.get("rol") not in roles:
                return jsonify({"error": "Permiso denegado"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def usuario_actual():
    return session.get("usuario", {})

_sse_clientes = {}; _sse_lock = threading.Lock()

@sys_bp.route("/state", methods=["GET"])
@requiere_login
def get_state():
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin estado local"}), 404
    return jsonify({"ok": True, "estado": estado})

@sys_bp.route("/state", methods=["POST"])
@requiere_login
def save_state():
    try:
        estado = request.get_json(force=True)
        if not isinstance(estado, dict):
            return jsonify({"error": "JSON inválido"}), 400
        guardar_estado(estado)
        if _sb.SUPABASE_OK:
            threading.Thread(target=_sb.sincronizar_subida, args=(estado,), daemon=True).start()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sys_bp.route("/status", methods=["GET"])
def get_status():
    try:
        u = session.get("usuario", {})
        return jsonify({
            "servidor": "activo",
            "usuario": u.get("username", "sin sesión"),
            "rol": u.get("rol", "none"),
            "sqlite": {"activo": True, "existe": True},
            "supabase": {"activo": _sb.SUPABASE_OK},
            "db_info": obtener_info_db(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sys_bp.route("/backup", methods=["GET"])
@requiere_rol("administrador", "desarrollador")
def export_backup():
    estado = cargar_estado() or {}
    backup = {"version": "5.0", "fecha": datetime.now().isoformat(), "datos": estado}
    resp = jsonify(backup)
    resp.headers["Content-Disposition"] = f"attachment; filename=tpv_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return resp

@sys_bp.route("/supabase/sync-all", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def sync_all():
    return jsonify(_sb.sincronizar_todo())

@sys_bp.route("/supabase/test", methods=["POST"])
@requiere_rol("desarrollador")
def test_supabase():
    return jsonify(_sb.probar_conexion())

@sys_bp.route("/supabase/push", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def push_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin datos locales"}), 400
    return jsonify({"ok": _sb.guardar_en_supabase(estado)})

@sys_bp.route("/supabase/pull", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def pull_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = _sb.cargar_desde_supabase()
    if not estado:
        return jsonify({"error": "Sin datos en Supabase"}), 500
    return jsonify({"ok": guardar_estado(estado)})

@sys_bp.route("/sse")
@requiere_login
def api_sse():
    u = usuario_actual(); uid = u["usuario_id"]; q = queue.Queue(maxsize=50)
    with _sse_lock: _sse_clientes[uid] = q
    def gen():
        yield f"data: {json.dumps({'tipo':'conectado','rol':u['rol']})}\n\n"
        try:
            while True:
                try: yield q.get(timeout=25)
                except queue.Empty: yield ": heartbeat\n\n"
        except GeneratorExit:
            with _sse_lock: _sse_clientes.pop(uid, None)
    return Response(stream_with_context(gen()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

def _sse_broadcast(evento: dict):
    msg = f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
    with _sse_lock:
        muertos = []
        for uid, q in _sse_clientes.items():
            try: q.put_nowait(msg)
            except queue.Full: muertos.append(uid)
        for uid in muertos: _sse_clientes.pop(uid, None)

@sys_bp.route("/auth/auto-backup", methods=["POST"])
@requiere_login
def api_auto_backup():
    try:
        estado = cargar_estado()
        conn = obtener_conexion(); ts = datetime.now().strftime("%Y-%m-%d %H-%M"); key = f"autobackup{ts}"
        conn.execute("INSERT OR REPLACE INTO app_state(clave, valor) VALUES(?,?)", (key, json.dumps(estado, ensure_ascii=False)))
        conn.execute("DELETE FROM app_state WHERE clave LIKE 'autobackup%' AND clave NOT IN (SELECT clave FROM app_state WHERE clave LIKE 'autobackup%' ORDER BY clave DESC LIMIT 7)")
        conn.commit(); conn.close()
        return jsonify({"ok": True, "clave": key, "supabase": _sb.guardar_en_supabase(estado) if _sb.SUPABASE_OK and estado else False})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@sys_bp.route("/supabase/sync-full", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_supabase_sync_full():
    if not _sb.SUPABASE_OK:
        return jsonify({"ok": False, "mensaje": "Supabase no configurado"}), 400
    try:
        conn = obtener_conexion()
        ventas = [dict(r) for r in conn.execute("SELECT * FROM historial_ventas WHERE fecha >= date('now') ORDER BY fecha DESC LIMIT 500").fetchall()]
        productos = [dict(r) for r in conn.execute("SELECT producto_id,nombre,precio,costo,categoria,unidad_medida,activo FROM productos WHERE activo=1").fetchall()]
        stock = [dict(r) for r in conn.execute("SELECT producto_id,nombre,stock_actual,precio_venta,categoria FROM inventario_general").fetchall()]
        gastos = [dict(r) for r in conn.execute("SELECT * FROM gastos WHERE fecha >= date('now')").fetchall()]
        conn.close()
        url = _sb.SUPABASE_CONFIG["url"]; hdrs = _sb.SUPABASE_CONFIG["anon_key"]
        import urllib.request as _ur
        def upsert(tabla, datos, pk="id"):
            if not datos: return 0
            from supabase_sync import _peticion, _headers
            req = _ur.Request(f"{url}/rest/v1/{tabla}", data=json.dumps(datos, ensure_ascii=False, default=str).encode(), method="POST")
            for k,v in _headers().items(): req.add_header(k,v)
            req.add_header("Prefer", "resolution=merge-duplicates")
            try:
                with _ur.urlopen(req, timeout=10) as r: r.read(); return len(datos)
            except Exception: return 0
        return jsonify({"ok": True, "ventas": upsert("tpv_ventas_dia", ventas, "venta_id"), "productos": upsert("tpv_productos", productos, "producto_id"),
                        "stock": upsert("tpv_stock", stock, "producto_id"), "gastos": upsert("tpv_gastos_dia", gastos, "id")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@sys_bp.route("/supabase/estado", methods=["GET"])
@requiere_login
def api_supabase_estado():
    try:
        config = _sb.obtener_config_actual(); tablas = _sb.verificar_tablas_supabase() if config.get("configurado") else {}
        return jsonify({"ok": True, "configurado": config.get("configurado", False), "url": config.get("url", " "), "tablas": tablas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@sys_bp.route("/supabase/setup", methods=["POST"])
@requiere_login
def api_supabase_setup():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    try: return jsonify(_sb.setup_supabase())
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@sys_bp.route("/supabase/sql", methods=["GET"])
@requiere_login
def api_supabase_sql():
    u = usuario_actual()
    if u.get("rol") != "desarrollador":
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    return jsonify({"ok": True, "sql": _sb.obtener_sql_completo(), "sql_por_tabla": {t: s.strip() for t, s in _sb.TABLAS_SQL.items()}})

@sys_bp.route("/historial/diario", methods=["GET"])
@requiere_login
def api_historial_get():
    try:
        res_sb = _sb.obtener_historial_diario(limite=int(request.args.get("limite", 30)))
        if res_sb.get("ok") and res_sb.get("historial"):
            return jsonify({"ok": True, "historial": res_sb["historial"], "fuente": "supabase"})
        return jsonify({"ok": True, "historial": obtener_historial_diario_local(limite=int(request.args.get("limite", 30))), "fuente": "local"})
    except Exception as e:
        return jsonify({"ok": False, "historial": [], "mensaje": str(e)}), 500

@sys_bp.route("/historial/diario", methods=["POST"])
@requiere_login
def api_historial_post():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    datos = request.get_json(force=True) or {}
    try:
        return jsonify({"ok": guardar_historial_diario_local(datos), "supabase": _sb.guardar_historial_diario(datos).get("ok", False), "mensaje": f"Snapshot {datos.get('fecha','?')} guardado"})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@sys_bp.route("/historial/diario/<fecha>", methods=["GET"])
@requiere_login
def api_historial_detalle(fecha):
    try:
        res_sb = _sb.obtener_historial_detalle(fecha)
        if res_sb.get("ok"): return jsonify(res_sb)
        local = obtener_historial_detalle_local(fecha)
        if local: return jsonify({"ok": True, "dia": local, "fuente": "local"})
        return jsonify({"ok": False, "mensaje": f"Sin historial para {fecha}"}), 404
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@sys_bp.route("/debug/health", methods=["GET"])
@requiere_login
def api_debug_health():
    u = usuario_actual()
    if u.get("rol") != "desarrollador":
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    try:
        return jsonify({"ok": True, "servidor": "Flask OK", "sqlite": obtener_info_db(), "supabase": {"configurado": _sb.obtener_config_actual().get("configurado"), "tablas": _sb.verificar_tablas_supabase() if _sb.obtener_config_actual().get("configurado") else {}}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
