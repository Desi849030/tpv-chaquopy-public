from routes.settings_bp import settings_bp
from routes.settings_helpers import *

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
@settings_bp.route("/api/ping", methods=["GET"])
def api_ping():
    """Health check usando config dinamica de Supabase."""
    try:
        from sync.supabase_sync import SUPABASE_CONFIG, SUPABASE_OK
        if not SUPABASE_OK:
            return jsonify({"online": False, "error": "Supabase no configurado"})
        import urllib.request
        url = SUPABASE_CONFIG.get("url", "") + "/rest/v1/tpv_estado?limit=0"
        req = urllib.request.Request(url)
        req.add_header("apikey", SUPABASE_CONFIG.get("anon_key", ""))
        req.add_header("Authorization", "Bearer " + SUPABASE_CONFIG.get("anon_key", ""))
        with urllib.request.urlopen(req, timeout=5) as resp:
            return jsonify({"online": resp.status == 200})
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

