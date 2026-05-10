#!/usr/bin/env python3
"""FIX COMPLETO - todos los errores de sintaxis e import"""
import os, re, sys

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")

def read(f):
    return open(os.path.join(PY, f)).read()

def write(f, content):
    open(os.path.join(PY, f), "w").write(content)

def has_syntax(f):
    try:
        import ast
        ast.parse(open(os.path.join(PY, f)).read())
        return None
    except SyntaxError as e:
        return f"{f}:{e.lineno} {e.msg}"

# ═══════════════════════════════════════
# 1. app.py - REMOVE decorators import (not needed, blueprints import themselves)
# ═══════════════════════════════════════
print("=== FIX app.py ===")
t = read("app.py")
# Remove ANY line importing from decorators
new_lines = []
for line in t.split("\n"):
    if "from decorators import" in line:
        print(f"  Removed: {line.strip()}")
        continue
    new_lines.append(line)
write("app.py", "\n".join(new_lines))
err = has_syntax("app.py")
print(f"  Syntax: {'OK' if not err else 'ERROR: ' + err}")

# ═══════════════════════════════════════
# 2. decorators.py - REMOVE self-import
# ═══════════════════════════════════════
print("\n=== FIX decorators.py ===")
t = read("decorators.py")
new_lines = []
for line in t.split("\n"):
    if "from decorators import" in line:
        print(f"  Removed: {line.strip()}")
        continue
    new_lines.append(line)
write("decorators.py", "\n".join(new_lines))
err = has_syntax("decorators.py")
print(f"  Syntax: {'OK' if not err else 'ERROR: ' + err}")

# ═══════════════════════════════════════
# 3. ia_assistant_routes.py - KEEP import (needs it)
# ═══════════════════════════════════════
t = read("ia_assistant_routes.py")
if "from decorators import requiere_login" in t:
    print(f"\n=== ia_assistant_routes.py ===")
    print(f"  OK: tiene import correcto")
    err = has_syntax("ia_assistant_routes.py")
    print(f"  Syntax: {'OK' if not err else 'ERROR: ' + err}")

# ═══════════════════════════════════════
# 4. Verify ALL .py files syntax
# ═══════════════════════════════════════
print("\n=== VERIFICANDO TODOS LOS ARCHIVOS ===")
all_ok = True
for fn in sorted(os.listdir(PY)):
    if not fn.endswith(".py"):
        continue
    err = has_syntax(fn)
    status = "OK" if not err else f"ERROR: {err}"
    if err:
        all_ok = False
    print(f"  {fn}: {status}")

# ═══════════════════════════════════════
# 5. Verify no circular imports
# ═══════════════════════════════════════
print("\n=== VERIFICANDO CIRCULAR IMPORTS ===")
for fn in sorted(os.listdir(PY)):
    if not fn.endswith(".py"):
        continue
    t = read(fn)
    name = fn.replace(".py", "")
    # Check if file imports itself
    if f"from {name} import" in t or f"import {name}" in t:
        print(f"  CIRCULAR: {fn} se importa a si misma!")
        all_ok = False

if all_ok:
    print("  Sin imports circulares")

# ═══════════════════════════════════════
# 6. Verify route files that use decorators HAVE the import
# ═══════════════════════════════════════
print("\n=== VERIFICANDO IMPORTS EN ROUTES ===")
for fn in sorted(os.listdir(PY)):
    if not fn.endswith("_routes.py") and fn != "ia_assistant_routes.py":
        continue
    t = read(fn)
    uses = any(x in t for x in ["requiere_login", "requiere_rol", "usuario_actual"])
    has_imp = "from decorators import" in t
    if uses and not has_imp:
        print(f"  MISSING: {fn} usa decorators pero no importa")
        all_ok = False
    elif uses and has_imp:
        print(f"  OK: {fn}")

print(f"\n{'='*50}")
if all_ok:
    print("TODOS OK - ejecuta tests")
else:
    print("HAY ERRORES - revisa arriba")
