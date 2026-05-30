"""Tests de Sintaxis e Indentación para compilación APK"""
import os, sys, py_compile, glob

BASE = 'app/src/main/python'
passed = failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}")
        failed += 1

print("=" * 60)
print("🔍 VERIFICACIÓN DE SINTAXIS PARA APK")
print("=" * 60)

# 1. Archivo principal
print("\n📦 ARCHIVO PRINCIPAL")
check("app.py compila", py_compile.compile(f'{BASE}/app.py', doraise=True) is None)

# 2. Todos los .py en python/
print(f"\n🐍 MÓDULOS PYTHON ({BASE}/)")
python_files = []
for root, dirs, files in os.walk(BASE):
    # Excluir __pycache__
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            python_files.append(os.path.join(root, f))

total = len(python_files)
for f in sorted(python_files):
    try:
        py_compile.compile(f, doraise=True)
        check(f"  {f}", True)
    except py_compile.PyCompileError as e:
        check(f"  {f}", False)
        print(f"      Error: {e}")

# 3. Indentación consistente
print("\n📏 VERIFICACIÓN DE INDENTACIÓN")
indent_ok = True
for f in sorted(python_files)[:30]:  # Primeros 30 archivos
    try:
        with open(f, 'r') as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('#', '"', "'")):
                if '\t' in line:
                    indent_ok = False
                    print(f"  ⚠️ TAB en {f}:{i+1}")
                    break
    except:
        pass
check("Indentación sin TABs", indent_ok)

# 4. Sintaxis general
print("\n🔧 VERIFICACIÓN DE SINTAXIS GENERAL")
syntax_ok = True
for f in sorted(python_files):
    try:
        with open(f, 'r') as fh:
            compile(fh.read(), f, 'exec')
    except SyntaxError as e:
        syntax_ok = False
        check(f"  {f}", False)
        print(f"      Línea {e.lineno}: {e.msg}")
    except Exception as e:
        syntax_ok = False
        check(f"  {f}", False)
        print(f"      {e}")
check("Todos los archivos sin errores de sintaxis", syntax_ok)

# 5. Verificar imports circulares
print("\n🔄 VERIFICACIÓN DE IMPORTS")
try:
    sys.path.insert(0, BASE)
    import app
    check("Import de app.py exitoso", True)
except Exception as e:
    check("Import de app.py", False)
    print(f"      {e}")

# 6. Verificar start_server.py
print("\n🚀 VERIFICACIÓN DE ARRANQUE")
start = f'{BASE}/start_server.py'
if os.path.exists(start):
    try:
        py_compile.compile(start, doraise=True)
        check("start_server.py compila", True)
    except:
        check("start_server.py compila", False)
else:
    check("start_server.py existe", False)

# 7. Verificar requirements
print("\n📋 DEPENDENCIAS")
req = 'requirements.txt'
if os.path.exists(req):
    with open(req) as f:
        deps = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    check(f"requirements.txt ({len(deps)} dependencias)", len(deps) > 0)
else:
    check("requirements.txt existe", False)

# Resultado
print("\n" + "=" * 60)
total_tests = passed + failed
pct = round(passed/total_tests*100) if total_tests > 0 else 0
print(f"✅ {passed} | ❌ {failed} | 📊 {total_tests} | 🎯 {pct}%")
if pct == 100:
    print("🏆 LISTO PARA COMPILAR APK")
else:
    print("🔧 Corregir errores antes de compilar")
print("=" * 60)
