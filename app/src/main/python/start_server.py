"""Android bootstrap — security, IA Edge, MPOC, SSE and Loyalty.
Historical component fixes:
  - Eliminado doble registro de assistant_bp (ya se registra en app.py)
  - Set TPV_DB_PATH para que ia_assistant.py encuentre la DB rapido
  - IA Assistant se carga DESPUES de crear_tablas para asegurar DB lista
"""
import sys,os,threading,traceback,time
from version import __version__
print(f"[TPV] Iniciando TPV Ultra Smart v{__version__}...",flush=True)
try:
    from java.lang import System
    FILES_DIR=str(System.getProperty("TPV_FILES_DIR"))
    FRONTEND_DIR=str(System.getProperty("TPV_FRONTEND_DIR"))
except Exception as e:
    FILES_DIR=os.getcwd(); FRONTEND_DIR=os.path.join(FILES_DIR,"frontend")
os.chdir(FILES_DIR); sys.path.insert(0,FILES_DIR)
os.environ["TPV_FILES_DIR"]=FILES_DIR
os.environ["TPV_FRONTEND_DIR"]=FRONTEND_DIR
# v9.0 CRITICAL: Set TPV_DB_PATH para ia_assistant.py encuentre la DB
_db_path = os.path.join(FILES_DIR, "tpv_datos.db")
os.environ["TPV_DB_PATH"]=_db_path
print("[TPV] DB path: %s" % _db_path, flush=True)

print("[TPV] Cargando blindaje PCI-DSS...",flush=True)
try:
    from security_pci import tokenize_pan,mask_pan,validate_luhn,process_payment_token
    print("[TPV] PCI-DSS OK",flush=True)
except Exception as e:
    print(f"[TPV] PCI-DSS advertencia: {e}",flush=True)
print("[TPV] Cargando blindaje HET...",flush=True)
try:
    from security_het import create_het_middleware,check_login,record_login_result,get_threat_summary
    print("[TPV] HET OK",flush=True)
except Exception as e:
    print(f"[TPV] HET advertencia: {e}",flush=True)
print("[TPV] Cargando blindaje WebSockets...",flush=True)
try:
    from security_websocket import create_ws_routes,register_terminal,notify_sale,start_cleanup_thread
    start_cleanup_thread()
    print("[TPV] WebSockets OK",flush=True)
except Exception as e:
    print(f"[TPV] WebSockets advertencia: {e}",flush=True)
try:
    from app import app as flask_app
    print("[TPV] Flask app importada OK",flush=True)
except Exception as e:
    print(f"[TPV] ERROR app: {e}",flush=True); traceback.print_exc(); raise
try:
    create_het_middleware(flask_app)
    print("[TPV] HET middleware integrado",flush=True)
except Exception as e:
    print(f"[TPV] HET middleware adv: {e}",flush=True)
try:
    create_ws_routes(flask_app)
    print("[TPV] WebSocket rutas integradas",flush=True)
except Exception as e:
    print(f"[TPV] WS rutas adv: {e}",flush=True)
try:
    from security_routes import sec_bp
    flask_app.register_blueprint(sec_bp)
    print("[TPV] Security API rutas integradas",flush=True)
except Exception as e:
    print(f"[TPV] Security routes adv: {e}",flush=True)
try:
    from database import crear_tablas; crear_tablas()
    print("[TPV] Tablas OK",flush=True)
except Exception as e:
    print(f"[TPV] DB error: {e}",flush=True); traceback.print_exc()
try:
    from tienda_routes import crear_tablas_tienda; crear_tablas_tienda()
    print("[TPV] Tablas tienda OK",flush=True)
except Exception as e:
    print(f"[TPV] Tienda adv: {e}",flush=True)
try:
    from migrar_tablas_tienda import migrar; migrar()
    print("[TPV] Migracion OK",flush=True)
except Exception as e:
    print(f"[TPV] Migracion adv: {e}",flush=True)
