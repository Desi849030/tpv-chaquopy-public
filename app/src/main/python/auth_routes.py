import sys, os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from auth_decorator import login_required, admin_required
from security.crypto import rate_limit

LOG_DIR = '/sdcard/tpv_logs'
LOG_FILE = os.path.join(LOG_DIR, 'tpv_debug.log')
os.makedirs(LOG_DIR, exist_ok=True)

def log_debug(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linea + '\n')
    except:
        pass
    print(linea)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/auth/login", methods=["POST"])
@rate_limit(max_attempts=5, window=60)
def api_login():
    log_debug("=== INTENTO DE LOGIN ===")
    datos = request.get_json(force=True, silent=True) or {}
    log_debug(f"Datos JSON recibidos: {datos}")
    
    username = datos.get("username", "").strip()
    password = datos.get("password", "")
    log_debug(f"Username: '{username}' | Password vacio: {not password}")
    
    if not username or not password:
        log_debug("ERROR: Faltan credenciales")
        return jsonify({"error": "Faltan credenciales"}), 400
    
    try:
        from db.users import login_usuario
        resultado = login_usuario(username, password)
        log_debug(f"Resultado login_usuario: {resultado}")
        
        if resultado is None:
            log_debug("ERROR: Credenciales incorrectas (None)")
            return jsonify({"error": "Credenciales incorrectas"}), 401
        
        if isinstance(resultado, dict) and "error" in resultado:
            log_debug(f"ERROR: {resultado}")
            return jsonify(resultado), 429
        
        session.permanent = True
        session["usuario"] = resultado
        log_debug(f"LOGIN EXITOSO: {resultado}")
        return jsonify({"ok": True, "usuario": resultado})
        
    except Exception as e:
        log_debug(f"EXCEPCION: {str(e)}")
        import traceback
        log_debug(traceback.format_exc())
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    log_debug(f"Logout: {session.get('usuario', {}).get('username', 'desconocido')}")
    session.clear()
    return jsonify({"ok": True})

@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
def api_me():
    return jsonify({"usuario": session.get("usuario")})

@auth_bp.route("/api/auth/cambiar-password", methods=["POST"])
@login_required
def api_cambiar_password():
    datos = request.get_json(force=True, silent=True) or {}
    return jsonify({"ok": True})

@auth_bp.route("/api/auth/auto-backup", methods=["POST"])
@login_required
def api_auto_backup():
    return jsonify({"ok": True, "mensaje": "Backup no implementado aún"})
