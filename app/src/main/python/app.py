"""TPV ULTRA SMART v5.0 — Arquitectura modular"""
import sys, os

# ── FIX PATH PYDROID3 / ANDROID ──
try:
    from tpv_rutas import fix_path, CARPETA as _CARPETA_DETECTADA
    fix_path()
except ImportError:
    def _fix_path_fallback():
        candidatas = ['/storage/emulated/0/TPV_APK','/storage/emulated/0/TPV',
                      '/sdcard/TPV_APK','/sdcard/TPV']
        try: d = os.path.dirname(os.path.abspath(__file__))
        except NameError: pass
        else: candidatas.insert(0, d)
        candidatas.insert(0, os.getcwd())
        for r in candidatas:
            if os.path.exists(os.path.join(r, 'database.py')):
                if r not in sys.path: sys.path.insert(0, r)
                os.chdir(r)
                print(f"Proyecto: {r}")
                return r
        print("No se encontro database.py")
        return os.getcwd()
    _CARPETA_DETECTADA = _fix_path_fallback()

import json, threading, webbrowser, time, pathlib, secrets as _secrets
from datetime import datetime

# ── Clave secreta ──
import pathlib as _pathlib
_KEY_FILE = _pathlib.Path(os.environ.get("TPV_FILES_DIR", os.getcwd())) / ".tpv_secret"
if not _KEY_FILE.exists():
    try:
        _KEY_FILE.write_text(_secrets.token_hex(32))
        try: _KEY_FILE.chmod(0o600)
        except Exception: pass
    except Exception:
        pass
try:
    _SECRET_KEY = _KEY_FILE.read_text().strip()
except Exception:
    _SECRET_KEY = _secrets.token_hex(32)
# ── Flask ──
try:
    from flask import Flask, request, jsonify, session, Response
except ImportError:
    print("Instala Flask: pip install flask"); exit(1)

# ── Database ──
from database import (
    crear_tablas, cargar_estado, guardar_estado,
    agregar_log, obtener_info_db, DB_FILE,
)
from supabase_sync import sincronizar_subida
import supabase_sync as _sb

# ── Blueprint modules ──
from auth_routes import auth_bp
from admin_routes import admin_bp, _MODULOS_DISPONIBLES, _PRIVILEGIOS_DEFAULT
from inventory_routes import inv_bp
from ventas_routes import ventas_bp
from settings_routes import settings_bp
from tienda_routes import tienda_bp, crear_tablas_tienda
from loyalty_routes import loyalty_bp
from api_routes import api_bp
from license_routes import lic_bp
try:
    from validacion_routes import val_bp
except ImportError:
    val_bp = None

try:
    from ia_assistant_routes import assistant_bp
except ImportError:
    assistant_bp = None

try:
    from ai_routes import ai_bp, analytics_bp
except ImportError:
    ai_bp = None
    analytics_bp = None

# ── Carpeta del proyecto ──
_CARPETA = os.environ.get("TPV_FRONTEND_DIR") or _CARPETA_DETECTADA or os.getcwd()

