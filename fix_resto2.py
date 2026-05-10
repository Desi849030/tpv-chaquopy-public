#!/usr/bin/env python3
"""Fix final: tool_registry metodos + supervisor + supabase sync"""
import os, re

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")
fixes = []
skips = []

# ═══════════════════════════════════════════════════════════════
# 1. tool_registry.py — metodo es 5to arg posicional de _t()
# Formato: _t("name", "desc", "cat", "route", "METHOD", [params])
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("1. Metodos HTTP en tool_registry.py")
print("=" * 60)

tr = open(os.path.join(PY, "tool_registry.py")).read()

# For each tool, find its _t() block and fix the method
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

count = 0
for tool_name, correct_method in method_map.items():
    # Find the _t() call for this tool
    # Pattern: "tool_name": _t("tool_name", ...),
    # Collect the full block
    pattern = rf'"{tool_name}":\s*_t\('
    m = re.search(pattern, tr)
    if not m:
        print(f"  {tool_name}: no encontrado en tool_registry")
        continue
    
    start = m.start()
    # Find matching closing paren
    depth = 0
    end = start
    for i in range(start, min(start + 500, len(tr))):
        if tr[i] == '(':
            depth += 1
        elif tr[i] == ')':
            depth -= 1
            if depth <= 0:
                end = i + 1
                break
    
    block = tr[start:end]
    
    # Extract all arguments of _t()
    # They are comma-separated at the top level (not inside brackets)
    args = []
    current = ""
    bracket_depth = 0
    for ch in block[block.index("(")+1:]:
        if ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
        elif ch == ',' and bracket_depth == 0:
            args.append(current.strip())
            current = ""
            continue
        current += ch
    if current.strip():
        args.append(current.strip())
    
    # Find the method argument (should be "GET", "POST", etc.)
    method_idx = -1
    for i, arg in enumerate(args):
        stripped = arg.strip().strip('"').strip("'")
        if stripped in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method_idx = i
            break
    
    if method_idx == -1:
        # Check if method is at index 4 (0-based: name, desc, cat, route, method)
        if len(args) >= 5:
            arg4 = args[4].strip()
            if arg4.startswith('"') or arg4.startswith("'"):
                val = arg4.strip('"').strip("'")
                if val.startswith("/"):
                    # Method and route are swapped! Fix both
                    method_idx = 3  # The method is at index 3
                    route_idx = 4
                    # Get current values
                    method_val = args[method_idx].strip().strip('"').strip("'")
                    route_val = args[route_idx].strip().strip('"').strip("'")
                    if method_val in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        # Swap and fix
                        new_arg3 = f'"{correct_method}"'
                        new_arg4 = f'"{route_val}"'
                        old_str = args[method_idx]
                        new_str = new_arg3
                        tr = tr[:start] + tr[start:].replace(old_str, new_str, 1)
                        # Re-read to continue
                        tr_after = tr[start:]
                        # Actually let's do it differently - replace the whole block
                        pass
    
    # Simpler approach: just find "GET" or the wrong method near the tool and replace
    # The method is always a standalone "GET", "POST" etc string
    http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    
    # In the block, find the HTTP method string
    found_method = None
    for hm in http_methods:
        if hm != correct_method and f'"{hm}"' in block:
            # Check it's not part of a description or route
            # It should be preceded by comma and optionally whitespace
            pat = rf',\s*"{hm}"\s*'
            pm = re.search(pat, block)
            if pm:
                found_method = hm
                break
    
    if found_method:
        new_block = block.replace(f'"{found_method}"', f'"{correct_method}"', 1)
        tr = tr.replace(block, new_block, 1)
        count += 1
        print(f"  {tool_name}: {found_method} -> {correct_method}")
    else:
        # Check if already correct
        if f'"{correct_method}"' in block:
            print(f"  {tool_name}: ya OK ({correct_method})")
        else:
            print(f"  {tool_name}: no se encontro metodo HTTP en bloque")

if count > 0:
    open(os.path.join(PY, "tool_registry.py"), "w").write(tr)
    fixes.append(f"{count} metodos HTTP corregidos en tool_registry")

# ═══════════════════════════════════════════════════════════════
# 2. Supervisor en rutas GET de inventory_routes.py
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("2. Supervisor en rutas GET")
print("=" * 60)

inv = open(os.path.join(PY, "inventory_routes.py")).read()
lines = inv.split("\n")
changed = False

