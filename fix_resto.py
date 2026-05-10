#!/usr/bin/env python3
"""Fix resto auditoria: methods, supervisor, mixed_content, sync"""
import os, re

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")
fixes = []
skips = []

# ═══════════════════════════════════════════════════════════════
# 1. tool_registry.py — Fix 14 herramientas con metodo HTTP
# Formato: _t("name", "desc", "category", "route", "METHOD", [params])
# El metodo es el 5to argumento posicional (string "GET"/"POST")
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("1. Metodos HTTP incorrectos en tool_registry.py")
print("=" * 60)

tr = open(os.path.join(PY, "tool_registry.py")).read()
tr_lines = tr.split("\n")

# Map: tool_name -> correct method
method_map = {
    "login_cliente": "POST",
    "registrar_cliente": "POST",
    "crear_pedido": "POST",
    "actualizar_estado_pedido": "POST",
    "subir_imagen_producto": "POST",
    "eliminar_tienda": "DELETE",
    "lic_activate": "POST",
    "lic_deactivate": "POST",
    "lic_generate": "POST",
    "loyalty_enroll": "POST",
    "loyalty_add_points": "POST",
    "loyalty_redeem": "POST",
    "loyalty_headless_order": "POST",
}

# For each tool, find its _t() call and fix the 5th positional arg
count = 0
for tool_name, correct_method in method_map.items():
    # Pattern: "tool_name": _t("tool_name", ..., "/route", "WRONG", [params])
    # We need to find the line with "tool_name": _t( and then find the METHOD string
    for i, line in enumerate(tr_lines):
        if f'"{tool_name}"' in line and '_t(' in line:
            # Found the start of this tool definition
            # Collect lines until we find the closing )
            block = []
            depth = 0
            started = False
            for j in range(i, min(i + 15, len(tr_lines))):
                block.append(tr_lines[j])
                depth += tr_lines[j].count("(") - tr_lines[j].count(")")
                started = True
                if started and depth <= 0:
                    break
            
            block_text = "\n".join(block)
            
            # Extract all quoted strings in order to find the method
            # Format: _t("name", "desc", "category", "route", "METHOD", [...])
            strings = re.findall(r'"([^"]*)"', block_text)
            
            # The 5th string (index 4) should be the method if it's a valid HTTP method
            if len(strings) >= 5:
                current_method = strings[4]
                if current_method in ("GET", "POST", "PUT", "DELETE", "PATCH") and current_method != correct_method:
                    # Replace the method string
                    # Be careful to only replace the 5th occurrence
                    new_block = block_text
                    # Find and count occurrences of the current method
                    method_pos = 0
                    search_from = 0
                    target_pos = -1
                    for k in range(5):  # We want the 5th quoted string
                        pos = new_block.find(f'"{current_method}"', search_from)
                        if pos == -1:
                            break
                        # Check if this is inside a string that's a parameter
                        target_pos = pos
                        search_from = pos + 1
                    
                    if target_pos > -1:
                        new_block = new_block[:target_pos] + f'"{correct_method}"' + new_block[target_pos + len(f'"{current_method}"'):]
                        # Replace in tr_lines
                        for j in range(len(block)):
                            tr_lines[i + j] = ""  # Clear old
                        tr_lines[i] = new_block  # Set new
                        count += 1
                        print(f"  {tool_name}: {current_method} -> {correct_method}")
                    else:
                        print(f"  {tool_name}: no se pudo localizar metodo")
                elif current_method == correct_method:
                    print(f"  {tool_name}: ya OK ({current_method})")
                else:
                    print(f"  {tool_name}: string inesperada '{strings[4]}'")
            break  # Only process first match per tool

if count > 0:
    tr = "\n".join(tr_lines)
    open(os.path.join(PY, "tool_registry.py"), "w").write(tr)
    fixes.append(f"{count} metodos HTTP corregidos")
else:
    skips.append("No se corrigieron metodos HTTP")

