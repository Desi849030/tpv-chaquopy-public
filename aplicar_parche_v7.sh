#!/bin/bash
echo "🚀 Aplicando parche TPV v7.0..."
set -e

BASE="app/src/main"
PYTHON="$BASE/python"
ASSETS="$BASE/assets/frontend"

# Crear estructura
mkdir -p "$PYTHON/routes"
mkdir -p "$ASSETS/static/js/tpv"

# ==========================================
# 1. app.py — MODULAR CON TODOS BLUEPRINTS
# ==========================================
cat > "$PYTHON/app.py" << 'EOF'
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
EOF
echo "✅ app.py actualizado"

# ==========================================
# 2. routes/agent.py — AGENTE IA CONVERSACIONAL
# ==========================================
cat > "$PYTHON/routes/agent.py" << 'EOF'
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from database import obtener_conexion, agregar_log

agent_bp = Blueprint('agent', __name__, url_prefix='/api')

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"): return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def usuario_actual(): return session.get("usuario", {})

@agent_bp.route('/agent/query', methods=['POST'])
@requiere_login
def agent_query():
    datos = request.get_json(force=True, silent=True) or {}
    query = datos.get('query', '').lower()
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    respuesta = "No entiendo tu pregunta. Prueba con: 'ventas', 'inventario', 'ayuda' o 'cerrar'."
    tipo = "text"
    data_extra = {}
    try:
        if any(k in query for k in ['venta', 'dinero', 'caja']):
            conn = obtener_conexion()
            hoy = datetime.now().strftime('%Y-%m-%d')
            vid = u['usuario_id'] if rol == 'vendedor' else None
            filtro = "WHERE vendedor_id = ?" if vid else ""
            params = (vid,) if vid else ()
            cursor = conn.execute(f"SELECT COUNT(*) as num, SUM(total) as total FROM historial_ventas {filtro} AND fecha LIKE ?", params + (f"{hoy}%",))
            res = cursor.fetchone()
            conn.close()
            respuesta = f"📊 Ventas hoy: ${res['total'] or 0:.2f} ({res['num'] or 0} transacciones)"
        elif any(k in query for k in ['stock', 'inventario', 'producto']):
            conn = obtener_conexion()
            cursor = conn.execute("SELECT COUNT(*) as total FROM productos WHERE activo=1")
            res = cursor.fetchone()
            conn.close()
            respuesta = f"📦 Inventario: {res['total'] or 0} productos activos"
        elif 'qr' in query:
            respuesta = "🔲 Ve a Gestión → Etiquetas QR para generar códigos"
            tipo = "action"; data_extra = {"target": "cliente-qr-tab"}
        elif 'exportar' in query or 'backup' in query:
            respuesta = "📤 Ve a Herramientas → Exportar para descargar datos"
        elif 'cerrar' in query or 'turno' in query:
            respuesta = "🔒 Ve a Inventario → Cerrar Día para registrar el cierre"
        elif 'ayuda' in query:
            respuesta = "🤖 Puedo ayudarte con: ventas, inventario, QR, exportar, cerrar día. ¿Qué necesitas?"
        agregar_log(f"IA: {u.get('username')} preguntó: {query[:50]}...", 'info')
        return jsonify({'ok': True, 'respuesta': respuesta, 'tipo': tipo, 'data': data_extra})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@agent_bp.route('/agent/suggestions', methods=['GET'])
@requiere_login
def agent_suggestions():
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    comunes = ["¿Cuánto vendí hoy?", "¿Qué productos tengo en stock bajo?", "¿Cómo genero QR?"]
    por_rol = {
        'desarrollador': ["¿Cómo activo una licencia?", "¿Cómo sincronizo con Supabase?"],
        'administrador': ["¿Cómo creo un nuevo usuario?", "¿Cómo asigno inventario?"],
        'vendedor': ["¿Cuánto me falta para cerrar?", "¿Cómo registro una venta?"]
    }
    return jsonify({'ok': True, 'sugerencias': comunes + por_rol.get(rol, [])})
EOF
echo "✅ routes/agent.py creado"

# ==========================================
# 3. routes/metrics.py — DASHBOARD MÉTRICAS
# ==========================================
cat > "$PYTHON/routes/metrics.py" << 'EOF'
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta
from database import obtener_conexion, agregar_log

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')
def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"): return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper
def usuario_actual(): return session.get("usuario", {})

