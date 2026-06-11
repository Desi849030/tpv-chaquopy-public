import json, threading, queue as _queue
from decorators import login_required, requiere_rol, usuario_actual
from modules.settings_helpers import settings_bp
import sync.config_supabase as _csb_mod
from sync.config_persist import TABLAS_SQL, SQL_COMPLETO
import sync.supabase_sync as _sb
from modules.settings_helpers import (request, jsonify, session,
    cargar_estado, guardar_estado,
    sincronizar_todo, probar_conexion, guardar_en_supabase,
    cargar_desde_supabase, verificar_tablas_supabase, setup_supabase)


@settings_bp.route("/api/supabase/config", methods=["GET"])
@login_required
def get_supabase_config():
    try:
        url = _csb_mod.SUPABASE_CONFIG.get("url", "")
        key = _csb_mod.SUPABASE_CONFIG.get("anon_key", "")
        k = key[:8] + "..." + key[-4:] if len(key) > 12 else "no configurada"
        return jsonify({"url": url, "anon_key": key, "anon_key_preview": k,
                        "configurado": _csb_mod.SUPABASE_OK})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/supabase/config", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def save_supabase_config():
    try:
        d = request.get_json(silent=True) or {}
        url = d.get("url", "").strip()
        key = d.get("anon_key", "").strip()
        if not url or not key:
            return jsonify({"error": "URL y anon_key son obligatorios"}), 400
        _csb_mod.SUPABASE_CONFIG["url"] = url.rstrip("/")
        _csb_mod.SUPABASE_CONFIG["anon_key"] = key
        import os
        cfg_path = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), "supabase_config.json")
        with open(cfg_path, "w") as f:
            json.dump({"url": url.rstrip("/"), "anon_key": key}, f)
        _csb_mod.verificar_supabase()
        return jsonify({"ok": True, "mensaje": "Config guardada", "configurado": _csb_mod.SUPABASE_OK})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/supabase/sync", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def sync_alias():
    return sync_all()


@settings_bp.route("/api/supabase/sync-all", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def sync_all():
    return jsonify(sincronizar_todo())


@settings_bp.route("/api/supabase/test", methods=["POST"])
@requiere_rol("desarrollador")
def test_supabase():
    return jsonify(probar_conexion())


@settings_bp.route("/api/supabase/push", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def push_supabase():
    if not _csb_mod.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin datos locales"}), 400
    return jsonify({"ok": guardar_en_supabase(estado)})


@settings_bp.route("/api/supabase/pull", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def pull_supabase():
    if not _csb_mod.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_desde_supabase()
    if not estado:
        return jsonify({"error": "Sin datos en Supabase"}), 500
    return jsonify({"ok": guardar_estado(estado)})


@settings_bp.route("/api/supabase/sync-full", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_supabase_sync_full():
    if not _csb_mod.SUPABASE_OK:
        return jsonify({"ok": False, "mensaje": "Supabase no configurado"}), 400
    try:
        from database import obtener_conexion
        from sync.config_supabase import _peticion, _headers
        conn = obtener_conexion()
        ventas = [dict(r) for r in conn.execute(
            "SELECT * FROM historial_ventas ORDER BY fecha DESC LIMIT 500").fetchall()]
        productos = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,activo FROM productos WHERE activo=1").fetchall()]
        stock = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,stock_actual,precio_venta,categoria FROM inventario_general").fetchall()]
        gastos = [dict(r) for r in conn.execute("SELECT * FROM gastos").fetchall()]
        url = _csb_mod.SUPABASE_CONFIG["url"]
        def upsert(tabla, datos):
            if not datos:
                return 0
            import urllib.request as _ur
            req = _ur.Request(url + "/rest/v1/" + tabla,
                data=json.dumps(datos, ensure_ascii=False, default=str).encode(), method="POST")
            for k, v in _headers().items():
                req.add_header(k, v)
            req.add_header("Prefer", "resolution=merge-duplicates")
            try:
                with _ur.urlopen(req, timeout=15) as r:
                    r.read()
                return len(datos)
            except Exception:
                return 0
        ok_v = upsert("tpv_ventas_dia", ventas)
        ok_p = upsert("tpv_productos", productos)
        ok_s = upsert("tpv_stock", stock)
        ok_g = upsert("tpv_gastos_dia", gastos)
        # Sync usuarios
        usuarios = [dict(r) for r in conn.execute(
            "SELECT usuario_id,username,nombre,rol,password_hash,password_salt,activo FROM usuarios").fetchall()]
        conn.close()
        ok_u = upsert("tpv_usuarios", usuarios)
        return jsonify({"ok": True, "ventas": ok_v, "productos": ok_p, "stock": ok_s, "gastos": ok_g, "usuarios": ok_u})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@settings_bp.route("/api/supabase/estado", methods=["GET"])
@login_required
def api_supabase_estado():
    try:
        url = _csb_mod.SUPABASE_CONFIG.get("url", "")
        key = _csb_mod.SUPABASE_CONFIG.get("anon_key", "")
        ok = bool(url.startswith("https://") and len(key) > 20)
        tablas = {}
        if ok:
            import time as _t
            _now = _t.time()
            _prev = getattr(api_supabase_estado, '_cache_t', 0)
            if _now - _prev > 120:
                try:
                    tablas = verificar_tablas_supabase()
                    api_supabase_estado._cache = tablas
                    api_supabase_estado._cache_t = _now
                except Exception:
                    tablas = getattr(api_supabase_estado, '_cache', {})
            else:
                tablas = getattr(api_supabase_estado, '_cache', {})
        return jsonify({"ok": True, "configurado": ok, "url": url, "tablas": tablas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@settings_bp.route("/api/supabase/setup", methods=["POST"])
@login_required
def api_supabase_setup():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    try:
        return jsonify(setup_supabase())
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500


@settings_bp.route("/api/supabase/sql", methods=["GET"])
@login_required
def api_supabase_sql():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador",):
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    return jsonify({
        "ok": True, "sql": SQL_COMPLETO,
        "sql_por_tabla": {tabla: sql.strip() for tabla, sql in TABLAS_SQL.items()}
    })


_sse_clientes = {}
_sse_lock = threading.Lock()

def _sse_broadcast(evento):
    msg = "data: " + json.dumps(evento, ensure_ascii=False) + "\n\n"
    with _sse_lock:
        muertos = []
        for uid, q in _sse_clientes.items():
            try:
                q.put_nowait(msg)
            except _queue.Full:
                muertos.append(uid)
        for uid in muertos:
            _sse_clientes.pop(uid, None)
