#!/usr/bin/env python3
"""Diagnostico: formato real de tool_registry + bugs restantes"""
import os, re

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")

# ═══ 1. tool_registry.py — formato real ═══
print("=== TOOL_REGISTRY FORMAT ===")
tr = open(os.path.join(PY, "tool_registry.py")).read()

# Show first 3 tool definitions
defs = re.findall(r'".*?":\s*\w+\(', tr)
print(f"Total definiciones encontradas: {len(defs)}")
print("Primeras 5:")
for d in defs[:5]:
    print(f"  {d[:80]}")

# Show how method is defined
method_patterns = re.findall(r'method\s*=\s*["\'](\w+)["\']', tr)
from collections import Counter
print(f"\nMetodos usados: {dict(Counter(method_patterns))}")

# Show 3 complete tool examples
examples = []
for m in re.finditer(r'("(\w+)":\s*\w+\(.*?\))', tr, re.DOTALL):
    examples.append(m.group(0)[:200])
    if len(examples) >= 3:
        break
print("\nEjemplos completos:")
for i, ex in enumerate(examples):
    print(f"\n  --- Ejemplo {i+1} ---")
    print(f"  {ex}")

# Check actual function names
funcs = re.findall(r'def (\w+)', tr)
print(f"\nFunciones definidas: {funcs[:20]}")

# Check for register_tool or ToolDefinition
has_register = "def register_tool" in tr or "register_tool(" in tr
has_td = "ToolDefinition" in tr
print(f"\nUsa register_tool: {has_register}")
print(f"Usa ToolDefinition: {has_td}")

# ═══ 2. start_server.py — loyalty_bp double register ═══
print("\n=== START_SERVER LOYALTY_BP ===")
ss = open(os.path.join(PY, "start_server.py")).read()
for i, line in enumerate(ss.split("\n"), 1):
    if "loyalty" in line.lower():
        print(f"  line {i}: {line.strip()}")

# ═══ 3. settings_routes.py — Supabase hardcoded ═══
print("\n=== SETTINGS ROUTES SUPABASE ===")
sr = open(os.path.join(PY, "settings_routes.py")).read()
for i, line in enumerate(sr.split("\n"), 1):
    if "supabase" in line.lower() or "anon" in line.lower() or "url" in line.lower():
        print(f"  line {i}: {line.strip()}")

# ═══ 4. supabase_sync.py — sync ventas/stock ═══
print("\n=== SUPABASE SYNC FUNCTIONS ===")
sb = open(os.path.join(PY, "supabase_sync.py")).read()
for m in re.finditer(r'def (\w+)', sb):
    fname = m.group(1)
    print(f"  {fname}")

# Check if ventas sync exists
has_ventas = "ventas" in sb and "sync" in sb
print(f"\nMenciona ventas: {has_ventas}")

# ═══ 5. Version check across files ═══
print("\n=== VERSION CHECK ===")
version_files = {
    "app.py": open(os.path.join(PY, "app.py")).read(),
    "start_server.py": open(os.path.join(PY, "start_server.py")).read(),
    "README.md": open(os.path.join(BASE, "README.md")).read() if os.path.exists(os.path.join(BASE, "README.md")) else "",
}
for fn, content in version_files.items():
    versions = re.findall(r'(\d+\.\d+\.\d+)', content)
    unique = list(set(versions))
    if unique:
        print(f"  {fn}: {unique[:5]}")

# ═══ 6. requirements.txt vs build.gradle Flask ═══
print("\n=== FLASK VERSION ===")
req_path = os.path.join(BASE, "requirements.txt")
if os.path.exists(req_path):
    for line in open(req_path):
        if "flask" in line.lower():
            print(f"  requirements.txt: {line.strip()}")
gradle_path = os.path.join(BASE, "app/build.gradle")
if os.path.exists(gradle_path):
    for line in open(gradle_path):
        if "flask" in line.lower() and "install" in line.lower():
            print(f"  build.gradle: {line.strip()}")

# ═══ 7. MIXED_CONTENT in MainActivity ═══
print("\n=== MIXED_CONTENT ===")
ma_path = os.path.join(BASE, "app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java")
if os.path.exists(ma_path):
    ma = open(ma_path).read()
    if "MIXED_CONTENT" in ma:
        print("  MIXED_CONTENT_ALWAYS_ALLOW: ENCONTRADO")
    else:
        print("  MIXED_CONTENT_ALWAYS_ALLOW: no encontrado (OK)")

# ═══ 8. /api/supabase/sync route ═══
print("\n=== /api/supabase/sync ROUTE ===")
for fn in os.listdir(PY):
    if fn.endswith(".py"):
        content = open(os.path.join(PY, fn)).read()
        if "supabase/sync" in content:
            print(f"  Encontrado en: {fn}")
            for i, line in enumerate(content.split("\n"), 1):
                if "supabase/sync" in line:
                    print(f"    line {i}: {line.strip()}")

print("\n=== FIN DIAGNOSTICO ===")
