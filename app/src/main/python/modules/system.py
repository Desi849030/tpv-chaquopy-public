from auth_decorator import login_required
"""
╔══════════════════════════════════════════════════════════════╗
║   system.py  —  TPV ULTRA SMART  v7.0 (COMPLETO)           ║
║   Status, backups, logs y configuración del sistema         ║
╚══════════════════════════════════════════════════════════════╝
"""
from flask import Blueprint, request, jsonify, session, Response
from functools import wraps
from datetime import datetime
import json, os
from database import (
    obtener_info_db, DB_FILE, cargar_estado, guardar_estado,
    obtener_historial_diario_local, guardar_historial_diario_local,
    agregar_log
)
import supabase_sync as _sb

system_bp = Blueprint('system', __name__, url_prefix='/api')




# ══════════════════════════════════════════════════════════════
# STATUS DEL SISTEMA
# ══════════════════════════════════════════════════════════════
@system_bp.route("/status", methods=["GET"])
def api_status():
    """Endpoint público de status del servidor."""
    try:
        u = session.get("usuario", {})
        return jsonify({
            "servidor": "activo",
            "usuario": u.get("username", "sin sesión"),
            "rol": u.get("rol", "none"),
            "sqlite": {"activo": True, "archivo": DB_FILE, "existe": os.path.exists(DB_FILE)},
            "supabase": {"activo": _sb.SUPABASE_OK},
            "db_info": obtener_info_db(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# BACKUPS
# ══════════════════════════════════════════════════════════════
@system_bp.route("/backup/export", methods=["GET"])
@requiere_rol("administrador", "desarrollador")
def api_export_backup():
    """Exporta backup completo en JSON."""
    estado = cargar_estado() or {}
    backup = {
        "version": "7.0",
        "fecha": datetime.now().isoformat(),
        "datos": estado
    }
    resp = jsonify(backup)
    resp.headers["Content-Disposition"] = f"attachment; filename=tpv_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return resp

@system_bp.route("/backup/import", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_import_backup():
    """Importa backup desde JSON."""
    try:
        datos = request.get_json(force=True)
        if not isinstance(datos, dict) or "datos" not in datos:
            return jsonify({"error": "Formato de backup inválido"}), 400
        guardar_estado(datos["datos"])
        agregar_log(f"Backup importado por {usuario_actual().get('username')}", "info")
        return jsonify({"ok": True, "mensaje": "Backup importado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# HISTORIAL DIARIO
# ══════════════════════════════════════════════════════════════
@system_bp.route("/historial/diario", methods=["GET"])
@login_required
def api_historial_get():
    """Obtiene historial diario local."""
    limite = int(request.args.get("limite", 30))
    try:
        historial = obtener_historial_diario_local(limite=limite)
        return jsonify({"ok": True, "historial": historial, "fuente": "local"})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@system_bp.route("/historial/diario", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_historial_post():
    """Guarda snapshot diario."""
    datos = request.get_json(force=True) or {}
    try:
        ok = guardar_historial_diario_local(datos)
        return jsonify({
            "ok": ok,
            "mensaje": f"Snapshot {datos.get('fecha', '?')} guardado"
        })
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# LOGS DEL SISTEMA
# ══════════════════════════════════════════════════════════════
@system_bp.route("/logs", methods=["GET"])
@requiere_rol("desarrollador", "administrador")
def api_logs():
    """Obtiene logs recientes del sistema."""
    nivel = request.args.get("nivel", "info")  # info, warning, error
    limite = int(request.args.get("limite", 100))
    conn = obtener_conexion()
    try:
        if nivel == "all":
            rows = conn.execute(
                "SELECT * FROM logs_sistema ORDER BY timestamp DESC LIMIT ?", (limite,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM logs_sistema WHERE tipo = ? ORDER BY timestamp DESC LIMIT ?",
                (nivel, limite)
            ).fetchall()
        return jsonify({"logs": [dict(r) for r in rows]})
    finally:
        conn.close()

@system_bp.route("/logs/limpiar", methods=["POST"])
@requiere_rol("desarrollador")
def api_limpiar_logs():
    """Limpia logs antiguos (>30 días)."""
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM logs_sistema WHERE timestamp < datetime('now', '-30 days')")
        eliminados = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "eliminados": eliminados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
@system_bp.route("/config", methods=["GET"])
@login_required
def api_get_config():
    """Obtiene configuración del sistema."""
    estado = cargar_estado() or {}
    config = estado.get("config", {})
    return jsonify({"ok": True, "config": config})

@system_bp.route("/config", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_update_config():
    """Actualiza configuración del sistema."""
    datos = request.get_json(force=True) or {}
    estado = cargar_estado() or {}
    estado["config"] = {**(estado.get("config", {})), **datos}
    guardar_estado(estado)
    return jsonify({"ok": True, "mensaje": "Configuración actualizada"})
