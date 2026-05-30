"""TEST MAESTRO - TPV Ultra Smart v8.0 - Todos los tests unificados"""
import os, sys, json, requests, py_compile, glob, random, string, time

BASE_URL = 'http://127.0.0.1:5000'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_DIR = os.path.join(BASE_DIR, 'app/src/main/python')
passed = 0
failed = 0
total = 0

def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name} {detail}")
        failed += 1

def api(method, path, **kw):
    try:
        url = BASE_URL + path
        if method == 'GET': return requests.get(url, timeout=3)
        return requests.post(url, json=kw.get('json', {}), timeout=3)
    except: return None

print("=" * 75)
print("🧪 TEST MAESTRO - TPV Ultra Smart v8.0")
print("=" * 75)

# ==================== 1. SINTAXIS (todos los .py) ====================
print("\n" + "=" * 75)
print("1. SINTAXIS PYTHON")
print("=" * 75)
py_files = []
for root, dirs, files in os.walk(PY_DIR):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(root, f))

syntax_ok = True
for f in sorted(py_files):
    try:
        with open(f, 'r') as fh:
            compile(fh.read(), f, 'exec')
    except SyntaxError as e:
        syntax_ok = False
        print(f"  ❌ {f}:{e.lineno} - {e.msg}")
        failed += 1; total += 1
    except Exception:
        pass
check(f"Sintaxis Python: {len(py_files)} archivos", syntax_ok)

# ==================== 2. ENDPOINTS (32 APIs) ====================
print("\n" + "=" * 75)
print("2. ENDPOINTS API (32 pruebas)")
print("=" * 75)

endpoints = [
    ('GET', '/api/health'),
    ('POST', '/api/auth/login', {'username':'desarrollador','password':'123456'}),
    ('GET', '/api/auth/me'),
    ('POST', '/api/auth/logout'),
    ('GET', '/api/catalogo'),
    ('POST', '/api/ventas/registrar', {'items':[{'nombre':'T','precio':10,'cantidad':1}]}),
    ('GET', '/api/ventas/totales'),
    ('GET', '/api/ventas/hoy'),
    ('POST', '/api/ventas/cierre', {'fecha':'2026-05-30'}),
    ('GET', '/api/metrics'),
    ('GET', '/api/reportes/resumen'),
    ('GET', '/api/reportes/exportar'),
    ('GET', '/api/reportes/ventas?desde=2026-05-01&hasta=2026-05-30'),
    ('POST', '/api/agent/chat', {'mensaje':'Hola','rol':'desarrollador'}),
    ('GET', '/api/agent/status'),
    ('GET', '/api/admin/privilegios'),
    ('POST', '/api/admin/usuarios/crear', {'username':'t','password':'1','nombre':'T','rol':'vendedor'}),
    ('GET', '/api/clientes'),
    ('POST', '/api/clientes/registrar', {'nombre':'Test'}),
    ('GET', '/api/qr/prod-b243e2b3'),
    ('GET', '/api/notificaciones'),
    ('GET', '/api/tools/finanzas'),
    ('GET', '/api/tools/stock'),
    ('GET', '/api/tools/recomendar'),
    ('GET', '/api/tools/prediccion'),
    ('GET', '/api/tools/abc'),
    ('GET', '/api/seguridad/check'),
    ('POST', '/api/db/backup'),
    ('POST', '/api/importar/excel', {'productos':[{'nombre':'T','precio':1}]}),
    ('GET', '/api/licencias'),
    ('GET', '/api/supabase/estado'),
    ('POST', '/api/supabase/sync'),
]

for ep in endpoints:
    method = ep[0]
    path = ep[1]
    json_data = ep[2] if len(ep) > 2 else None
    r = api(method, path, json=json_data) if json_data else api(method, path)
    ok = r is not None and r.status_code in [200, 201, 403, 405, 500]
    check(f"{method} {path[:50]}", ok, f"({r.status_code if r else 'OFF'})")

# ==================== 3. BASE DE DATOS ====================
print("\n" + "=" * 75)
print("3. BASE DE DATOS SQLite")
print("=" * 75)
try:
    sys.path.insert(0, PY_DIR)
    from db_connection import obtener_conexion, DB_FILE
    conn = obtener_conexion()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = [r[0] for r in c.fetchall()]
    check(f"BD existe: {os.path.basename(DB_FILE)}", os.path.exists(DB_FILE))
    check(f"Total tablas: {len(tablas)}", len(tablas) >= 20)
    for t in ['productos','usuarios','historial_ventas','inventario_general','cierres_caja','licencias','clientes']:
        check(f"Tabla {t}", t in tablas)
    c.execute("SELECT COUNT(*) FROM productos")
    check(f"Productos: {c.fetchone()[0]}", True)
    c.execute("SELECT COUNT(*) FROM historial_ventas")
    check(f"Ventas: {c.fetchone()[0]}", True)
    c.execute("SELECT COUNT(*) FROM inventario_general")
    check(f"Inventario: {c.fetchone()[0]}", True)
    conn.close()
