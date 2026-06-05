from auth_decorator import login_required
from modules.settings_bp import settings_bp
from modules.settings_helpers import *

@login_required
@settings_bp.route("/api/supabase/config", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def get_supabase_config():
    try:
        return jsonify(_sb.obtener_config_completa())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@login_required
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

@login_required
@settings_bp.route("/api/supabase/sync-all", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def sync_all():
    return jsonify(sincronizar_todo())

@login_required
@settings_bp.route("/api/supabase/test", methods=["POST"])
@requiere_rol("desarrollador")
def test_supabase():
    return jsonify(probar_conexion())

@login_required
@settings_bp.route("/api/supabase/push", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def push_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin datos locales"}), 400
    return jsonify({"ok": guardar_en_supabase(estado)})

@login_required
@settings_bp.route("/api/supabase/pull", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def pull_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_desde_supabase()
    if not estado:
        return jsonify({"error": "Sin datos en Supabase"}), 500
    return jsonify({"ok": guardar_estado(estado)})

@login_required
@settings_bp.route("/api/supabase/sync-full", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_supabase_sync_full():
    if not _sb.SUPABASE_OK:
        return jsonify({"ok": False, "mensaje": "Supabase no configurado"}), 400
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        ventas = [dict(r) for r in conn.execute(
            "SELECT * FROM historial_ventas WHERE 1=1 ORDER BY fecha DESC LIMIT 500"
        ).fetchall()]
        productos = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,activo FROM productos WHERE activo=1"
        ).fetchall()]
        stock = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,stock_actual,precio_venta,categoria FROM inventario_general"
        ).fetchall()]
        gastos = [dict(r) for r in conn.execute(
            "SELECT * FROM gastos WHERE 1=1"
        ).fetchall()]
        conn.close()
        url = _sb.SUPABASE_CONFIG["url"]
        def upsert(tabla, datos):
            if not datos: return 0
            from sync.supabase_sync import _peticion, _headers
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

@login_required
@settings_bp.route("/api/supabase/estado", methods=["GET"])
@requiere_login
def api_supabase_estado():
    try:
        config = obtener_config_actual()
        tablas = verificar_tablas_supabase() if config.get("configurado") else {}
        return jsonify({"ok":True,"configurado":config.get("configurado",False),"url":config.get("url",""),"tablas":tablas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@login_required
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

@login_required
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