try:
    from inject_rol_fix import injectar_script; injectar_script(flask_app)
    print("[TPV] Fix rol OK",flush=True)
except Exception as e:
    print(f"[TPV] Rol fix adv: {e}",flush=True)

def _run_flask():
    try:
        print("[TPV] Flask en http://127.0.0.1:5050",flush=True)
        flask_app.run(host="127.0.0.1",port=5050,debug=False,use_reloader=False,threaded=True)
    except Exception as e:
        print(f"[TPV] ERROR Flask: {e}",flush=True); traceback.print_exc()

t=threading.Thread(target=_run_flask,daemon=False); t.start()

# Esperar a que Flask esté listo (hasta 15 segundos)
for i in range(30):
    time.sleep(0.5)
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:5050/api/health",timeout=1)
        print("[TPV] Flask listo en http://127.0.0.1:5050",flush=True); break
    except: pass
time.sleep(1)

# v9.0: Cargar IA Assistant DESPUES de que Flask y la DB estan listos
print("[TPV] Cargando Asistente IA v9.0 (aprendizaje + SQLite + rol automatico)...",flush=True)
try:
    from ia_assistant import _init_learning_table; _init_learning_table()
    print("[TPV] IA Learning tabla OK",flush=True)
except Exception as e:
    print(f"[TPV] IA Learning adv: {e}",flush=True)

# v9.0: NO registrar assistant_bp de nuevo (ya lo hace app.py)
# Verificar que el modulo está cargado y accesible
try:
    from ia_assistant_routes import assistant_bp
    # Verificar si ya está registrado (app.py lo registra al importar)
    already_registered = False
    for rule in flask_app.url_map.iter_rules():
        if '/api/ia/chat' in str(rule):
            already_registered = True
            break
    if not already_registered:
        flask_app.register_blueprint(assistant_bp)
        print("[TPV] IA Assistant v9.0 blueprint registrado",flush=True)
    else:
        print("[TPV] IA Assistant v9.0 ya estaba registrado (via app.py)",flush=True)
except Exception as e:
    print(f"[TPV] IA Assistant adv: {e}",flush=True)

print("[TPV] Cargando IA Edge + Loyalty + MPOC...",flush=True)
# ai_bp y analytics_bp ya se registran en app.py (evitar doble registro)
try:
    from ai_routes import ai_bp, analytics_bp
    # Verificar si ya estan registrados (app.py los registra al importar)
    ai_registered = any('/api/ai/' in str(rule) for rule in flask_app.url_map.iter_rules())
    analytics_registered = any('/api/analytics/' in str(rule) for rule in flask_app.url_map.iter_rules())
    if not ai_registered:
        flask_app.register_blueprint(ai_bp)
    if not analytics_registered:
        flask_app.register_blueprint(analytics_bp)
    print("[TPV] IA Edge API integrada (ai_bp + analytics_bp)",flush=True)
except Exception as e:
    print(f"[TPV] IA Edge adv: {e}",flush=True)
try:
    from loyalty_routes import loyalty_bp
    flask_app.register_blueprint(loyalty_bp)
    print("[TPV] Loyalty + Headless Commerce OK",flush=True)
except Exception as e:
    print(f"[TPV] Loyalty adv: {e}",flush=True)
try:
    from security_attestation import run_full_attestation
    print("[TPV] MPOC Attestation OK",flush=True)
except Exception as e:
    print(f"[TPV] MPOC Attestation adv: {e}",flush=True)

# v9.0: Verificar que el IA ping responde
try:
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:5050/api/ia/ping",timeout=5)
    data = resp.read().decode()
    print("[TPV] IA Ping: %s" % data.strip(),flush=True)
except Exception as e:
    print(f"[TPV] IA Ping fallo: {e}",flush=True)

print(f"[TPV] Bootstrap v{__version__} completado: seguridad, IA Edge, MPOC, SSE y Loyalty activos",flush=True)