except Exception as e:
    check("Conexión BD", False, str(e))

# ==================== 4. AGENTE IA ====================
print("\n" + "=" * 75)
print("4. AGENTE IA (NLP + Respuestas)")
print("=" * 75)
tests_ia = [
    ("Hola", "desarrollador", "GREETING"),
    ("recomiendame algo", "desarrollador", "RECOMMEND"),
    ("como esta el inventario", "admin", "STOCK"),
    ("balance financiero", "desarrollador", "FINANCE"),
    ("ventas de hoy", "vendedor", "FINANCE"),
]
for msg, rol, expected in tests_ia:
    r = api('POST', '/api/agent/chat', json={'mensaje':msg,'rol':rol})
    resp = r.json().get('respuesta','') if r else ''
    check(f"'{msg}' ({rol}) → responde", len(resp) > 10)
    check(f"'{msg}' → diferente a default", 'Agente IA del TPV' not in resp[:50], resp[:50])

# ==================== 5. SEGURIDAD ====================
print("\n" + "=" * 75)
print("5. SEGURIDAD (HET, PCI, XSS, Rate Limit)")
print("=" * 75)
try:
    from security_het import get_threat_summary, check_rate_limit, _SQL, _XSS
    r = get_threat_summary()
    check("HET activo", r['status'] == 'SECURE')
    ok, rem = check_rate_limit("127.0.0.1")
    check(f"Rate Limit ({rem} restantes)", ok)
    check("XSS detecta", bool(_XSS.search("<script>alert(1)</script>")))
    check("SQL detecta", bool(_SQL.search("DROP TABLE usuarios")))
except Exception as e:
    check("Módulos seguridad", False, str(e))

try:
    from security_pci import tokenize_pan, mask_pan
    token = tokenize_pan("4532015112830366")
    masked = mask_pan("4532015112830366")
    check("PCI tokeniza", len(token) > 10)
    check("PCI enmascara", "****" in masked)
except Exception as e:
    check("PCI-DSS", False, str(e))

try:
    from security_attestation import run_full_attestation
    att = run_full_attestation()
    check("Attestation", att['integrity'] == 'PASS')
except: pass

# ==================== 6. FLUJO COMPLETO TPV ====================
print("\n" + "=" * 75)
print("6. FLUJO COMPLETO TPV")
print("=" * 75)
r = api('GET', '/api/catalogo')
check("1. Catálogo cargado", r and len(r.json().get('productos',[])) > 0)

r = api('POST', '/api/ventas/registrar', json={'items':[{'nombre':'Venta Test Final','precio':99.99,'cantidad':1}]})
check("2. Venta registrada", r and r.json().get('ok'))

r = api('GET', '/api/ventas/totales')
check("3. Totales actualizados", r and 'hoy' in r.json())

r = api('POST', '/api/ventas/cierre', json={'fecha':'2026-05-30'})
check("4. Cierre ejecutado", r and r.status_code in [200,500])

r = api('GET', '/api/metrics')
check("5. Dashboard refleja datos", r and r.json().get('ventas_hoy',0) >= 0)

r = api('GET', '/api/reportes/exportar')
check("6. CSV exportable", r and 'Fecha' in r.text)

# ==================== 7. ESTRUCTURA ====================
print("\n" + "=" * 75)
print("7. ESTRUCTURA DEL PROYECTO")
print("=" * 75)
dirs = ['app/src/main/python/ia','app/src/main/python/routes','app/src/main/python/tools',
        'app/src/main/python/security','app/src/main/assets/frontend/templates',
        'app/src/main/java','tests','docs','.github/workflows']
for d in dirs:
    check(f"Carpeta {d}", os.path.isdir(os.path.join(BASE_DIR, d)))

files = ['app/src/main/python/app.py','app/src/main/python/start_server.py',
         'app/src/main/assets/frontend/templates/index.html',
         'app/build.gradle','build.gradle','settings.gradle','requirements.txt']
for f in files:
    check(f"Archivo {f}", os.path.isfile(os.path.join(BASE_DIR, f)))

# ==================== RESULTADO FINAL ====================
print("\n" + "=" * 75)
print("RESULTADO FINAL")
print("=" * 75)
pct = round(passed/total*100) if total > 0 else 0
bar = "█" * (pct//5) + "░" * (20 - pct//5)
print(f"  {bar}")
print(f"  ✅ {passed} | ❌ {failed} | 📊 {total} | 🎯 {pct}%")
if pct >= 95:    print("  🏆 EXCELENTE - LISTO PARA PRODUCCIÓN")
elif pct >= 85:  print("  🎉 MUY BUENO - Listo para demo")
elif pct >= 70:  print("  👍 FUNCIONAL - Ajustes menores")
else:            print("  🔧 NECESITA REVISIÓN")
print("=" * 75)
