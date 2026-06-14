# -*- coding: utf-8 -*-
"""TPV Ultra Smart v8.0 — Backend Flask (refactorizado)

Todas las rutas están en blueprints dentro de modules/.
Este archivo solo configura Flask, registra blueprints e inicializa la BD.
"""
import os
import sys
import logging

from flask import Flask, send_from_directory, request, jsonify

# ══════════════════════════════════════════════════════════════
# Paths
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# Flask app
# ══════════════════════════════════════════════════════════════
app = Flask(__name__, static_folder=_STAT, static_url_path='/static')

# ── Compresión gzip (Capa 6 - Presentación) ──
try:
    import gzip
    from io import BytesIO
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
    pass  # gzip not available

# ── Security + CORS headers (Capa 7 - Aplicación) ──
@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')

    if request.path.startswith('/api/'):
        response.headers.setdefault('Cache-Control', 'no-store')

    # CORS para loopback/local
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
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 días (no 365)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('TPV_HTTPS', '0') == '1'
app.config['SESSION_COOKIE_NAME'] = 'tpv_session'
app.secret_key = os.environ.get(
    'TPV_SECRET_KEY',
    'tpv-ultra-smart-v8-CAMBIAR-EN-PRODUCCION'
)

# ══════════════════════════════════════════════════════════════
# Frontend (solo 2 rutas: index + static)
# ══════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════
# Auth: movido a modules/auth.py (auth_bp) — #20
# Las rutas /api/auth/login, /api/auth/logout y /api/auth/me
# se registran via blueprint en la sección "Registro de Blueprints".
# ══════════════════════════════════════════════════════════════
# Inicializar BD con datos de ejemplo (si está vacía)
# ══════════════════════════════════════════════════════════════

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
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        c.execute("SELECT COUNT(*) FROM productos")
        if c.fetchone()[0] > 0:
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
        # Usuarios demo
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
                _h = hashlib.scrypt("123456".encode(), salt=bytes.fromhex(_salt),
                                    n=16384, r=8, p=1).hex()
                c.execute(
                    "INSERT OR IGNORE INTO usuarios "
                    "(usuario_id,username,nombre,rol,password_hash,password_salt) "
                    "VALUES (?,?,?,?,?,?)",
                    (_uid, _un, _nom, _rol, _h, _salt))
            except Exception as _e:
                print(f"⚠️ Error creando usuario demo {_un}: {_e}")
        for i, (pid, nom, pv, pc, cat, um) in enumerate(prods):
            c.execute(
                "INSERT OR IGNORE INTO productos "
                "(producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,imagen,activo) "
                "VALUES (?,?,?,?,?,?,0,?,1)",
                (pid, nom, pv, pc, cat, um, emojis[i]))
            c.execute(
                "INSERT OR IGNORE INTO inventario_general "
                "(producto_id,nombre,stock_actual,stock_minimo,precio_compra,precio_venta,"
                "categoria,unidad_medida,actualizado) VALUES (?,?,?,5,?,?,?,?,?)",
                (pid, nom, stocks[i], pc, pv, cat, um, ahora))
        conn.commit()
        conn.close()
        print(f"✅ BD inicializada con {len(prods)} productos de ejemplo")
    except Exception as e:
        print(f"⚠️ Error init BD: {e}")

_init_db_if_empty()

# ══════════════════════════════════════════════════════════════
# Registro de Blueprints
# ══════════════════════════════════════════════════════════════

_BLUEPRINTS = [
    # ── Nuevos (extraídos de app.py) ──
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
    # ── Existentes ──
    ("modules.sales", "sales_bp"),
    ("modules.inventory", "inv_bp"),
    ("modules.system", "system_bp"),
    ("modules.auth", "auth_bp"),
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
]

for entry in _BLUEPRINTS:
    try:
        mod_name = entry[0]
        bp_attr = entry[1]
        # Handle entries with alternative attr names
        mod = __import__(mod_name, fromlist=[bp_attr])
        bp = getattr(mod, bp_attr, None)
        if bp_attr == "ai_routes_bp" and bp is None:
            bp = getattr(mod, "analytics_bp", None)
        if bp:
            app.register_blueprint(bp)
            print(f"  ✅ {bp_attr}")
    except Exception as e:
        print(f"  ⚠️ {entry[0]}: {e}")


# ══════════════════════════════════════════════════════════════
# Módulos de seguridad (carga lazy, no son blueprints)
# ══════════════════════════════════════════════════════════════
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
        pass  # Optional modules

# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f"\n{'=' * 50}")
    print("  TPV Ultra Smart v8.0 — REFACTORIZADO")
    print(f"{'=' * 50}")
    print(f" 📁 Frontend: {_TPL}")
    print(f" ✅ Login: desarrollador / 123456")
    print(f" ✅ URL: http://localhost:5000\n")
    logging.basicConfig(level=logging.WARNING)
    port = int(os.environ.get('TPV_PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
