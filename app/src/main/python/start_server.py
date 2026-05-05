"""start_server.py v9.1 — Logging + estabilidad APK"""
import sys, os, threading, traceback, time

def _setup_log():
    import logging
    log_file = '/sdcard/tpv_error.log'
    try:
        logging.basicConfig(filename=log_file, level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s', filemode='w')
    except Exception:
        logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger("TPV")

_log = _setup_log()
def _info(msg):
    print(f"[TPV] {msg}", flush=True); _log.info(msg)
def _warn(msg):
    print(f"[TPV] WARN: {msg}", flush=True); _log.warning(msg)
def _err(msg):
    print(f"[TPV] ERROR: {msg}", flush=True); _log.error(msg)
def _err_exc(msg):
    tb = traceback.format_exc()
    print(f"[TPV] ERROR: {msg}\n{tb}", flush=True); _log.error(f"{msg}\n{tb}")

_info("Iniciando start_server.py v9.1...")

try:
    from java.lang import System
    FILES_DIR = str(System.getProperty("TPV_FILES_DIR"))
    FRONTEND_DIR = str(System.getProperty("TPV_FRONTEND_DIR"))
except Exception as e:
    FILES_DIR = os.getcwd()
    FRONTEND_DIR = os.path.join(FILES_DIR, "frontend")
    _warn(f"Modo escritorio: {e}")

os.chdir(FILES_DIR); sys.path.insert(0, FILES_DIR)
os.environ["TPV_FILES_DIR"] = FILES_DIR
os.environ["TPV_FRONTEND_DIR"] = FRONTEND_DIR
_db_path = os.path.join(FILES_DIR, "tpv_datos.db")
os.environ["TPV_DB_PATH"] = _db_path
_info(f"FILES_DIR: {FILES_DIR}")
_info(f"DB path: {_db_path}")

_info("Cargando blindaje PCI-DSS...")
try:
    from security_pci import tokenize_pan,mask_pan,validate_luhn,process_payment_token
    _info("PCI-DSS OK")
except Exception as e: _warn(f"PCI-DSS: {e}")

_info("Cargando blindaje HET...")
try:
    from security_het import create_het_middleware,check_login,record_login_result,get_threat_summary
    _info("HET OK")
except Exception as e: _warn(f"HET: {e}")

_info("Cargando blindaje WebSockets...")
try:
    from security_websocket import create_ws_routes,register_terminal,notify_sale,start_cleanup_thread
    start_cleanup_thread(); _info("WebSockets OK")
except Exception as e: _warn(f"WebSockets: {e}")

_info("Importando app.py...")
flask_app = None
try:
    from app import app as flask_app
    _info("Flask app importada OK")
except Exception as e:
    _err_exc(f"FATAL: No se pudo importar app.py: {e}"); raise

try:
    create_het_middleware(flask_app); _info("HET middleware OK")
except Exception as e: _warn(f"HET middleware: {e}")

try:
    create_ws_routes(flask_app); _info("WS rutas OK")
except Exception as e: _warn(f"WS rutas: {e}")

try:
    from security_routes import sec_bp
    flask_app.register_blueprint(sec_bp); _info("Security routes OK")
except Exception as e: _warn(f"Security routes: {e}")

try:
    from database import crear_tablas; crear_tablas(); _info("Tablas OK")
except Exception as e: _err_exc(f"DB crear_tablas: {e}")

try:
    from tienda_routes import crear_tablas_tienda; crear_tablas_tienda()
    _info("Tablas tienda OK")
except Exception as e: _warn(f"Tablas tienda: {e}")

try:
    from migrar_tablas_tienda import migrar; migrar(); _info("Migracion OK")
except Exception as e: _warn(f"Migracion: {e}")

try:
    from inject_rol_fix import injectar_script; injectar_script(flask_app)
    _info("Fix rol OK")
except Exception as e: _warn(f"Rol fix: {e}")

def _run_flask():
    try:
        _info("Flask arrancando en http://127.0.0.1:5050")
        flask_app.run(host="127.0.0.1",port=5050,debug=False,use_reloader=False,threaded=True)
    except Exception as e: _err_exc(f"Flask runtime: {e}")

t=threading.Thread(target=_run_flask,daemon=False); t.start()

_info("Esperando Flask...")
for i in range(30):
    time.sleep(0.5)
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:5050/api/health",timeout=1)
        _info("Flask listo"); break
    except Exception:
        if i==29: _err("Flask NO respondio en 15s")
time.sleep(1)

_info("Cargando IA Assistant...")
try:
    from ia_assistant import _init_learning_table; _init_learning_table()
    _info("IA Learning OK")
except Exception as e: _warn(f"IA Learning: {e}")

try:
    from ia_assistant_routes import assistant_bp
    already = any('/api/ia/chat' in str(r) for r in flask_app.url_map.iter_rules())
    if not already: flask_app.register_blueprint(assistant_bp)
    _info("IA Assistant OK")
except Exception as e: _warn(f"IA Assistant: {e}")

_info("Cargando IA Edge + Loyalty + MPOC...")
try:
    from ai_routes import ai_bp, analytics_bp
    ai_reg = any('/api/ai/' in str(r) for r in flask_app.url_map.iter_rules())
    an_reg = any('/api/analytics/' in str(r) for r in flask_app.url_map.iter_rules())
    if not ai_reg: flask_app.register_blueprint(ai_bp)
    if not an_reg: flask_app.register_blueprint(analytics_bp)
    _info("IA Edge OK")
except Exception as e: _warn(f"IA Edge: {e}")

try:
    from loyalty_routes import loyalty_bp
    flask_app.register_blueprint(loyalty_bp); _info("Loyalty OK")
except Exception as e: _warn(f"Loyalty: {e}")

try:
    from security_attestation import run_full_attestation; _info("MPOC OK")
except Exception as e: _warn(f"MPOC: {e}")

try:
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:5050/api/ia/ping",timeout=5)
    _info(f"IA Ping: {resp.read().decode().strip()}")
except Exception as e: _warn(f"IA Ping: {e}")

_info("start_server.py v9.1 completado OK")
