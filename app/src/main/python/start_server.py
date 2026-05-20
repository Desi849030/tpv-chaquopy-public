# === CRASH DEBUG v1 ===
import traceback, os as _crash_os
_crash_log = _crash_os.path.join(_crash_os.path.dirname(_crash_os.path.abspath(__file__)), '..', '..', 'crash_log.txt')

import sys, os, threading, traceback, time
_log_file = None
def _w(msg):
    try:
        if _log_file: _log_file.write(msg+"\n"); _log_file.flush()
    except Exception: pass
    print(msg, flush=True)
_w("=== TPV v2.5.5 ===")
try:
    from java.lang import System
    FILES_DIR = str(System.getProperty("TPV_FILES_DIR"))
    FRONTEND_DIR = str(System.getProperty("TPV_FRONTEND_DIR"))
except Exception:
    FILES_DIR = os.getcwd()
    FRONTEND_DIR = os.path.join(FILES_DIR, "frontend")
os.chdir(FILES_DIR); sys.path.insert(0, FILES_DIR)
os.environ["TPV_FILES_DIR"] = FILES_DIR
os.environ["TPV_FRONTEND_DIR"] = FRONTEND_DIR
try:
    _log_file = open(os.path.join(FILES_DIR, "tpv_debug.log"), "w")
except Exception: pass
os.environ["TPV_DB_PATH"] = os.path.join(FILES_DIR, "tpv_datos.db")
_w("[INFO] DIR: " + FILES_DIR)
_w("[INFO] Python: " + str(sys.version))
_w("[INFO] Cargando PCI-DSS...")
try:
    from security_pci import tokenize_pan,mask_pan,validate_luhn,process_payment_token
    _w("[INFO] PCI-DSS OK")
except Exception as e:
    _w("[WARN] PCI-DSS: " + str(e))
_w("[INFO] Cargando HET...")
try:
    from security_het import create_het_middleware,check_login,record_login_result,get_threat_summary
    _w("[INFO] HET OK")
except Exception as e:
    _w("[WARN] HET: " + str(e))
_w("[INFO] Cargando WebSockets...")
try:
    from security_websocket import create_ws_routes,register_terminal,notify_sale,start_cleanup_thread
    start_cleanup_thread()
    _w("[INFO] WebSockets OK")
except Exception as e:
    _w("[WARN] WebSockets: " + str(e))
_w("[INFO] Importando app.py...")
flask_app = None
try:
    from app import app as flask_app
    _w("[INFO] Flask OK")
except Exception as e:
    _w("[ERROR] FATAL app.py: " + str(e))
    _w("[ERROR] " + traceback.format_exc())
    raise
try: create_het_middleware(flask_app); _w("[INFO] HET mw OK")
except Exception as e: _w("[WARN] HET mw: " + str(e))
try: create_ws_routes(flask_app); _w("[INFO] WS routes OK")
except Exception as e: _w("[WARN] WS: " + str(e))
try:
    from security_routes import sec_bp
    flask_app.register_blueprint(sec_bp)
    _w("[INFO] Sec routes OK")
except Exception as e: _w("[WARN] Sec: " + str(e))
_w("[INFO] Creando tablas...")
try:
    from database import crear_tablas; crear_tablas()
    _w("[INFO] Tablas OK")
except Exception as e:
    _w("[ERROR] DB: " + str(e))
    _w("[ERROR] " + traceback.format_exc())
# ── ASEGURAR USUARIO DESARROLLADOR ──
try:
    import sqlite3, os as _os, uuid as _uuid
    from db_connection import _hash_password
    _dbp = _os.path.join(FILES_DIR, "tpv_datos.db")
    if _os.path.exists(_dbp):
        _hp, _sp = _hash_password("123456")
        _cn = sqlite3.connect(_dbp)
        _cn.execute("INSERT OR IGNORE INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt, creado_por, activo) VALUES (?, 'desarrollador', 'Desarrollador Principal', 'desarrollador', ?, ?, 'sistema', 1)", ('dev-'+_uuid.uuid4().hex[:8], _hp, _sp))
        _cn.execute("UPDATE usuarios SET password_hash=?, password_salt=? WHERE username='desarrollador'", (_hp, _sp))
        _cn.commit()
        _cn.close()
        _w("[INFO] Usuario desarrollador asegurado OK")
except Exception as _e:
    _w("[WARN] Dev user: " + str(_e))
try:
    from tienda_routes import crear_tablas_tienda; crear_tablas_tienda()
    _w("[INFO] Tienda OK")
except Exception as e: _w("[WARN] Tienda: " + str(e))
try:
    from migrar_tablas_tienda import migrar; migrar()
    _w("[INFO] Migracion OK")
except Exception as e: _w("[WARN] Migracion: " + str(e))
# inject_rol_fix eliminado - el rol se maneja en el frontend JS
def _run_flask():
    try:
        _w("[INFO] Flask en 127.0.0.1:5050")
        flask_try:
        app.run(host="127.0.0.1",port=5050,debug=False,use_reloader=False,threaded=True)
    except Exception as e:
        _w("[ERROR] Flask crash: " + str(e))
        _w("[ERROR] " + traceback.format_exc())
t=threading.Thread(target=_run_flask,daemon=False); t.start()
_w("[INFO] Esperando Flask...")
for i in range(20):
    time.sleep(0.5)
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:5050/api/health",timeout=1)
        _w("[INFO] Flask LISTO!"); break
    except Exception:
        if i==29: _w("[ERROR] Flask TIMEOUT 15s")
time.sleep(1)
_w("[INFO] Cargando IA...")
try:
    from tools.i18n_builder import construir_diccionario
    construir_diccionario()
    _w("[INFO] Diccionario i18n actualizado")
except Exception as e:
    _w("[WARN] i18n builder: " + str(e))
# IA: learning table via app.py
# assistant_bp via app.py
# ai_bp + analytics_bp via app.py
# loyalty_bp via app.py
try:
    from security_attestation import run_full_attestation; _w("[INFO] MPOC OK")
except Exception as e: _w("[WARN] MPOC: " + str(e))
_w("[INFO] === v2.5.5 OK ===")
if _log_file: _log_file.close()
