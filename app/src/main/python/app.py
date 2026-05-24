"""
╔══════════════════════════════════════════════════════════════╗
║   app.py  —  TPV ULTRA SMART  v6.0 (MODULAR)               ║
║   Punto de entrada para Blueprints - RUTAS CORREGIDAS      ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os, pathlib, secrets as _secrets, json, threading, time
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, Response, stream_with_context

# Fix path para Android
try:
    from tpv_rutas import fix_path, CARPETA as _CARPETA_DETECTADA
    fix_path()
except ImportError:
    def _fix_path_fallback():
        candidatas = [
            '/storage/emulated/0/TPV_APK',
            '/storage/emulated/0/TPV',
            '/sdcard/TPV_APK',
            os.getcwd(),
        ]
        try:
            d = os.path.dirname(os.path.abspath(__file__))
            candidatas.insert(0, d)
        except NameError:
            pass
        for r in candidatas:
            if os.path.exists(os.path.join(r, 'database.py')):
                if r not in sys.path: sys.path.insert(0, r)
                os.chdir(r)
                print(f"✅ Proyecto: {r}")
                return r
        print("❌ No se encontró database.py")
        return os.getcwd()
    _CARPETA_DETECTADA = _fix_path_fallback()

# Detectar carpeta MAIN (nivel superior a python/)
_CARPETA_MAIN = os.path.dirname(_CARPETA_DETECTADA)

# Imports locales
from database import (crear_tablas, cargar_estado, guardar_estado, login_usuario,
                      obtener_info_db, DB_FILE, obtener_conexion, agregar_log)
from tienda_routes import tienda_bp, crear_tablas_tienda
import supabase_sync as _sb

# Importar Blueprints Modulares
from routes.auth import auth_bp
from routes.inventory import inv_bp
from routes.products import prod_bp
from routes.sales import sales_bp
from routes.system import sys_bp

# Setup Flask
ap = os.environ.get("ANDROID_PRIVATE", "")
_KEY_FILE = pathlib.Path(ap) / ".tpv_secret_key" if ap and os.path.isdir(ap) else pathlib.Path(os.getcwd()) / ".tpv_secret_key"
if not _KEY_FILE.exists(): _KEY_FILE.write_text(_secrets.token_hex(32))
try: _KEY_FILE.chmod(0o600)
except Exception: pass

app = Flask(__name__, static_folder=None)
app.config["JSON_ENSURE_ASCII"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_DOMAIN"] = None
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7
app.secret_key = _KEY_FILE.read_text().strip()

# Registrar Blueprints
app.register_blueprint(tienda_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(inv_bp)
app.register_blueprint(prod_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(sys_bp)

# ══════════════════════════════════════════════════════════════
# RUTA PRINCIPAL — Busca index.html en múltiples ubicaciones
# ══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Busca index.html en rutas corregidas para estructura assets/"""
    candidatos = [
        # Ruta CORREGIDA: assets está al mismo nivel que python/
        os.path.join(_CARPETA_MAIN, 'assets', 'frontend', 'templates', 'index.html'),
        os.path.join(_CARPETA_DETECTADA, '..', 'assets', 'frontend', 'templates', 'index.html'),
        # Fallbacks
        os.path.join(_CARPETA_DETECTADA, 'assets', 'frontend', 'templates', 'index.html'),
        os.path.join(os.getcwd(), 'assets', 'frontend', 'templates', 'index.html'),
        os.path.join(os.getcwd(), 'index.html'),
        os.path.join(_CARPETA_DETECTADA, 'index.html'),
    ]
    for ruta in candidatos:
        ruta_norm = os.path.normpath(ruta)
        if os.path.exists(ruta_norm):
            try:
                with open(ruta_norm, 'r', encoding='utf-8') as f:
                    return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
            except Exception as e:
                print(f"⚠️ Error leyendo {ruta_norm}: {e}")
    return '<h3>No se encontro index.html</h3><p>Ruta buscada: assets/frontend/templates/</p>', 500

# ══════════════════════════════════════════════════════════════
# SERVICIO DE ARCHIVOS ESTÁTICOS — rutas corregidas
# ══════════════════════════════════════════════════════════════
@app.route("/<path:filename>")
def serve_static(filename):
    """Sirve .js, .css, etc desde assets/frontend/static/"""
    allowed = {'.js', '.css', '.ico', '.png', '.svg', '.woff', '.woff2', '.json'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed:
        return '', 404
    mime_map = {
        '.js': 'application/javascript', '.css': 'text/css', '.ico': 'image/x-icon',
        '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json',
    }
    nombre_base = os.path.basename(filename)
    
    # Rutas corregidas para assets/
    candidatos = [
        # assets/frontend/static/js/tpv/
        os.path.join(_CARPETA_MAIN, 'assets', 'frontend', 'static', 'js', 'tpv', nombre_base),
        os.path.join(_CARPETA_DETECTADA, '..', 'assets', 'frontend', 'static', 'js', 'tpv', nombre_base),
        # assets/frontend/static/
        os.path.join(_CARPETA_MAIN, 'assets', 'frontend', 'static', nombre_base),
        os.path.join(_CARPETA_DETECTADA, '..', 'assets', 'frontend', 'static', nombre_base),
        # Fallbacks
        os.path.join(_CARPETA_DETECTADA, nombre_base),
        os.path.join(os.getcwd(), nombre_base),
    ]
    for ruta in candidatos:
        ruta_norm = os.path.normpath(ruta)
        if os.path.exists(ruta_norm):
            try:
                with open(ruta_norm, 'rb') as f:
                    return f.read(), 200, {'Content-Type': mime_map.get(ext, 'application/octet-stream')}
            except Exception:
                pass
    return '', 404

# ══════════════════════════════════════════════════════════════
# AUTH (rutas existentes, sin cambios)
# ══════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
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

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u:
        return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

# ══════════════════════════════════════════════════════════════
# STATUS
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

# ══════════════════════════════════════════════════════════════
# ERRORES
# ══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def error_404(e):
    return jsonify({"error": "Ruta no encontrada", "code": 404}), 404
@app.errorhandler(500)
def error_500(e):
    return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# ARRANQUE
# ══════════════════════════════════════════════════════════════
def main():
    print("\n" + "="*58 + "\n   TPV ULTRA SMART v6.0 (MODULAR)\n" + "="*58)
    crear_tablas()
    crear_tablas_tienda()
    estado = cargar_estado()
    if estado:
        print(f" {len(estado.get('productos',[]))} productos | {len(estado.get('historialVentas',[]))} ventas ")
    print(f" Supabase: {'✅ Activo' if _sb.SUPABASE_OK else '⚠️  Solo local'} ")
    print(" Servidor: http://localhost:5000 ")
    print(" Login:    desarrollador / dev2024\n ")
    
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
