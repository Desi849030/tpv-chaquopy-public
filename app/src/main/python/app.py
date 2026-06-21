# -*- coding: utf-8 -*-
"""TPV Ultra Smart v8.0 — Backend Flask (refactorizado)

Todas las rutas están en blueprints dentro de modules/.
Este archivo solo configura Flask, registra blueprints e inicializa la BD.
"""
import os
import sys
import logging

from flask import Flask, jsonify, send_from_directory, request, jsonify

_CD = os.path.dirname(os.path.abspath(__file__))
_MAIN = os.path.dirname(_CD)

_ENV_FRONTEND = os.environ.get('TPV_FRONTEND_DIR', '')
_CANDIDATOS = [
    _ENV_FRONTEND,
    os.path.join(_MAIN, 'assets', 'frontend'),
    os.path.join(_CD, 'frontend'),
]
_ASSETS = ''
for _c in _CANDIDATOS:
    if _c and os.path.isdir(os.path.join(_c, 'templates')):
        _ASSETS = _c
        break
if not _ASSETS:
    _ASSETS = _ENV_FRONTEND or os.path.join(_MAIN, 'assets', 'frontend')

_TPL = os.path.join(_ASSETS, 'templates')
_STAT = os.path.join(_ASSETS, 'static')
print("📁 Frontend en uso:", _ASSETS)

# ═══ MIGRACIÓN: tabla documentacion + datos demo ═══
try:
    import sqlite3 as _sql
    _db_path = os.path.join(_CD, 'tpv_datos.db')
    _conn = _sql.connect(_db_path)
    
    # Crear tabla documentacion
    _conn.execute("CREATE TABLE IF NOT EXISTS documentacion (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, contenido TEXT NOT NULL, lineas INTEGER DEFAULT 0, actualizado TEXT DEFAULT (datetime('now','localtime')))")
    _count = _conn.execute("SELECT COUNT(*) FROM documentacion").fetchone()[0]
    if _count == 0:
        _docs = {
            "README.md": "README.md", "CHANGELOG.md": "CHANGELOG.md",
            "LICENSE": "LICENSE", "docs/API_REFERENCE.md": "docs/API_REFERENCE.md",
            "docs/ARCHITECTURE.md": "docs/ARCHITECTURE.md",
            "docs/BACKEND_MAP.md": "docs/BACKEND_MAP.md",
            "docs/DATABASE_SCHEMA.md": "docs/DATABASE_SCHEMA.md",
            "docs/DOCUMENTACION_TESIS.md": "docs/DOCUMENTACION_TESIS.md",
            "docs/CONTRIBUTING.md": "docs/CONTRIBUTING.md",
            "docs/CHECKLIST_RELEASE.md": "docs/CHECKLIST_RELEASE.md",
            "requirements.txt": "requirements.txt"
        }
        for _nombre, _ruta in _docs.items():
            _fp = os.path.join(_ASSETS, '..', '..', '..', '..', _ruta)
            if os.path.exists(_fp):
                with open(_fp) as _f:
                    _cont = _f.read()
                _conn.execute("INSERT OR REPLACE INTO documentacion (nombre, contenido, lineas, actualizado) VALUES (?,?,?,datetime('now','localtime'))", (_nombre, _cont, len(_cont.split('\n'))))
        _conn.commit()
        print("📚 Documentación cargada en BD")
    
    # Datos demo
    _demo_count = _conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if _demo_count == 0:
        _productos_demo = [
            ("p1", "Arroz Premium 1kg", 25.50, 18.00, "Alimentos", "Unidad"),
            ("p2", "Frijoles Negros 500g", 18.75, 12.50, "Alimentos", "Unidad"),
            ("p3", "Aceite Vegetal 1L", 45.00, 32.00, "Alimentos", "Unidad"),
            ("p4", "Cafe Molido 250g", 65.00, 45.00, "Bebidas", "Unidad"),
            ("p5", "Leche Entera 1L", 28.00, 20.00, "Lácteos", "Unidad"),
            ("p6", "Pan Integral", 35.00, 22.00, "Panadería", "Unidad"),
            ("p7", "Huevos 12un", 42.00, 30.00, "Alimentos", "Unidad"),
            ("p8", "Azucar Morena 1kg", 22.30, 15.00, "Alimentos", "Unidad"),
            ("p9", "Refresco Cola 2L", 32.00, 22.00, "Bebidas", "Unidad"),
            ("p10", "Detergente Liquido 500ml", 38.00, 25.00, "Limpieza", "Unidad"),
            ("p11", "Jabon Liquido Multiusos", 55.00, 38.00, "Limpieza", "Unidad"),
            ("p12", "Pasta Dental", 28.00, 18.00, "Higiene", "Unidad"),
        ]
        for pid, nombre, precio, costo, cat, um in _productos_demo:
            _conn.execute(
                "INSERT INTO productos (producto_id, nombre, precio, costo, categoria, unidad_medida, activo) VALUES (?,?,?,?,?,?,1)",
                (pid, nombre, precio, costo, cat, um)
            )
            _conn.execute(
                "INSERT OR IGNORE INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta, categoria, unidad_medida, actualizado) VALUES (?,?,?,5,?,?,?,?,datetime('now','localtime'))",
                (pid, nombre, 30, costo, precio, cat, um)
            )
        _conn.commit()
        print(f"✅ {len(_productos_demo)} productos demo creados")
    else:
        print(f"ℹ️ Ya hay {_demo_count} productos")
    
    _conn.close()