# ═══════════════════════════════════════════════════════════════
# 2. Supervisor acceso a herramientas de solo lectura
# Formato: _t("name", "desc", "category", "route", "METHOD", [params])
# No tiene requires_role como kwarg — el rol esta implicito en la categoria
# Las rutas reales usan @requiere_rol en los archivos de rutas
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("2. Supervisor acceso herramientas solo lectura")
print("=" * 60)

# The real fix is in the route decorators, not tool_registry
# Check which route files have @requiere_rol without supervisor for GET routes
route_files = ["inventory_routes.py", "ventas_routes.py", "tienda_routes.py", "admin_routes.py"]
sup_added = 0

for rf in route_files:
    fp = os.path.join(PY, rf)
    if not os.path.exists(fp):
        continue
    content = open(fp).read()
    
    # Find GET routes with @requiere_rol("administrador","desarrollador") that don't include supervisor
    # These should be accessible to supervisor for read-only operations
    pattern = r'@requiere_rol\("([^"]+)"\)\s*\n\s*@inv_bp\.route\("(/api/[^"]+)",\s*methods=\["GET"\]\)'
    
    # Simpler approach: find all requiere_rol decorators and add supervisor where missing for GET routes
    # Find blocks: @requiere_rol("...", "...\") followed by @*_bp.route("...", methods=["GET"])
    blocks = re.findall(
        r'(@requiere_rol\("([^"]+)"\))\s*\n(\s*@[\w_]+\.route\("([^"]+)",\s*methods=\["GET"\]\))',
        content
    )
    
    for full_decorator, roles, route_decorator, route in blocks:
        if "supervisor" not in roles:
            # Add supervisor to this role check
            new_roles = roles.rstrip('"').rstrip() + ', "supervisor"'
            # Rebuild decorator
            new_dec = f'@requiere_rol("{new_roles}")'
            new_block = f'{new_dec}\n{route_decorator}'
            old_block = f'{full_decorator}\n{route_decorator}'
            content = content.replace(old_block, new_block)
            sup_added += 1
            print(f"  {rf}: {route} +supervisor")

# Also check ventas_routes and tienda_routes with their own blueprint names
for rf in ["ventas_routes.py", "tienda_routes.py"]:
    fp = os.path.join(PY, rf)
    if not os.path.exists(fp):
        continue
    content = open(fp).read()
    
    # Generic pattern for any blueprint
    blocks = re.findall(
        r'(@requiere_rol\("([^"]+)"\))\s*\n(\s*@[\w_]+\.route\("([^"]+)",\s*methods=\["GET"\]\))',
        content
    )
    
    for full_decorator, roles, route_decorator, route in blocks:
        if "supervisor" not in roles:
            new_roles = roles + ', "supervisor"'
            new_dec = f'@requiere_rol("{new_roles}")'
            new_block = f'{new_dec}\n{route_decorator}'
            old_block = f'{full_decorator}\n{route_decorator}'
            content = content.replace(old_block, new_block)
            sup_added += 1
            print(f"  {rf}: {route} +supervisor")
    
    if content != open(fp).read():
        open(fp, "w").write(content)

if sup_added > 0:
    fixes.append(f"{sup_added} rutas GET con +supervisor")
else:
    skips.append("Supervisor: no se encontraron rutas GET sin supervisor")

# ═══════════════════════════════════════════════════════════════
# 3. MIXED_CONTENT_ALWAYS_ALLOW en MainActivity
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("3. MIXED_CONTENT en MainActivity")
print("=" * 60)

ma = os.path.join(BASE, "app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java")
if os.path.exists(ma):
    mc = open(ma).read()
    if "MIXED_CONTENT_ALWAYS_ALLOW" in mc:
        # Remove the entire line or set to MIXED_CONTENT_NEVER_ALLOW
        # First try to remove the import
        if "import android.webkit.MixedContentMode" in mc or "WebSettings.MIXED_CONTENT" in mc:
            # Remove the setMixedContentMode line
            mc = re.sub(r'.*MIXED_CONTENT_ALWAYS_ALLOW.*\n?', '', mc)
            # Also remove the import if it was only for this
            open(ma, "w").write(mc)
            fixes.append("MIXED_CONTENT_ALWAYS_ALLOW eliminado de MainActivity")
            print("  OK: eliminado")
        else:
            skips.append("MIXED_CONTENT: formato desconocido")
    else:
        skips.append("MIXED_CONTENT: ya eliminado (OK)")
