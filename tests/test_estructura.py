"""Test de Estructura del Proyecto - Verifica que todo esté en su lugar"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name} {detail}")
        failed += 1

print("=" * 70)
print("🏗️  VERIFICACIÓN DE ESTRUCTURA DEL PROYECTO")
print("=" * 70)

# 1. Carpetas principales
print("\n📁 CARPETAS PRINCIPALES")
dirs = [
    'app/src/main/python',
    'app/src/main/python/ia',
    'app/src/main/python/routes',
    'app/src/main/python/tools',
    'app/src/main/python/security',
    'app/src/main/python/sync',
    'app/src/main/python/db',
    'app/src/main/python/models',
    'app/src/main/assets/frontend/templates',
    'app/src/main/assets/frontend/static/css',
    'app/src/main/assets/frontend/static/js',
    'app/src/main/java/com/universidad/tpv/tpvultrasmart',
    'app/src/main/res',
    'tests',
    'docs',
    '.github/workflows'
]
for d in dirs:
    check(f"Existe {d}", os.path.isdir(os.path.join(BASE, d)))

# 2. Archivos clave
print("\n📄 ARCHIVOS CLAVE")
files = [
    'app/src/main/python/app.py',
    'app/src/main/python/start_server.py',
    'app/src/main/python/database.py',
    'app/src/main/python/db_connection.py',
    'app/src/main/assets/frontend/templates/index.html',
    'app/src/main/assets/frontend/static/js/tpv_chat.js',
    'app/src/main/assets/frontend/static/js/tpv_licencias.js',
    'app/src/main/assets/frontend/static/js/tpv_ventas.js',
    'app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java',
    'app/build.gradle',
    'build.gradle',
    'settings.gradle',
    'requirements.txt',
    'README.md',
    'CHANGELOG.md',
    'LICENSE',
    '.gitignore',
    'start.sh' if os.path.exists(os.path.join(BASE, 'start.sh')) else 'app/src/main/python/start.sh'
]
for f in files:
    path = os.path.join(BASE, f)
    check(f"Existe {f}", os.path.isfile(path), f"({f})")

# 3. Estructura Android
print("\n📱 ESTRUCTURA ANDROID")
android_files = [
    'app/src/main/AndroidManifest.xml',
    'app/src/main/res/xml/network_security_config.xml',
    'app/build.gradle',
    'gradle/wrapper/gradle-wrapper.properties',
    'gradlew'
]
for f in android_files:
    check(f"Android: {f}", os.path.isfile(os.path.join(BASE, f)))

# 4. Módulos IA
print("\n🧠 MÓDULOS IA")
ia_modules = ['agent_master', 'nlp_engine', 'humanizer',  # agent_pro/agent_core unificados en agent_master (#6)
              'guardrails_v2', 'tool_system', 'react_core', 'catalog', 'skills',
              'role_guidance', 'session_context', 'memory_advanced', 'normalizer',
              'intent_engine', 'anti_slop', 'fuzzy_match', 'handlers']
for mod in ia_modules:
    check(f"IA: {mod}.py", os.path.isfile(os.path.join(BASE, f'app/src/main/python/ia/{mod}.py')))

# 5. Blueprints
print("\n📦 BLUEPRINTS")
bps = ['auth', 'products', 'sales', 'inventory', 'system', 'agent', 'metrics',
       'tienda_bp', 'ai_bp', 'ventas_bp', 'settings_bp', 'admin_bp', 'loyalty_bp',
       'assistant_bp', 'inventory_bp', 'ventas', 'settings']
for bp in bps:
    check(f"Blueprint: {bp}.py", os.path.isfile(os.path.join(BASE, f'app/src/main/python/routes/{bp}.py')))

# 6. Seguridad
print("\n🛡️ SEGURIDAD")
sec = ['security_het', 'security_pci', 'security_attestation', 'security_websocket',
       'security_routes', 'biometric_auth', 'payment_tokenizer']
for s in sec:
    check(f"Seguridad: {s}.py", os.path.isfile(os.path.join(BASE, f'app/src/main/python/{s}.py')))

# 7. Tablas BD
print("\n🗄️ TABLAS BD")
try:
    sys.path.insert(0, os.path.join(BASE, 'app/src/main/python'))
    from db_connection import obtener_conexion
    conn = obtener_conexion()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = [r[0] for r in c.fetchall()]
    conn.close()
    expected = ['productos', 'usuarios', 'historial_ventas', 'inventario_general',
                'cierres_caja', 'licencias', 'clientes', 'app_state']
    for t in expected:
        check(f"Tabla {t}", t in tablas)
    check(f"Total tablas: {len(tablas)}", len(tablas) >= 20)
except Exception as e:
    check("Conexión BD", False, str(e))

# 8. APIs principales
print("\n🔌 APIs PRINCIPALES")
import requests
apis = [
    ('GET', '/api/health'),
    ('GET', '/api/catalogo'),
    ('GET', '/api/metrics'),
    ('GET', '/api/ventas/totales'),
    ('GET', '/api/reportes/resumen'),
    ('GET', '/api/admin/privilegios'),
    ('GET', '/api/clientes'),
    ('GET', '/api/notificaciones'),
    ('GET', '/api/seguridad/check'),
    ('GET', '/api/tools/finanzas'),
]
for method, path in apis:
    try:
        r = requests.request(method, f'http://127.0.0.1:5000{path}', timeout=3)
        check(f"API {method} {path}", r.status_code == 200, f"({r.status_code})")
    except:
        check(f"API {method} {path}", False, "(sin conexión)")

# 9. Assets frontend
print("\n🎨 ASSETS FRONTEND")
css_count = len([f for f in os.listdir(os.path.join(BASE, 'app/src/main/assets/frontend/static/css')) if f.endswith('.css')])
js_count = len([f for f in os.listdir(os.path.join(BASE, 'app/src/main/assets/frontend/static/js')) if f.endswith('.js')])
check(f"CSS: {css_count} archivos", css_count >= 4)
check(f"JS: {js_count} archivos", js_count >= 8)

# Resultado
print("\n" + "=" * 70)
total = passed + failed
pct = round(passed/total*100) if total > 0 else 0
print(f"✅ {passed} | ❌ {failed} | 📊 {total} | 🎯 {pct}%")
if pct >= 95: print("🏆 ESTRUCTURA COMPLETA - LISTO PARA APK")
elif pct >= 80: print("👍 Buena estructura - revisar detalles")
else: print("🔧 Estructura incompleta")
print("=" * 70)
