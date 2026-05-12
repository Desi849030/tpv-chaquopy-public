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


# ── DEBUG ENDPOINT (temporal, eliminar tras login) ──
@auth_bp.route("/api/debug/test-login", methods=["GET"])
def debug_test_login():
    """Test directo: ver estado del usuario y probar login."""
    import sqlite3, os
    from db_connection import verificar_password, _hash_password, obtener_conexion
    db_path = os.environ.get("TPV_FILES_DIR", os.getcwd()) + "/tpv_datos.db"
    info = {"db_path": db_path, "db_exists": os.path.exists(db_path)}
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT usuario_id, username, password_hash, password_salt, activo, rol FROM usuarios WHERE username=?", ("desarrollador",))
        u = cur.fetchone()
        conn.close()
        if u:
            info["user_found"] = True
            info["username"] = u["username"]
            info["rol"] = u["rol"]
            info["activo"] = u["activo"]
            info["hash_len"] = len(u["password_hash"]) if u["password_hash"] else 0
            info["salt_len"] = len(u["password_salt"]) if u["password_salt"] else 0
            info["verify_123456"] = verificar_password("123456", u["password_hash"], u["password_salt"])
            info["verify_Desarr2025"] = verificar_password("Desarrollador2025", u["password_hash"], u["password_salt"])
            # Ahora forzar password y probar login completo
            hp, sp = _hash_password("123456")
            conn2 = sqlite3.connect(db_path)
            conn2.execute("UPDATE usuarios SET password_hash=?, password_salt=? WHERE username=?", (hp, sp, "desarrollador"))
            conn2.commit()
            conn2.close()
            from database import login_usuario
            info["login_result"] = login_usuario("desarrollador", "123456")
        else:
            info["user_found"] = False
    except Exception as e:
        info["error"] = str(e)
        import traceback
        info["traceback"] = traceback.format_exc()
    return jsonify(info)
