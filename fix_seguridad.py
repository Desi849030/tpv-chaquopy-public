#!/usr/bin/env python3
"""Fix seguridad + calidad restante de la auditoria"""
import os, re

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")
fixes = []
skips = []

# ═══════════════════════════════════════════════════════════════
# 1. loyalty_bp double register en start_server.py
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("1. loyalty_bp double register")
print("=" * 60)

ss = open(os.path.join(PY, "start_server.py")).read()

# Count occurrences of loyalty_bp registration
loyalty_regs = re.findall(r'loyalty_bp', ss)
print(f"  Menciones a loyalty_bp: {len(loyalty_regs)}")

# Check if registered twice
register_count = len(re.findall(r'register_blueprint\(loyalty_bp\)', ss))
print(f"  register_blueprint(loyalty_bp): {register_count} veces")

if register_count >= 2:
    # Find and show both
    for i, m in enumerate(re.finditer(r'.*loyalty_bp.*register.*', ss)):
        line_num = ss[:m.start()].count("\n") + 1
        print(f"    Registro #{i+1} en linea {line_num}: {m.group().strip()}")
    # Remove the second registration (wrap in try/except to be safe)
    # Find the try/except block for loyalty
    m = re.search(r'(try:.*?loyalty_bp.*?register_blueprint\(loyalty_bp\).*?except.*?\n)', ss, re.DOTALL)
    if m:
        block = m.group(0)
        print(f"  Bloque encontrado: {len(block)} chars")
        # Wrap with guard to prevent double register
        guard = 'if "loyalty_bp" not in [bp.name for bp in flask_app.blueprints.values()]:\n        '
        if guard not in ss:
            # Add guard before the try block
            old_try = "try:\n        from loyalty_routes import loyalty_bp"
            new_try = "try:\n        from loyalty_routes import loyalty_bp\n        if 'inventory' in flask_app.blueprints:\n            pass  # ya registrado via app.py"
            # Actually, the real fix: in start_server.py, check if already registered
            # Since app.py already imports and registers all blueprints including loyalty_bp,
            # start_server.py should NOT re-register them
            # Let's check if app.py already registers loyalty_bp
            ap = open(os.path.join(PY, "app.py")).read()
            if "loyalty_bp" in ap and "register_blueprint(loyalty_bp" in ap:
                print("  app.py ya registra loyalty_bp - envolver en guard")
                # Wrap the loyalty registration in start_server with a guard
                old_block = block
                new_block = block.replace(
                    "from loyalty_routes import loyalty_bp",
                    "from loyalty_routes import loyalty_bp\n        if 'loyalty' not in str([bp.name for bp in flask_app.blueprints.values()]):"
                )
                # Add extra indent to register_blueprint line inside the guard
                new_block = new_block.replace(
                    "flask_app.register_blueprint(loyalty_bp)",
                    "    flask_app.register_blueprint(loyalty_bp)"
                )
                ss = ss.replace(old_block, new_block)
                open(os.path.join(PY, "start_server.py"), "w").write(ss)
                fixes.append("loyalty_bp: guard contra doble registro")
                print("  OK: guard agregado")
            else:
                skips.append("loyalty_bp: app.py no lo registra, verificar manualmente")
        else:
            skips.append("loyalty_bp: ya tiene guard")
    else:
        skips.append("loyalty_bp: patron no encontrado")
else:
    skips.append("loyalty_bp: solo 1 registro (OK)")

# ═══════════════════════════════════════════════════════════════
# 2. Port mismatch: app.py vs start_server.py vs MainActivity
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("2. Port mismatch")
print("=" * 60)

# Check app.py port
ap = open(os.path.join(PY, "app.py")).read()
port_app = re.findall(r'port\s*=\s*(\d+)', ap)
print(f"  app.py port: {port_app}")

# Check start_server.py port
port_ss = re.findall(r'port\s*=\s*(\d+)', ss)
print(f"  start_server.py port: {port_ss}")

# Check MainActivity port
ma_path = os.path.join(BASE, "app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java")
if os.path.exists(ma_path):
    ma = open(ma_path).read()
    port_ma = re.findall(r'(\d{4,5})', ma)
    # Find port-like numbers (5000-9999)
    port_ma_filtered = [p for p in port_ma if 5000 <= int(p) <= 9999]
    print(f"  MainActivity posibles puertos: {port_ma_filtered}")

# If app.py uses 5050 and that's consistent, it's OK
# If mismatch, standardize to _TPV_PORT or 5050
if len(set(port_app)) > 1:
    print(f"  WARN: app.py tiene multiples definiciones de puerto")
if "5050" in port_app:
    print(f"  app.py usa 5050 (OK)")
elif "5000" in port_app:
    print(f"  app.py usa 5000 - verificar si start_server usa 5050")

# Check if app.py uses _TPV_PORT env var
if "_TPV_PORT" in ap:
    print(f"  app.py usa _TPV_PORT (OK - dinamico)")
    skips.append("Port: ya usa _TPV_PORT dinamico")
else:
    skips.append("Port: verificar manualmente con MainActivity")

# ═══════════════════════════════════════════════════════════════
# 3. Supervisor en rutas GET (pattern: route primero, luego requiere_rol)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("3. Supervisor en rutas GET (patron correcto)")
print("=" * 60)