@metrics_bp.route('/dashboard/kpis', methods=['GET'])
@requiere_login
def api_kpis_dashboard():
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    hoy = datetime.now().strftime('%Y-%m-%d')
    conn = obtener_conexion()
    try:
        vid = u['usuario_id'] if rol == 'vendedor' else None
        filtro = "AND vendedor_id = ?" if vid else ""
        params = (vid,) if vid else ()
        cursor = conn.execute(f"SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ? {filtro}", (f"{hoy}%",) + params)
        hoy_stats = dict(cursor.fetchone() or {})
        cursor = conn.execute("SELECT COUNT(*) as stock_bajo FROM inventario_general WHERE stock_actual < 5 AND stock_actual >= 0")
        stock_bajo = cursor.fetchone()['stock_bajo'] or 0
        return jsonify({"ok": True, "kpis": {
            "ventas_hoy": {"num_ventas": hoy_stats.get('num_ventas') or 0, "total_ingresos": float(hoy_stats.get('total_ingresos') or 0), "unidades": int(hoy_stats.get('unidades') or 0)},
            "stock_bajo": stock_bajo,
            "timestamp": datetime.now().isoformat()
        }})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
EOF
echo "✅ routes/metrics.py creado"

# ==========================================
# 4. tpv_agent.js — INTERFAZ VISUAL AGENTE
# ==========================================
cat > "$ASSETS/static/js/tpv/tpv_agent.js" << 'EOF'
// ══════════════════════════════════════════════════════════════
//  TPV AGENT — Asistente IA Conversacional v7.0
// ══════════════════════════════════════════════════════════════
const TPV_AGENT = {
    activo: false,
    panel: null,
    rol: null,
    init(rol) {
        this.rol = rol;
        if (document.getElementById('agent-container')) return;
        const container = document.createElement('div');
        container.id = 'agent-container';
        container.innerHTML = `
            <div id="agent-btn" onclick="TPV_AGENT.toggle()" style="position:fixed;bottom:20px;right:20px;z-index:9999;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#5b21b6);box-shadow:0 4px 20px rgba(124,58,237,0.4);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform 0.2s;font-size:24px;color:white;">🤖</div>
            <div id="agent-panel" style="position:fixed;bottom:90px;right:20px;z-index:9998;width:320px;max-width:90vw;height:400px;max-height:60vh;background:white;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,0.15);display:none;flex-direction:column;overflow:hidden;border:1px solid #e2e8f0;">
                <div style="padding:12px 16px;background:#f8fafc;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;"><strong>🤖 Asistente TPV</strong><button onclick="TPV_AGENT.toggle()" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:#64748b;">×</button></div>
                <div id="agent-messages" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;"></div>
                <div style="padding:12px;border-top:1px solid #e2e8f0;display:flex;gap:8px;">
                    <input id="agent-input" type="text" placeholder="Pregunta algo..." style="flex:1;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;outline:none;" onkeypress="if(event.key==='Enter')TPV_AGENT.send()">
                    <button onclick="TPV_AGENT.send()" style="background:#7c3aed;color:white;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;">➤</button>
                </div>
            </div>`;
        document.body.appendChild(container);
        this.addMessage('¡Hola! Soy tu asistente TPV. ¿En qué puedo ayudarte?', 'agent');
        this.activo = true;
    },
    toggle() {
        const panel = document.getElementById('agent-panel');
        panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
        if (panel.style.display === 'flex') document.getElementById('agent-input')?.focus();
    },
    addMessage(text, from) {
        const container = document.getElementById('agent-messages');
        const div = document.createElement('div');
        const isUser = from === 'user';
        div.style.cssText = `padding:10px;border-radius:12px;max-width:85%;font-size:0.9rem;background:${isUser?'#7c3aed':'#f1f5f9'};color:${isUser?'white':'#334155'};align-self:${isUser?'flex-end':'flex-start'};margin-bottom:4px;`;
        div.innerText = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },
    async send() {
        const input = document.getElementById('agent-input');
        const msg = input.value.trim();
        if (!msg) return;
        this.addMessage(msg, 'user');
        input.value = '';
        try {
            const res = await fetch('/api/agent/query', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({query:msg, rol:this.rol})
            });
            const data = await res.json();
            setTimeout(() => this.addMessage(data.respuesta || 'Error', 'agent'), 400);
            if (data.tipo === 'action' && data.data?.target) {
                setTimeout(() => document.getElementById(data.data.target)?.click(), 600);
            }
        } catch(e) {
            this.addMessage('Error de conexión', 'agent');
        }
    }
};
document.addEventListener('DOMContentLoaded', () => {
    if (window.AUTH?.usuario) TPV_AGENT.init(window.AUTH.usuario.rol);
});
EOF
echo "✅ tpv_agent.js creado"

echo "🎉 ¡PARCHE V7.0 APLICADO CON ÉXITO!"
echo "📂 Estructura creada:"
echo "   ├─ app.py (modular con 8 blueprints)"
echo "   ├─ routes/agent.py (Agente IA)"
echo "   ├─ routes/metrics.py (Dashboard KPIs)"
echo "   └─ tpv_agent.js (Interfaz visual)"
echo ""
echo "✅ Ahora ejecuta:"
echo "   cd ~/tpv-chaquopy"
echo "   git add ."
echo "   git commit -m 'feat: TPV v7.0 - Modular + Agente IA + Métricas + Seguridad'"
echo "   git push origin main"
