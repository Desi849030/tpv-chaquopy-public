"""TPV Ultra Smart v7.0 - GitHub/APK Ready"""
from auth_decorator import login_required
import os, sys, pathlib, secrets, logging, time
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory

# Path fix
try:
    from tpv_rutas import fix_path, CARPETA as _CD
    fix_path()
except:
    _CD = os.getcwd()
    for p in ['/storage/emulated/0/TPV_APK', '/sdcard/TPV_APK', os.getcwd()]:
        if os.path.exists(os.path.join(p, 'database.py')):
            if p not in sys.path: sys.path.insert(0, p)
            os.chdir(p); _CD = p; break

# Paths
_MAIN = os.path.dirname(_CD)
_ASSETS = os.path.join(_MAIN, 'assets', 'frontend')
_TPL = os.path.join(_ASSETS, 'templates')
_STAT = os.path.join(_ASSETS, 'static')

# Imports
from database import crear_tablas, login_usuario, obtener_info_db, DB_FILE
from tienda_routes import tienda_bp, crear_tablas_tienda
import supabase_sync as _sb

# Blueprints (conditional)
bps = []
for m in ['auth','inventory','products','sales','system','agent','metrics']:
    try:
        mod = __import__(f'routes.{m}', fromlist=[''])
        for n in dir(mod):
            if n.endswith('_bp'): bps.append(getattr(mod,n)); break
    except: pass

# Flask setup - SIN template_folder para evitar Jinja2
app = Flask(__name__, static_folder=_STAT, static_url_path='/static')
app.config.update(JSON_ENSURE_ASCII=False, SESSION_COOKIE_SAMESITE='Lax', 
                  SESSION_COOKIE_HTTPONLY=True, PERMANENT_SESSION_LIFETIME=86400*7)
_KEY = pathlib.Path(os.environ.get('ANDROID_PRIVATE',_CD)) / '.tpv_key'
if not _KEY.exists(): _KEY.write_text(secrets.token_hex(32))
app.secret_key = _KEY.read_text().strip()

# Register
app.register_blueprint(tienda_bp)
for bp in bps: app.register_blueprint(bp)

# Rate limit
_att = {}
def rate_limit(max_att=5, win=600):
    def dec(f):
        @wraps(f)
        def w(*a,**k):
            u = request.get_json(force=True,silent=True or {}).get('username','').lower()
            now = time.time()
            _att[u] = [t for t in _att.get(u,[]) if now-t < win]
            if len(_att.get(u,[])) >= max_att: return jsonify({'error':'Too many attempts'}),429
            _att.setdefault(u,[]).append(now)
            return f(*a,**k)
        return w
    return dec

# Routes - SERVIR HTML PLANO (sin Jinja2)
@login_required
@app.route('/')
def index():
    path = os.path.join(_TPL, 'index.html')
    if os.path.exists(path):
        with open(path,'r',encoding='utf-8') as f: 
            return f.read(),200,{'Content-Type':'text/html; charset=utf-8'}
    return '<h3>❌ No se encontró index.html</h3>',500

@login_required
@app.route('/static/<path:f>')
def static_serve(f): return send_from_directory(_STAT, f)

@login_required
@app.route('/api/auth/login', methods=['POST'])
@rate_limit()
def login():
    d = request.get_json(force=True,silent=True) or {}
    u,p = d.get('username','').strip(), d.get('password','')
    if not u or not p: return jsonify({'error':'Missing credentials'}),400
    res = login_usuario(u,p)
    if res: session.permanent=True; session['usuario']=res; return jsonify({'ok':True,'usuario':res})
    return jsonify({'error':'Invalid credentials'}),401

@login_required
@app.route('/api/auth/logout', methods=['POST'])
def logout(): session.pop('usuario',None); return jsonify({'ok':True})

@login_required
@app.route('/api/auth/me', methods=['GET'])
def me(): u=session.get('usuario'); return jsonify({'autenticado':bool(u),'usuario':u}) if u else (jsonify({'autenticado':False}),401)

@login_required
@app.route('/api/status')
def status():
    try:
        u = session.get('usuario',{})
        return jsonify({'servidor':'activo','usuario':u.get('username'),'rol':u.get('rol'),
                       'sqlite':{'activo':True,'existe':os.path.exists(DB_FILE)},
                       'supabase':{'activo':_sb.SUPABASE_OK},'db_info':obtener_info_db(),'ts':datetime.now().isoformat()})
    except Exception as e: return jsonify({'error':str(e)}),500

@app.errorhandler(404)
def e404(e): return jsonify({'error':'Not found','code':404}),404
@app.errorhandler(500)
def e500(e): logging.error(f'500: {e}'); return jsonify({'error':'Internal error','detail':str(e)}),500

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print(f"\n{'='*50}\n  TPV Ultra Smart v7.0 (GitHub/APK)\n{'='*50}")
    print(f" 📁 DB: {DB_FILE}\n ✅ Login: desarrollador / dev2024\n ✅ URL: http://localhost:5000\n")
    crear_tablas(); crear_tablas_tienda()
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

if __name__=='__main__': main()

# === PARCHE DE SEGURIDAD ===
from security_patch import generate_csrf, validate_csrf, rate_limit_global, add_security_headers

@app.after_request
def after_request(response):
    return add_security_headers(response)

@login_required
@app.route('/api/csrf-token')
def csrf_token():
    return jsonify({'csrf': generate_cscsrf()})

# === PARCHE DE SEGURIDAD GLOBAL ===
from auth_decorator import csrf_protected

# Headers de seguridad
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

# Generar CSRF token en login
@login_required
@app.route('/api/csrf-token', methods=['GET'])
def get_csrf():
    from security import get_csrf_token
    token = get_csrf_token()
    session['csrf_token'] = token
    return jsonify({'csrf_token': token})

# Logout original ahora limpia csrf
@login_required
@app.route('/api/auth/logout-v2', methods=['POST'])
def logout_v2():
    session.pop('usuario', None)
    session.pop('csrf_token', None)
    return jsonify({'ok': True})
# === FIN PARCHE ===
