"""Rutas de autenticación — /api/auth/*"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    login_usuario, cambiar_password, cargar_estado,
    guardar_estado, agregar_log
)
import supabase_sync as _sb

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    datos = request.get_json(force=True, silent=True) or {}
    username = datos.get("username", "").strip()
    password = datos.get("password", "")
    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400
    resultado = login_usuario(username, password)
    if resultado:
        session.permanent = True
        session["usuario"] = resultado
        return jsonify({"ok": True, "usuario": resultado})
    return jsonify({"error": "Credenciales incorrectas"}), 401

@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@auth_bp.route("/api/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u:
        return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

@auth_bp.route("/api/auth/cambiar-password", methods=["POST"])
@requiere_login
def api_cambiar_password():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = cambiar_password(
        u["usuario_id"],
        datos.get("password_actual", ""),
        datos.get("password_nueva", "")
    )
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/api/auth/auto-backup", methods=["POST"])
@requiere_login
def api_auto_backup():
    """Guarda backup automático al cerrar sesión + sync Supabase si disponible."""
    try:
        estado = cargar_estado()
        from database import obtener_conexion as _oc
        import json as _json
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        key = f"autobackup_{ts}"
        conn = _oc()
        conn.execute(
            "INSERT OR REPLACE INTO app_state(clave, valor) VALUES(?,?)",
            (key, _json.dumps(estado, ensure_ascii=False))
        )
        conn.execute("""
            DELETE FROM app_state WHERE clave LIKE 'autobackup_%'
            AND clave NOT IN (
                SELECT clave FROM app_state WHERE clave LIKE 'autobackup_%'
                ORDER BY clave DESC LIMIT 7
            )
        """)
        conn.commit()
        conn.close()
        sb_ok = False
        if _sb.SUPABASE_OK and estado:
            sb_ok = _sb.guardar_en_supabase(estado)
        return jsonify({"ok": True, "clave": key, "supabase": sb_ok})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