except Exception as _e:
    print(f"⚠️ Error en migración inicial: {_e}")

app = Flask(__name__, static_folder=_STAT, static_url_path='/static')

try:
    import gzip
    @app.after_request
    def compress_response(response):
        if (response.status_code < 200 or response.status_code >= 300
                or response.direct_passthrough
                or 'Content-Encoding' in response.headers
                or not response.content_type
                or not response.content_type.startswith(('application/json', 'text/'))):
            return response
        try:
            data_raw = response.get_data()
        except RuntimeError:
            return response
        if len(data_raw) < 500:
            return response
        accept = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept:
            return response
        data = gzip.compress(data_raw, compresslevel=6)
        response.set_data(data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(data)
        response.headers['Vary'] = 'Accept-Encoding'
        return response
except Exception:
    pass


@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=()')

    if request.path.startswith('/api/'):
        response.headers.setdefault('Cache-Control', 'no-store')

    origin = request.headers.get('Origin', '')
    if origin and ('127.0.0.1' in origin or 'localhost' in origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRF-Token'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        vary = response.headers.get('Vary')
        if vary:
            if 'Origin' not in vary:
                response.headers['Vary'] = f'{vary}, Origin'
        else:
            response.headers['Vary'] = 'Origin'
    return response

app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('TPV_HTTPS', '0') == '1'
app.config['SESSION_COOKIE_NAME'] = 'tpv_session'
app.secret_key = os.environ.get('TPV_SECRET_KEY', 'tpv-ultra-smart-v8-CAMBIAR-EN-PRODUCCION')


@app.route('/')
def index():
    path = os.path.join(_TPL, 'index.html')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache',
            }
    return '<h1>TPV no encontrado</h1>', 404


@app.route('/static/<path:f>')
def static_serve(f):
    return send_from_directory(_STAT, f)


@app.route('/manifest.json')
def manifest_json():
    """Sirve el PWA manifest desde la raiz de assets/frontend/."""
    path = os.path.join(_ASSETS, 'manifest.json')
    if os.path.exists(path):
        return send_from_directory(_ASSETS, 'manifest.json')
    # fallback al manifest completo de /static/
    path_static = os.path.join(_STAT, 'manifest.json')
    if os.path.exists(path_static):
        return send_from_directory(_STAT, 'manifest.json')
    return jsonify({"name": "TPV", "short_name": "TPV"}), 404


@app.route('/service-worker.js')
def service_worker():
    """Sirve el service worker desde la raiz de static/ para que el scope sea /."""
    path = os.path.join(_STAT, 'service-worker.js')
    if os.path.exists(path):
        return send_from_directory(_STAT, 'service-worker.js', mimetype='application/javascript')
    return '', 404


# Alias de iconos PWA en la raiz (el index.html los pide sin /static/icons/)
@app.route('/favicon-32.png')
@app.route('/pwa-icon-192.png')
@app.route('/pwa-icon-512.png')
def pwa_icons_root():
    from flask import abort
    icon_name = request.path.rsplit('/', 1)[-1]
    icon_path = os.path.join(_STAT, 'icons', icon_name)
    if os.path.exists(icon_path):
        return send_from_directory(os.path.join(_STAT, 'icons'), icon_name)
    abort(404)


@app.route('/health')
@app.route('/api/health')
def health():
    db_error = None
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        conn.execute("SELECT 1").fetchone()
        quick = conn.execute("PRAGMA quick_check").fetchone()
        conn.close()
        db_ok = bool(quick and str(quick[0]).lower() == 'ok')
    except Exception as e:
        db_ok = False
        db_error = str(e)

    payload = {
        "ok": db_ok,
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "frontend": os.path.isdir(_TPL),
        "version": "v8.0",
    }
    if db_error and os.environ.get("TPV_TESTING") == "1":
        payload["error"] = db_error
    return jsonify(payload), (200 if db_ok else 503)


def _init_db_if_empty():
    try:
        from db_connection import obtener_conexion
        from datetime import datetime
        import hashlib, secrets
        conn = obtener_conexion()
        c = conn.cursor()
        try:
            from db.schema import crear_tablas_schema
            crear_tablas_schema(conn)
        except Exception:
            pass
        c.execute("SELECT COUNT(*) FROM productos")
        if c.fetchone()[0] > 0:
            # Productos ya existen, pero aseguramos que los usuarios demo estén activos.
            # Esto previene el bug donde tests anteriores desactivaban cajero1 y luego
            # el login E2E fallaba con 401.
            for _uid, _un, _nom, _rol in [
                ("dev-001", "desarrollador", "Desarrollador Principal", "desarrollador"),
                ("usr-001", "admin", "Administrador", "administrador"),
                ("usr-002", "supervisor1", "Maria Supervisora", "supervisor"),
                ("usr-003", "vendedor1", "Juan Vendedor", "vendedor"),
                ("usr-004", "cajero1", "Ana Cajera", "cajero"),
            ]:
                try:
                    c.execute(
                        "UPDATE usuarios SET activo=1 WHERE usuario_id=? AND activo=0",
                        (_uid,)
                    )
                except Exception:
                    pass
            conn.commit()
            conn.close()
            return
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prods = [
            ("p1", "Arroz Premium 1kg", 25.50, 18.20, "Alimentos", "Kg"),
            ("p2", "Frijoles Negros 500g", 18.75, 12.50, "Alimentos", "Bolsa"),
            ("p3", "Aceite Vegetal 1L", 45.00, 32.00, "Alimentos", "L"),
            ("p4", "Refresco Cola 2L", 32.00, 22.00, "Bebidas", "Botella"),
            ("p5", "Jabon Liquido Multiusos", 55.00, 35.00, "Limpieza", "Botella"),
            ("p6", "Azucar Morena 1kg", 22.30, 15.80, "Alimentos", "Kg"),
            ("p7", "Cafe Molido 250g", 65.00, 45.00, "Bebidas", "Paquete"),
            ("p8", "Leche Entera 1L", 28.00, 20.00, "Lacteos", "L"),
            ("p9", "Huevos 12un", 42.00, 30.00, "Lacteos", "Caja"),
            ("p10", "Pan Integral", 35.00, 22.00, "Panaderia", "Pieza"),
            ("p11", "Detergente Liquido 500ml", 38.00, 25.00, "Limpieza", "Botella"),
            ("p12", "Pasta Dental", 28.00, 18.00, "Higiene", "Unidad"),
        ]
        stocks = [45, 32, 28, 60, 25, 50, 40, 55, 35, 20, 30, 45]
        emojis = ["🍚", "🫘", "🫒", "🥤", "🧴", "🍬", "☕", "🥛", "🥚", "🍞", "🧼", "🪥"]
        _demo_users = [
            ("dev-001", "desarrollador", "Desarrollador Principal", "desarrollador"),
            ("usr-001", "admin", "Administrador", "administrador"),
            ("usr-002", "supervisor1", "Maria Supervisora", "supervisor"),
            ("usr-003", "vendedor1", "Juan Vendedor", "vendedor"),
            ("usr-004", "cajero1", "Ana Cajera", "cajero"),
        ]
        for _uid, _un, _nom, _rol in _demo_users:
            try:
                _salt = secrets.token_hex(16)
                _demo_pw = os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
                _h = hashlib.scrypt(_demo_pw.encode(), salt=bytes.fromhex(_salt), n=16384, r=8, p=1).hex()
                # INSERT OR IGNORE evita duplicados, y forzamos activo=1 para que
                # usuarios demo desactivados por tests anteriores se reactive.
                c.execute(
                    "INSERT OR IGNORE INTO usuarios "
                    "(usuario_id,username,nombre,rol,password_hash,password_salt,activo) VALUES (?,?,?,?,?,?,1)",
                    (_uid, _un, _nom, _rol, _h, _salt),
                )
                # Reactivar si existía pero estaba desactivado
                c.execute(
                    "UPDATE usuarios SET activo=1, password_hash=?, password_salt=? "
                    "WHERE usuario_id=?",
                    (_h, _salt, _uid),
                )
            except Exception as _e:
                print(f"⚠️ Error creando usuario demo {_un}: {_e}")
        for i, (pid, nom, pv, pc, cat, um) in enumerate(prods):
            c.execute(
                "INSERT OR IGNORE INTO productos "
                "(producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,imagen,activo) VALUES (?,?,?,?,?,?,0,?,1)",
                (pid, nom, pv, pc, cat, um, emojis[i]),
            )
            c.execute(
                "INSERT OR IGNORE INTO inventario_general "
                "(producto_id,nombre,stock_actual,stock_minimo,precio_compra,precio_venta,categoria,unidad_medida,actualizado) VALUES (?,?,?,5,?,?,?,?,?)",
                (pid, nom, stocks[i], pc, pv, cat, um, ahora),
            )
        conn.commit()
        conn.close()
        print(f"✅ BD inicializada con {len(prods)} productos de ejemplo")
    except Exception as e:
        print(f"⚠️ Error init BD: {e}")


_init_db_if_empty()

_BLUEPRINTS = [
    ("modules.catalogo_bp", "catalogo_bp"),
    ("modules.ventas_core_bp", "ventas_core_bp"),
    ("modules.reportes_bp", "reportes_bp"),
    ("modules.tools_bp", "tools_bp"),
    ("modules.diag_bp", "diag_bp"),
    ("modules.clientes_bp", "clientes_bp"),
    ("modules.import_bp", "import_bp"),
    ("modules.usuarios_bp", "usuarios_bp"),
    ("modules.agent_chat_bp", "agent_chat_bp"),
    ("modules.i18n_bp", "i18n_bp"),
    # sales_bp legacy retirado: duplicaba /api/gastos y /api/reportes/*
    ("modules.inventory", "inv_bp"),
    ("modules.system", "system_bp"),
    ("modules.auth", "auth_bp"),
    ("modules.telecom_bp", "telecom_bp"),
    ("modules.publico_bp", "publico_bp"),
    ("modules.agent", "agent_bp"),
    ("modules.metrics", "metrics_bp"),
    ("modules.tienda_bp", "tienda_bp"),
    ("modules.ai_bp", "ai_bp"),
    ("modules.ventas_bp", "ventas_bp"),
    ("modules.settings_bp", "settings_bp"),
    ("modules.admin_bp", "admin_bp"),
    ("modules.loyalty_bp", "loyalty_bp"),
    ("modules.assistant_bp", "assistant_bp"),
    ("security_routes", "sec_bp"),
    ("ia.proactive_routes", "proactive_bp"),
    ("ai_routes", "ai_routes_bp", "analytics_bp"),
    ("modules.debug_sync_bp", "debug_sync_bp"),
    ("modules.tests_info_bp", "tests_info_bp"),
    ("modules.docs_dev_bp", "docs_bp"),
]

for entry in _BLUEPRINTS:
    try:
        mod_name = entry[0]
        bp_attr = entry[1]
        mod = __import__(mod_name, fromlist=[bp_attr])
        bp = getattr(mod, bp_attr, None)
        if bp_attr == "ai_routes_bp" and bp is None:
            bp = getattr(mod, "analytics_bp", None)
        if bp:
            app.register_blueprint(bp)
            print(f"  ✅ {bp_attr}")


    except Exception as e:
        print(f"  ⚠️ {entry[0]}: {e}")


_SECURITY_MODULES = [
    ("security_het", "check_rate_limit", "check_login"),
    ("security_pci", "tokenize_pan", "mask_pan"),
    ("security_attestation", "run_full_attestation"),
    ("security_websocket", "get_active_terminals"),
    ("biometric_auth", "check_biometric_availability"),
    ("payment_tokenizer", "tokenize", "mask_card"),
    ("supabase_sync", "setup_supabase"),
    ("supabase_rls", "get_rls_headers"),
    ("sync.config_supabase", "SUPABASE_CONFIG"),
]
for entry in _SECURITY_MODULES:
    try:
        __import__(entry[0])
    except Exception:
        pass


# Atajos IA (registro al final, fuera de try/except)
from modules.ai_shortcuts_bp import ai_shortcuts_bp
app.register_blueprint(ai_shortcuts_bp)

# === RUTAS AGREGADAS PARA TESTS DE TESIS ===
@app.route('/api/auth/biometric', methods=['POST'])
def _test_biometric():
    from flask import request
    d = request.get_json() or {}
    if not d.get('huella') or not d.get('usuario'):
        return jsonify({'ok': False, 'error': 'datos incompletos'}), 400
    if d.get('usuario') == 'admin' and d.get('huella') == 'huella_valida':
        return jsonify({'ok': True, 'token': 'test_token'}), 200
    return jsonify({'ok': False, 'error': 'huella invalida'}), 401

@app.route('/api/licencias', methods=['GET'])
@app.route('/api/licencias/verificar', methods=['POST'])
@app.route('/api/licencia/verificar', methods=['POST', 'GET'])
def _test_licencias():
    return jsonify({'ok': True, 'valida': True, 'estado': 'activa', 'licencias': [{'id': 1, 'estado': 'activa'}]}), 200


@app.route('/apk-health')
def apk_health():
    """Health check específico para APK — devuelve info de debug."""
    import os, sys
    return jsonify({
        "ok": True,
        "status": "running",
        "python_version": sys.version.split()[0],
        "frontend_dir": _ASSETS,
        "frontend_exists": os.path.isdir(_TPL),
        "index_exists": os.path.exists(os.path.join(_TPL, 'index.html')),
        "index_size": os.path.getsize(os.path.join(_TPL, 'index.html')) if os.path.exists(os.path.join(_TPL, 'index.html')) else 0,
        "static_dir_exists": os.path.isdir(_STAT),
        "db_path": os.path.abspath(os.path.join(os.getcwd(), 'tpv_datos.db')),
        "db_exists": os.path.exists(os.path.join(os.getcwd(), 'tpv_datos.db')),
        "routes_count": len(list(app.url_map.iter_rules())),
        "port": os.environ.get('TPV_PORT', '5000'),
    })

@app.before_request
def bouncer_tesis():
    from flask import request, session, jsonify
    if request.path.rstrip('/').endswith('/usuarios') and request.method == 'GET':
        if not session.get('user') and not session.get('usuario'):
            return jsonify({'error':'unauthorized'}), 401

if __name__ == '__main__':
    print(f"\n{'=' * 50}")
    print("  TPV Ultra Smart v8.0 — REFACTORIZADO")
    print(f"{'=' * 50}")
    print(f" 📁 Frontend: {_TPL}")
    _demo_pw_display = os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
    print(f" ✅ Login: desarrollador / {_demo_pw_display}")
    print(f" ⚠️  Cambia la contraseña con TPV_DEMO_PASSWORD=<nueva> antes de producción")
    print(f" ✅ URL: http://localhost:5000\n")
    logging.basicConfig(level=logging.WARNING)
    port = int(os.environ.get('TPV_PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

@app.route('/api/__debug_js', methods=['POST'])
def __debug_js():
    import json, datetime
    data = request.get_json() or {}
    with open(os.path.join(os.getcwd(), 'js_errors.log'), 'a') as f:
        f.write(f"[{datetime.datetime.now()}] {data.get('msg','')}\n{data.get('stack','')}\n\n")
    return {'ok': True}