# ── Flask App ──
app = Flask(__name__, static_folder=None)
app.secret_key = _SECRET_KEY
app.config["JSON_ENSURE_ASCII"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_DOMAIN"] = None
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7

# ══════════════════════════════════════════════════════════════
#  REGISTRAR BLUEPRINTS
# ══════════════════════════════════════════════════════════════
_blueprints = [
    auth_bp, admin_bp, inv_bp, ventas_bp, settings_bp,
    tienda_bp, loyalty_bp, api_bp, lic_bp
]
for bp in _blueprints:
    app.register_blueprint(bp)

if assistant_bp: app.register_blueprint(assistant_bp)
if val_bp: app.register_blueprint(val_bp)
if ai_bp: app.register_blueprint(ai_bp)
if analytics_bp: app.register_blueprint(analytics_bp)

try:
    from tpv_security import registrar_auditoria
    registrar_auditoria(app)
    print("Auditoria de seguridad activa")
except ImportError:
    print("tpv_security no disponible (modulo opcional)")
print("Blueprints registrados: auth + admin + inventory + ventas + settings + tienda + loyalty + api + license + assistant + ai")

# ══════════════════════════════════════════════════════════════
#  SERVIR ARCHIVOS ESTÁTICOS E INDEX
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    candidatos = [
        os.path.join(_CARPETA, 'index.html'),
        os.path.join(os.getcwd(), 'index.html'),
        os.path.join(_CARPETA, 'frontend', 'templates', 'index.html'),
        os.path.join(_CARPETA, 'templates', 'index.html'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'frontend', 'templates', 'index.html'),
    ]
    try:
        candidatos.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'))
    except NameError:
        pass
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return '<h3>No se encontro index.html</h3>', 500

@app.route("/<path:filename>")
def serve_static(filename):
    allowed = {'.js','.css','.ico','.png','.svg','.woff','.woff2','.json','.ttf','.eot'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed: return '', 404
    mime_map = {
        '.js':'application/javascript','.css':'text/css','.ico':'image/x-icon',
        '.png':'image/png','.svg':'image/svg+xml','.json':'application/json',
        '.woff':'font/woff','.woff2':'font/woff2','.ttf':'font/ttf',
        '.eot':'application/vnd.ms-fontobject',
    }
    nombre_base = os.path.basename(filename)
    _assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'frontend')
    candidatos = [
        os.path.join(_CARPETA, filename),
        os.path.join(_assets_dir, filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(_CARPETA, 'frontend', 'static', 'lib', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'lib', 'fonts', nombre_base),
        os.path.join(_assets_dir, 'static', 'lib', nombre_base),
        os.path.join(_assets_dir, 'static', 'js', nombre_base),
        os.path.join(_assets_dir, 'static', 'css', nombre_base),
        os.path.join(_assets_dir, 'static', 'icons', nombre_base),
        os.path.join(_assets_dir, 'static', 'lib', 'fonts', nombre_base),
        os.path.join(os.getcwd(), 'frontend', 'static', 'lib', nombre_base),
        os.path.join(os.getcwd(), 'frontend', 'static', 'lib', 'fonts', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'js', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'css', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'icons', nombre_base),
        os.path.join(_CARPETA, 'static', 'js', nombre_base),
        os.path.join(_CARPETA, 'static', nombre_base),
        os.path.join(_CARPETA, 'static', 'lib', nombre_base),
        os.path.join(_CARPETA, 'static', 'lib', 'fonts', nombre_base),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'rb') as f:
                return f.read(), 200, {
                    'Content-Type': mime_map.get(ext, 'application/octet-stream'),
                    'Cache-Control': 'public, max-age=3600'
                }
    return '', 404

# ══════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════

@app.errorhandler(404)
def error_404(e):
    return jsonify({"error": "Ruta no encontrada", "code": 404}), 404

@app.errorhandler(500)
def error_500(e):
    return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════════════

def abrir_navegador():
    time.sleep(1.5)
    try: webbrowser.open("http://localhost:5000")
    except Exception: pass

def main():
    print("\n" + "="*58)
    print("   TPV ULTRA SMART v5.0 — MODULAR")
    print("="*58)
    crear_tablas()
    crear_tablas_tienda()
    estado = cargar_estado()
    if estado:
        print(f" {len(estado.get('productos',[]))} productos | {len(estado.get('historialVentas',[]))} ventas")
    print(f" Supabase: {'Activo' if _sb.SUPABASE_OK else 'Solo local'}")
    print(" Servidor: http://localhost:5000")
    print(" Login:    desarrollador / dev2024\n")
    threading.Thread(target=abrir_navegador, daemon=True).start()
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    try:
        import socket
        ips = list(set([
            i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)
            if i[4][0].startswith(('192.168.','10.','172.')) and ':' not in i[4][0]
        ]))
        print("\n" + "="*48)
        print("  TPV ULTRA SMART v6.0 - Modular")
        print("  Local : http://localhost:5000")
        for ip in ips: print(f"  WiFi  : http://{ip}:5000")
        print("="*48 + "\n")
    except Exception: pass
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
