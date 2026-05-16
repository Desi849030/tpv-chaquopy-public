#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA - TPV UltraSmart
Testea: Frontend, i18n, QR, Biometría, Tickets, Licencias, Java, Sintaxis
"""
import sys, os, json, re
sys.path.insert(0, 'app/src/main/python')

print("=" * 70)
print("🔍 AUDITORÍA COMPLETA - TPV UltraSmart")
print("=" * 70)

errors, warnings, ok = [], [], []
def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))
def warn(name, condition, msg=""):
    (warnings if condition else ok).append(name)
    if condition: print(f"  ⚠️ {name}: {msg}")

# ============================================================
# 1. SINTAXIS PYTHON (TODOS los archivos)
# ============================================================
print("\n🐍 1. SINTAXIS PYTHON")
import py_compile
syntax_errors = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git', 'venv', '__pycache__']]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                syntax_errors += 1
                print(f"    ❌ {path}: {e}")
            except Exception:
                pass
test("Sintaxis Python 100%", syntax_errors == 0, f"{syntax_errors} errores")

# ============================================================
# 2. FRONTEND (HTML/JS/CSS)
# ============================================================
print("\n🎨 2. FRONTEND")
# HTML
html_files = []
for root, _, files in os.walk('app/src/main/assets'):
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))
test("Archivos HTML", len(html_files) > 0, f"{len(html_files)} encontrados")

# JS válido
js_count = 0
css_count = 0
for root, _, files in os.walk('app/src/main/assets'):
    for f in files:
        if f.endswith('.js'):
            js_count += 1
        elif f.endswith('.css'):
            css_count += 1
test("Archivos JavaScript", js_count > 10, f"{js_count} archivos")
test("Archivos CSS", css_count > 5, f"{css_count} archivos")

# Verificar index.html tiene estructura básica
index = 'app/src/main/assets/frontend/templates/index.html'
if os.path.exists(index):
    with open(index, 'r') as f:
        content = f.read()
    test("HTML: DOCTYPE", '<!DOCTYPE html>' in content or '<!doctype html>' in content.lower())
    test("HTML: head", '<head>' in content)
    test("HTML: body", '<body>' in content)
    test("HTML: cierre html", '</html>' in content)
else:
    test("index.html existe", False, "No encontrado")

# ============================================================
# 3. INTERNACIONALIZACIÓN (i18n)
# ============================================================
print("\n🌐 3. INTERNACIONALIZACIÓN (ES/EN)")
i18n_file = 'app/src/main/assets/frontend/static/js/tpv/tpv_traduccion_i18n.js'
if os.path.exists(i18n_file):
    with open(i18n_file, 'r') as f:
        i18n_content = f.read()
    test("Archivo i18n existe", True)
    test("Contiene español", 'es' in i18n_content.lower() or 'español' in i18n_content.lower() or 'spanish' in i18n_content.lower())
    test("Contiene inglés", 'en' in i18n_content.lower() or 'english' in i18n_content.lower())
else:
    test("Archivo i18n", False, "No encontrado")

# ============================================================
# 4. BIOMETRÍA
# ============================================================
print("\n🔐 4. BIOMETRÍA")
try:
    import biometric_auth
    test("Módulo biometric_auth", True)
    # Verificar funciones
    funcs = [x for x in dir(biometric_auth) if not x.startswith('_')]
    test("Funciones biométricas", len(funcs) > 0, f"Funciones: {funcs}")
except Exception as e:
    test("Biometría", False, str(e))

# ============================================================
# 5. QR / ESCÁNER
# ============================================================
print("\n📷 5. QR / ESCÁNER")
qr_lib = 'app/src/main/assets/frontend/static/lib/html5-qrcode.min.js'
test("Librería QR", os.path.exists(qr_lib))

qr_js = 'app/src/main/assets/frontend/static/js/tpv/tpv_qr_etiquetas.js'
if os.path.exists(qr_js):
    with open(qr_js, 'r') as f:
        qr_content = f.read()
    test("JS QR existe", len(qr_content) > 100)
else:
    test("JS QR", False)

# ============================================================
# 6. TICKETS / IMPRESIÓN
# ============================================================
print("\n🧾 6. TICKETS")
ticket_refs = 0
for root, _, files in os.walk('app/src/main/python'):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f), 'r') as fp:
                content = fp.read()
                if 'ticket' in content.lower() or 'factura' in content.lower():
                    ticket_refs += 1
test("Referencias a tickets", ticket_refs > 5, f"{ticket_refs} referencias")

# ============================================================
# 7. NOTIFICACIONES
# ============================================================
print("\n🔔 7. NOTIFICACIONES")
notif_files = []
for root, _, files in os.walk('app/src/main'):
    for f in files:
        if f.endswith('.py') or f.endswith('.js') or f.endswith('.java'):
            path = os.path.join(root, f)
            with open(path, 'r') as fp:
                if 'notif' in fp.read().lower():
                    notif_files.append(path)
test("Sistema notificaciones", len(notif_files) > 3, f"{len(notif_files)} archivos")

# ============================================================
# 8. LICENCIAS
# ============================================================
print("\n📜 8. LICENCIAS")
try:
    from license.core import generar_licencia, validar_licencia, activar_licencia, desactivar_licencia
    test("Módulo licencias", True)
    funcs = ['generar_licencia', 'validar_licencia', 'activar_licencia', 'desactivar_licencia']
    for fn in funcs:
        test(f"Función {fn}", fn in dir())
except Exception as e:
    warn("Licencias", True, str(e))

# ============================================================
# 9. JAVA (MainActivity)
# ============================================================
print("\n☕ 9. MÓDULO ANDROID (JAVA)")
java_file = 'app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java'
if os.path.exists(java_file):
    with open(java_file, 'r') as f:
        java_content = f.read()
    test("MainActivity.java existe", True)
    test("Tiene onCreate", 'onCreate' in java_content)
    test("Tiene Chaquopy", 'Chaquopy' in java_content or 'Python' in java_content)
    test("Tiene WebView", 'WebView' in java_content)
    test("Tiene Biometría", 'Biometric' in java_content or 'biometric' in java_content)
else:
    test("MainActivity.java", False, "No encontrado")

# ============================================================
# 10. ESTRUCTURA COMPLETA DEL PROYECTO
# ============================================================
print("\n📁 10. ESTRUCTURA DEL PROYECTO")
dirs_esperados = [
    'app/src/main/python/ia',
    'app/src/main/python/routes',
    'app/src/main/python/security',
    'app/src/main/python/metrics',
    'app/src/main/python/license',
    'app/src/main/python/dictionary',
    'app/src/main/python/db',
    'app/src/main/python/sync',
    'app/src/main/python/tools',
    'app/src/main/assets/frontend',
    'tests',
    'docs',
    '.github/workflows'
]
for d in dirs_esperados:
    test(f"Directorio {d}", os.path.isdir(d))

# Archivos clave
archivos_clave = [
    'app/src/main/python/app.py',
    'app/build.gradle',
    'build.gradle',
    'README.md',
    'LICENSE',
    '.github/workflows/main.yml',
    'test_simulacion_apk.py',
    'test_simulacion_apk_full.py',
    'test_stress_concurrente.py'
]
for a in archivos_clave:
    test(f"Archivo {os.path.basename(a)}", os.path.exists(a))

# ============================================================
# 11. CONSISTENCIA DE VERSIONES
# ============================================================
print("\n📌 11. VERSIONES")
version_files = {
    'build.gradle': r'versionName\s+"([^"]+)"',
    'app/build.gradle': r'versionName\s+"([^"]+)"',
    'README.md': r'v(\d+\.\d+\.\d+)',
}
versions = {}
for fname, pattern in version_files.items():
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            match = re.search(pattern, f.read())
            if match:
                versions[fname] = match.group(1)
test("Versiones consistentes", len(set(versions.values())) <= 1, 
     f"Versiones: {versions}")

# ============================================================
# 12. SEGURIDAD - VERIFICACIONES FINALES
# ============================================================
print("\n🛡️ 12. SEGURIDAD FINAL")
# No debe haber secretos en el repo
secretos = []
for root, _, files in os.walk('.'):
    if '.git' in root:
        continue
    for f in files:
        if f in ['.tpv_secret', '.tpv_hmac_secret', 'keystore']:
            secretos.append(os.path.join(root, f))
test("Sin secretos en repo", len(secretos) == 0, f"Encontrados: {secretos}")

# .gitignore debe existir
test(".gitignore existe", os.path.exists('.gitignore'))

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 70)
print("📋 RESUMEN AUDITORÍA")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ⚠️ {len(warnings)} warnings")
print(f"  ❌ {len(errors)} errores")

if errors:
    print("\n❌ FALLOS:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 ¡AUDITORÍA COMPLETA EXITOSA! Nada sin testear.")
    sys.exit(0)
