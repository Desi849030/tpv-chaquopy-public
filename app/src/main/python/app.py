"""
╔══════════════════════════════════════════════════════════════╗
║   app.py  —  TPV ULTRA SMART  v6.0 (MODULAR)               ║
║   Punto de entrada para Blueprints                         ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os
try:
    from tpv_rutas import fix_path, CARPETA as _CARPETA_DETECTADA
    fix_path()
except ImportError:
    def _fix_path_fallback():
        candidatas = ['/storage/emulated/0/TPV_APK', '/storage/emulated/0/TPV', '/sdcard/TPV_APK', '/sdcard/TPV']
        try: candidatas.insert(0, os.path.dirname(os.path.abspath(__file__)))
        except NameError: pass
        candidatas.insert(0, os.getcwd())
        for r in candidatas:
            if os.path.exists(os.path.join(r, 'database.py')):
                if r not in sys.path: sys.path.insert(0, r)
                os.chdir(r); print(f"✅ Proyecto: {r}"); return r
        print("❌ No se encontró database.py"); return os.getcwd()
    _CARPETA_DETECTADA = _fix_path_fallback()

import json, threading, webbrowser, time, pathlib, secrets as _secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session

# Importar componentes
from database import crear_tablas, cargar_estado, guardar_estado, obtener_info_db, DB_FILE
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

# Ruta index.html - buscar en assets/frontend/templates/
@app.route("/")
def index():
    candidatos = [
        os.path.join(_CARPETA_DETECTADA, 'assets', 'frontend', 'templates', 'index.html'),
        os.path.join(os.getcwd(), 'assets', 'frontend', 'templates', 'index.html'),
        os.path.join(os.getcwd(), 'index.html'),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f: return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return '<h3>No se encontro index.html</h3>', 500

# Servir estaticos desde assets/frontend/static/
@app.route("/<path:filename>")
def serve_static(filename):
    allowed = {'.js', '.css', '.ico', '.png', '.svg', '.woff', '.woff2', '.json'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed: return '', 404
    mime_map = {'.js': 'application/javascript', '.css': 'text/css', '.ico': 'image/x-icon', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json'}
    nombre_base = os.path.basename(filename)
    candidatos = [
        os.path.join(_CARPETA_DETECTADA, 'assets', 'frontend', 'static', 'js', 'tpv', nombre_base),
        os.path.join(_CARPETA_DETECTADA, 'assets', 'frontend', 'static', nombre_base),
        os.path.join(os.getcwd(), 'assets', 'frontend', 'static', 'js', 'tpv', nombre_base),
        os.path.join(os.getcwd(), 'assets', 'frontend', 'static', nombre_base),
        os.path.join(os.getcwd(), nombre_base),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'rb') as f: return f.read(), 200, {'Content-Type': mime_map.get(ext, 'application/octet-stream')}
    return '', 404

# Errores
@app.errorhandler(404)
def error_404(e): return jsonify({"error": "Ruta no encontrada", "code": 404}), 404
@app.errorhandler(500)
def error_500(e): return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

def main():
    print("\n" + "="*58 + "\n   TPV ULTRA SMART v6.0 (MODULAR)\n" + "="*58)
    crear_tablas()
    crear_tablas_tienda()
    estado = cargar_estado()
    if estado: print(f" {len(estado.get('productos',[]))} productos | {len(estado.get('historialVentas',[]))} ventas ")
    print(f" Supabase: {'✅ Activo' if _sb.SUPABASE_OK else '⚠️  Solo local'} ")
    print(" Servidor: http://localhost:5000 ")
    print(" Login:    desarrollador / dev2024\n ")
    
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