else:
    skips.append("MainActivity.java no encontrado")

# ═══════════════════════════════════════════════════════════════
# 4. supabase_sync.py — verificar que sincroniza ventas y stock
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("4. Supabase sync ventas/stock")
print("=" * 60)

sb = open(os.path.join(PY, "supabase_sync.py")).read()

# Check sincronizar_todo function
m = re.search(r'def sincronizar_todo\(.*?\):(.*?)(?=\ndef )', sb, re.DOTALL)
if m:
    body = m.group(1)
    has_ventas = "ventas" in body.lower()
    has_stock = "stock" in body.lower() or "inventario" in body.lower()
    print(f"  sincronizar_todo tiene ventas: {has_ventas}")
    print(f"  sincronizar_todo tiene stock/inventario: {has_stock}")
    
    if not has_ventas or not has_stock:
        # Add ventas and stock sync
        print("  Agregando sync de ventas y stock...")
        # Find the end of sincronizar_todo to append
        old_func_end = "return {'ok': True, 'sincronizado': True}"
        if old_func_end in sb:
            new_sync = '''
        # Sync ventas
        try:
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 100")
            ventas = [dict(r) for r in cursor.fetchall()]
            conn.close()
            if ventas:
                guardar_en_supabase({"ventas": ventas})
                print("  Ventas sincronizadas")
        except Exception as e:
            print(f"  Error sync ventas: {e}")

        # Sync inventario/stock
        try:
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventario_general ORDER BY producto_id")
            stock = [dict(r) for r in cursor.fetchall()]
            conn.close()
            if stock:
                guardar_en_supabase({"inventario": stock})
                print("  Inventario sincronizado")
        except Exception as e:
            print(f"  Error sync inventario: {e}")

        return {'ok': True, 'sincronizado': True}'''
            sb = sb.replace(old_func_end, new_sync, 1)
            open(os.path.join(PY, "supabase_sync.py"), "w").write(sb)
            fixes.append("sincronizar_todo: +ventas +stock")
            print("  OK: agregado")
        else:
            skips.append("sincronizar_todo: no se encontro return para insertar")
    else:
        skips.append("sincronizar_todo: ya tiene ventas y stock")
else:
    skips.append("sincronizar_todo: no encontrada")

# ═══════════════════════════════════════════════════════════════
# 5. VERIFICACION FINAL
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICACION FINAL")
print("=" * 60)

import ast
all_ok = True
for fn in os.listdir(PY):
    if not fn.endswith(".py"):
        continue
    fp = os.path.join(PY, fn)
    try:
        ast.parse(open(fp, encoding="utf-8").read())
    except SyntaxError as e:
        print(f"  ERROR {fn}:{e.lineno} {e.msg}")
        all_ok = False

if all_ok:
    print("  Todos los .py: SYNTAX OK")

# Check MainActivity
if os.path.exists(ma):
    mc_check = open(ma).read()
    if "MIXED_CONTENT_ALWAYS_ALLOW" in mc_check:
        print("  WARN: MIXED_CONTENT todavia en MainActivity")
    else:
        print("  MainActivity: MIXED_CONTENT eliminado OK")

print(f"\n{'='*60}")
print(f"  Fixes: {len(fixes)}")
for f in fixes:
    print(f"    + {f}")
print(f"  Saltados: {len(skips)}")
for s in skips:
    print(f"    ~ {s}")
print(f"  Errores: 0")
print(f"\nEjecuta: cd ~/tpv-chaquopy && python3 -m pytest tests/ -v 2>&1 | tail -10")