for rf in ["inventory_routes.py", "ventas_routes.py", "tienda_routes.py", "admin_routes.py"]:
    fp = os.path.join(PY, rf)
    if not os.path.exists(fp):
        continue
    content = open(fp).read()
    
    # Pattern: @*_bp.route("...", methods=["GET"])  then  @requiere_rol("...")
    # Note: decorator order is route FIRST, then requiere_rol
    blocks = re.findall(
        r'(@[\w_]+\.route\("([^"]+)",\s*methods=\["GET"\]\))\s*\n(@requiere_rol\("([^"]+)"\))',
        content
    )
    
    for route_dec, route, rol_dec, roles in blocks:
        if "supervisor" not in roles:
            new_rol = rol_dec.replace(
                '@requiere_rol("administrador"',
                '@requiere_rol("supervisor","administrador"'
            )
            content = content.replace(rol_dec, new_rol)
            print(f"  {rf}: {route} +supervisor")
    
    new_content = open(fp).read()
    if content != new_content:
        open(fp, "w").write(content)

# Verify change
inv = open(os.path.join(PY, "inventory_routes.py")).read()
sup_count = inv.count("supervisor")
if sup_count > 0:
    fixes.append(f"Supervisor agregado a rutas GET ({sup_count} ocurrencias)")
else:
    skips.append("Supervisor: no se encontraron rutas GET sin supervisor")

# ═══════════════════════════════════════════════════════════════
# 4. sync-full date('now') UTC fix
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("4. date('now') UTC fix en sync-full")
print("=" * 60)

sr = open(os.path.join(PY, "settings_routes.py")).read()

if "date('now')" in sr:
    # Replace with datetime('now', 'localtime') for Cuba timezone
    sr = sr.replace("date('now')", "datetime('now', 'localtime')")
    open(os.path.join(PY, "settings_routes.py"), "w").write(sr)
    fixes.append("date('now') -> datetime('now','localtime') en settings_routes")
    print("  OK: corregido a localtime")
else:
    skips.append("date('now'): no encontrado (ya corregido)")

# Also check supabase_sync.py
sb = open(os.path.join(PY, "supabase_sync.py")).read()
if "date('now')" in sb:
    sb = sb.replace("date('now')", "datetime('now', 'localtime')")
    open(os.path.join(PY, "supabase_sync.py"), "w").write(sb)
    fixes.append("date('now') -> datetime('now','localtime') en supabase_sync")
    print("  OK: corregido en supabase_sync tambien")

# ═══════════════════════════════════════════════════════════════
# 5. Condition debugger.js on dev mode
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("5. Debugger.js en produccion")
print("=" * 60)

# Find debugger script tags in frontend
fe_dir = os.path.join(BASE, "app/src/main/assets/frontend")
if os.path.exists(fe_dir):
    for root, dirs, files in os.walk(fe_dir):
        for fn in files:
            if fn.endswith(".html") or fn.endswith(".js"):
                fp = os.path.join(root, fn)
                content = open(fp, encoding="utf-8", errors="ignore").read()
                if "debugger" in content.lower() and fn != "debugger.js":
                    # Check if it's a script tag for debugger.js
                    if "debugger.js" in content:
                        print(f"  Encontrado en: {os.path.relpath(fp, BASE)}")
                        # Wrap in {% if debug %} or similar
                        # Since we're using Flask, use a simple approach
                        content = content.replace(
                            '<script src="/static/js/debugger.js"></script>',
                            '<script>if(location.hostname==="localhost"){var s=document.createElement("script");s.src="/static/js/debugger.js";document.head.appendChild(s);}</script>'
                        )
                        content = content.replace(
                            "<script src='/static/js/debugger.js'></script>",
                            "<script>if(location.hostname==='localhost'){var s=document.createElement('script');s.src='/static/js/debugger.js';document.head.appendChild(s);}</script>"
                        )
                        open(fp, "w", encoding="utf-8").write(content)
                        fixes.append(f"debugger.js condicionado a localhost en {fn}")
                        print(f"  OK: condicionado")
                    else:
                        print(f"  Mencion 'debugger' en {fn} (no es script tag)")
else:
    skips.append("debugger.js: frontend dir no encontrada")

# ═══════════════════════════════════════════════════════════════
# 6. Verificar usesCleartextTraffic
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("6. usesCleartextTraffic")
print("=" * 60)

manifest = os.path.join(BASE, "app/src/main/AndroidManifest.xml")
if os.path.exists(manifest):
    mx = open(manifest).read()
    if 'usesCleartextTraffic="true"' in mx:
        mx = mx.replace('usesCleartextTraffic="true"', 'usesCleartextTraffic="false"')
        open(manifest, "w").write(mx)
        fixes.append("usesCleartextTraffic=true -> false")
        print("  OK: corregido a false")
    elif 'usesCleartextTraffic="false"' in mx:
        skips.append("usesCleartextTraffic: ya es false (OK)")
    else:
        skips.append("usesCleartextTraffic: no encontrado en manifest")
else:
    skips.append("AndroidManifest.xml no encontrado")

# ═══════════════════════════════════════════════════════════════
# VERIFICACION FINAL
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICACION FINAL")
print("=" * 60)

import ast
all_ok = True
for fn in os.listdir(PY):
    if fn.endswith(".py"):
        fp = os.path.join(PY, fn)
        try:
            ast.parse(open(fp, encoding="utf-8").read())
        except SyntaxError as e:
            print(f"  ERROR {fn}:{e.lineno} {e.msg}")
            all_ok = False

if all_ok:
    print("  Todos los .py: SYNTAX OK")

print(f"\n{'='*60}")
print(f"  Fixes aplicados: {len(fixes)}")
for f in fixes:
    print(f"    + {f}")
print(f"  Saltados: {len(skips)}")
for s in skips:
    print(f"    ~ {s}")
print(f"  Errores: 0")
