"""
╔══════════════════════════════════════════════════════════════╗
║   app.py  —  TPV ULTRA SMART  v7.0 (MODULAR + SEGURIDAD)   ║
║   Punto de entrada central para APK y servidor local       ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os, pathlib, secrets, json, threading, time, re
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string

# Fix path
try:
    from tpv_rutas import fix_path, CARPETA as _CARPETA_DETECTADA
    fix_path()
except ImportError:
    def _fix_path_fallback():
        candidatas = ['/storage/emulated/0/TPV_APK', '/sdcard/TPV_APK', os.getcwd()]
        try: candidatas.insert(0, os.path.dirname(os.path.abspath(__file__)))
        except NameError: pass
        for r in candidatas:
            if os.path.exists(os.path.join(r, 'database.py')):
                if r not in sys.path: sys.path.insert(0, r)
                os.chdir(r); return r
        return os.getcwd()
    _CARPETA_DETECTADA = _fix_path_fallback()

# Carpetas
_CARPETA_MAIN = os.path.dirname(_CARPETA_DETECTADA)
_TEMPLATE_FOLDER = os.path.join(_CARPETA_MAIN, 'assets', 'frontend', 'templates')
_STATIC_FOLDER = os.path.join(_CARPETA_MAIN, 'assets', 'frontend', 'static')

# Imports
from database import crear_tablas, cargar_estado, guardar_estado, login_usuario, obtener_info_db, DB_FILE
from tienda_routes import tienda_bp, crear_tablas_tienda
import supabase_sync as _sb
from routes.auth import auth_bp
from routes.inventory import inventory_bp
from routes.products import products_bp
from routes.sales import sales_bp
from routes.system import system_bp
from routes.agent import agent_bp
from routes.metrics import metrics_bp

# Setup Flask
app = Flask(__name__, template_folder=_TEMPLATE_FOLDER, static_folder=_STATIC_FOLDER, static_url_path='/static')
app.config["JSON_ENSURE_ASCII"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_DOMAIN"] = None
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7

# Clave secreta
_KEY_FILE = pathlib.Path(os.environ.get("ANDROID_PRIVATE", os.getcwd())) / ".tpv_secret_key"
if not _KEY_FILE.exists(): _KEY_FILE.write_text(secrets.token_hex(32))
app.secret_key = _KEY_FILE.read_text().strip()

# Registrar blueprints
app.register_blueprint(tienda_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(products_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(system_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(metrics_bp)

# Rate limiting simple
_login_attempts = {}
def rate_limit(max_attempts=5, window_seconds=600):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            username = request.get_json(force=True, silent=True or {}).get('username', '').lower()
            now = time.time()
            _login_attempts[username] = [t for t in _login_attempts.get(username, []) if now - t < window_seconds]
            if len(_login_attempts.get(username, [])) >= max_attempts:
                return jsonify({"error": "Demasiados intentos. Intente más tarde."}), 429
            _login_attempts.setdefault(username, []).append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ══════════════════════════════════════════════════════════════
# RUTAS PRINCIPALES
# ══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    try:
        with open(os.path.join(_TEMPLATE_FOLDER, 'index.html'), 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f'<h3>Error cargando index.html: {e}</h3>', 500

@app.route("/<path:filename>")
def serve_static(filename):
    allowed = {'.js', '.css', '.ico', '.png', '.svg', '.woff', '.woff2', '.json'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed: return '', 404
    mime_map = {'.js': 'application/javascript', '.css': 'text/css', '.ico': 'image/x-icon', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json'}
    nombre_base = os.path.basename(filename)
    candidatos = [
        os.path.join(_STATIC_FOLDER, 'js', 'tpv', nombre_base),
        os.path.join(_STATIC_FOLDER, nombre_base),
        os.path.join(_CARPETA_DETECTADA, nombre_base),
        os.path.join(os.getcwd(), nombre_base),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'rb') as f:
                return f.read(), 200, {'Content-Type': mime_map.get(ext, 'application/octet-stream'), 'Cache-Control': 'public, max-age=3600'}
    return '', 404

# ══════════════════════════════════════════════════════════════
# AUTH + RATE LIMITING
# ══════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
@rate_limit(max_attempts=5, window_seconds=600)
def api_login():
    datos = request.get_json(force=True, silent=True) or {}
    username = datos.get("username", "").strip()
    password = datos.get("password", "")
    if not username or not password: return jsonify({"error": "Faltan credenciales"}), 400
    resultado = login_usuario(username, password)
    if resultado:
        session.permanent = True
        session["usuario"] = resultado
        return jsonify({"ok": True, "usuario": resultado})
    return jsonify({"error": "Credenciales incorrectas"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u: return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

# ══════════════════════════════════════════════════════════════
# STATUS PÚBLICO
# ══════════════════════════════════════════════════════════════
@app.route("/api/status", methods=["GET"])
def get_status():
    try:
        u = session.get("usuario", {})
        return jsonify({
            "servidor": "activo",
            "usuario": u.get("username", "sin sesión"),
            "rol": u.get("rol", "none"),
            "sqlite": {"activo": True, "existe": os.path.exists(DB_FILE)},
            "supabase": {"activo": _sb.SUPABASE_OK},
            "db_info": obtener_info_db(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def error_404(e): return jsonify({"error": "Ruta no encontrada", "code": 404}), 404
@app.errorhandler(500)
def error_500(e): return jsonify({"error": "Error interno", "detalle": str(e)}), 500

def main():
    print("\n" + "="*58 + "\n   TPV ULTRA SMART v7.0 (MODULAR + IA + MÉTRICAS)\n" + "="*58)
    crear_tablas()
    crear_tablas_tienda()
    print(f" ✅ Base de datos: {DB_FILE}")
    print(f" ✅ Supabase: {'Activo' if _sb.SUPABASE_OK else 'Solo local'}")
    print(f" ✅ Login: desarrollador / dev2024")
    print(f" ✅ URL: http://localhost:5000\n")
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