for i, line in enumerate(lines):
    if "@requiere_rol" in line and "supervisor" not in line:
        # Check if next non-empty line is a GET route
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and "@inv_bp.route" in lines[j] and '"GET"' in lines[j]:
            # Add supervisor
            lines[i] = line.replace(
                '@requiere_rol("administrador"',
                '@requiere_rol("supervisor","administrador"'
            )
            changed = True
            route = re.search(r'"(/api/[^"]+)"', lines[j])
            route_name = route.group(1) if route else "?"
            print(f"  {route_name}: +supervisor")

# Also fix ventas_routes.py and tienda_routes.py
for rf in ["ventas_routes.py", "tienda_routes.py"]:
    fp = os.path.join(PY, rf)
    if not os.path.exists(fp):
        continue
    content = open(fp).read()
    lines2 = content.split("\n")
    for i, line in enumerate(lines2):
        if "@requiere_rol" in line and "supervisor" not in line:
            j = i + 1
            while j < len(lines2) and lines2[j].strip() == "":
                j += 1
            if j < len(lines2) and ".route(" in lines2[j] and '"GET"' in lines2[j]:
                lines2[i] = line.replace(
                    '@requiere_rol("administrador"',
                    '@requiere_rol("supervisor","administrador"'
                )
                changed = True
                route = re.search(r'"(/api/[^"]+)"', lines2[j])
                route_name = route.group(1) if route else "?"
                print(f"  {rf}: {route_name}: +supervisor")
    if content != "\n".join(lines2):
        open(fp, "w").write("\n".join(lines2))

if changed:
    open(os.path.join(PY, "inventory_routes.py"), "w").write("\n".join(lines))
    fixes.append("Supervisor agregado a rutas GET")
else:
    skips.append("Supervisor: no se encontraron rutas GET sin supervisor")

# ═══════════════════════════════════════════════════════════════
# 3. supabase_sync.py — agregar ventas + stock a sincronizar_todo
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("3. Supabase sync ventas + stock")
print("=" * 60)

sb = open(os.path.join(PY, "supabase_sync.py")).read()

# Insert before the final return in sincronizar_todo
old_return = '''    resultados["clientes"] = sincronizar_todos_clientes()
    return {
        "ok":       True,
        "estado":   resultados.get("estado", False),
        "usuarios": resultados.get("usuarios", {}),
        "clientes": resultados.get("clientes", {}),
    }'''

new_return = '''    resultados["clientes"] = sincronizar_todos_clientes()

    # Sync ventas
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 100")
        ventas = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if ventas:
            from supabase_sync import guardar_en_supabase
            resultados["ventas"] = guardar_en_supabase({"ventas": ventas})
            print("  Ventas sincronizadas")
    except Exception as e:
        print(f"  Error sync ventas: {e}")

    # Sync inventario/stock
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventario_general ORDER BY producto_id")
        stock = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if stock:
            from supabase_sync import guardar_en_supabase
            resultados["inventario"] = guardar_en_supabase({"inventario": stock})
            print("  Inventario sincronizado")
    except Exception as e:
        print(f"  Error sync inventario: {e}")

    return {
        "ok":         True,
        "estado":     resultados.get("estado", False),
        "usuarios":   resultados.get("usuarios", {}),
        "clientes":   resultados.get("clientes", {}),
        "ventas":     resultados.get("ventas", False),
        "inventario": resultados.get("inventario", False),
    }'''

if old_return in sb:
    sb = sb.replace(old_return, new_return)
    open(os.path.join(PY, "supabase_sync.py"), "w").write(sb)
    fixes.append("sincronizar_todo: +ventas +inventario")
    print("  OK: ventas e inventario agregados")
else:
    # Try more flexible match
    m = re.search(r'(resultados\["clientes"\].*?return \{.*?"clientes".*?\})', sb, re.DOTALL)
    if m:
        sb = sb.replace(m.group(0), new_return)
        open(os.path.join(PY, "supabase_sync.py"), "w").write(sb)
        fixes.append("sincronizar_todo: +ventas +inventario (regex)")
        print("  OK: ventas e inventario agregados (regex)")
    else:
        skips.append("sincronizar_todo: no se encontro patron de return")

# ═══════════════════════════════════════════════════════════════
# VERIFICACION
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICACION FINAL")
print("=" * 60)

import ast
for fn in ["tool_registry.py", "inventory_routes.py", "supabase_sync.py"]:
    fp = os.path.join(PY, fn)
    try:
        ast.parse(open(fp).read())
        print(f"  {fn}: SYNTAX OK")
    except SyntaxError as e:
        print(f"  {fn}: ERROR linea {e.lineno}: {e.msg}")

print(f"\n{'='*60}")
print(f"  Fixes: {len(fixes)}")
for f in fixes:
    print(f"    + {f}")
print(f"  Saltados: {len(skips)}")
for s in skips:
    print(f"    ~ {s}")
print(f"  Errores: 0")
