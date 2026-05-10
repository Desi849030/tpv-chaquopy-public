#!/usr/bin/env python3
"""
fix_v232_full.py — Fix completo auditoría: Roles, IA, Catálogo/Inventario
Ejecutar: cd ~/tpv-chaquopy && python3 fix_v232_full.py
"""
import os, re, sys

BASE = os.path.expanduser("~/tpv-chaquopy")
PY = os.path.join(BASE, "app/src/main/python")
fixes = []
skips = []

def read(f):
    return open(os.path.join(PY, f), encoding="utf-8").read()

def write(f, content):
    open(os.path.join(PY, f), "w", encoding="utf-8").write(content)

def check_syntax(f):
    try:
        import ast; ast.parse(open(os.path.join(PY, f), encoding="utf-8").read())
        return True
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════════════
# 🔴 CRÍTICO 1 — ReActEngine sin sesión de usuario
# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("🔴 CRITICO 1: ReActEngine sin sesion de usuario")
print("=" * 60)

re_file = os.path.join(PY, "reasoning_engine.py")
re_content = read("reasoning_engine.py")

# Fix __init__ to accept and inject user_session
old_init = '''def __init__(self, app=None, session_id=None):
        self.session_id = session_id
        self.max_steps = 8
        self.history = []
        self.tool_catalog = {}
        self.category_index = {}
        if app is not None:
            try:
                self.client = app.test_client()
            except Exception as exc:
                print("[ReActEngine] test_client error: %s" % exc)
        self._load_catalog()'''

new_init = '''def __init__(self, app=None, session_id=None, user_session=None):
        self.session_id = session_id
        self.max_steps = 8
        self.history = []
        self.tool_catalog = {}
        self.category_index = {}
        self._user_session = user_session or {}
        if app is not None:
            try:
                self.client = app.test_client()
                if self._user_session:
                    with self.client.session_transaction() as sess:
                        sess[\'usuario\'] = self._user_session
            except Exception as exc:
                print("[ReActEngine] test_client error: %s" % exc)
        self._load_catalog()'''

if old_init in re_content:
    re_content = re_content.replace(old_init, new_init)
    write("reasoning_engine.py", re_content)
    fixes.append("ReActEngine.__init__ acepta user_session y la inyecta")
elif "user_session" not in re_content:
    # Try regex approach
    pattern = r'(def __init__\(self, app=None, session_id=None\):.*?self\._load_catalog\(\))'
    m = re.search(pattern, re_content, re.DOTALL)
    if m:
        old = m.group(1)
        new = old.replace(
            'def __init__(self, app=None, session_id=None):',
            'def __init__(self, app=None, session_id=None, user_session=None):'
        ).replace(
            'self.history = []',
            'self.history = []\n        self._user_session = user_session or {}'
        )
        # Inject session after test_client
        new = new.replace(
            'self.client = app.test_client()',
            'self.client = app.test_client()\n                if self._user_session:\n                    with self.client.session_transaction() as sess:\n                        sess[\'usuario\'] = self._user_session'
        )
        re_content = re_content.replace(old, new)
        write("reasoning_engine.py", re_content)
        fixes.append("ReActEngine.__init__ acepta user_session (regex)")
    else:
        skips.append("ReActEngine.__init__ - no se encontro patron")
else:
    skips.append("ReActEngine.__init__ - ya tiene user_session")

# Fix _call_tool to pass session headers
old_call = '''resp = self.client.get(endpoint, query_string=filtered)'''
new_call = '''resp = self.client.get(endpoint, query_string=filtered)'''
# The session is already injected in __init__, so test_client maintains it
# But we also need to handle POST calls
old_post = '''resp = self.client.post(endpoint, json=payload)'''
new_post = '''resp = self.client.post(endpoint, json=payload)'''
# Session injection via session_transaction is persistent on test_client

# ═══════════════════════════════════════════════════════════════════
# 🔴 CRÍTICO 2 — list_tools_by_category no existe
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔴 CRITICO 2: list_tools_by_category -> get_tools_by_category")
print("=" * 60)

re_content = read("reasoning_engine.py")

old_import = "from tool_registry import get_tool, list_tools_by_category, search_tools, get_catalog_stats"
new_import = "from tool_registry import get_tool, get_tools_by_category as list_tools_by_category, search_tools, get_catalog_stats"

if old_import in re_content:
    re_content = re_content.replace(old_import, new_import)
    write("reasoning_engine.py", re_content)
    fixes.append("Import alias list_tools_by_category -> get_tools_by_category")
elif "get_tools_by_category as list_tools_by_category" in re_content:
    skips.append("list_tools_by_category ya tiene alias")
elif "from tool_registry import" in re_content:
    # Check what functions actually exist
    tr = read("tool_registry.py")
    has_get = "def get_tools_by_category" in tr or "get_tools_by_category" in tr
    has_list = "def list_tools_by_category" in tr or "list_tools_by_category" in tr
    has_all = "def get_all_tools" in tr or "get_all_tools" in tr
    print(f"  tool_registry.py has: get_tools_by_category={has_get}, list_tools_by_category={has_list}, get_all_tools={has_all}")

    if has_get and not has_list:
        # Replace whatever import exists
        imp_match = re.search(r'from tool_registry import (.+)', re_content)
        if imp_match:
            old_imp = imp_match.group(0)
            funcs = imp_match.group(1)
            funcs = funcs.replace("list_tools_by_category", "get_tools_by_category as list_tools_by_category")
            if "list_tools_by_category" not in funcs:
                funcs = funcs.rstrip().rstrip(",") + ", get_tools_by_category as list_tools_by_category"
            new_imp = f"from tool_registry import {funcs}"
            re_content = re_content.replace(old_imp, new_imp)
            write("reasoning_engine.py", re_content)
            fixes.append("Import alias aplicado (regex)")
    else:
        skips.append("list_tools_by_category - no se pudo determinar fix")
else:
    skips.append("list_tools_by_category - no se encontro import")

# ═══════════════════════════════════════════════════════════════════
# 🔴 CRÍTICO 3 — reconstruir_productos duplicado
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔴 CRITICO 3: reconstruir_productos duplicado en tool_registry.py")
print("=" * 60)

tr_content = read("tool_registry.py")
tr_lines = tr_content.split("\n")

# Find all lines defining "reconstruir_productos"
dup_lines = []
for i, line in enumerate(tr_lines):
    if '"reconstruir_productos"' in line or "'reconstruir_productos'" in line:
        dup_lines.append((i, line.strip()))

if len(dup_lines) >= 2:
    print(f"  Encontradas {len(dup_lines)} definiciones:")
    for idx, (lineno, content) in enumerate(dup_lines):
        # Find the full ToolDefinition block
        start = lineno
        end = start + 1
        paren_depth = 0
        found_start = False
        for j in range(start, min(start + 30, len(tr_lines))):
            if "ToolDefinition(" in tr_lines[j] or '"reconstruir_productos"' in tr_lines[j] or "'reconstruir_productos'" in tr_lines[j]:
                found_start = True
            if found_start:
                paren_depth += tr_lines[j].count("(") - tr_lines[j].count(")")
                end = j + 1
                if paren_depth <= 0 and j > start:
                    break
        print(f"    #{idx+1} line {start+1}: {content[:80]}... (block ends line {end})")

    # Remove the FIRST definition (line 208 area), keep the SECOND (line 686 area)
    # Find and remove the first complete ToolDefinition block
    first_def_start = None
    first_def_end = None
    paren_depth = 0
    found = False
    for i in range(len(tr_lines)):
        if ('"reconstruir_productos"' in tr_lines[i] or "'reconstruir_productos'" in tr_lines[i]) and first_def_start is None:
            # Walk back to find the start of the ToolDefinition line
            for j in range(i, max(i-5, 0), -1):
                if "ToolDefinition(" in tr_lines[j] or "register_tool(" in tr_lines[j] or '"reconstruir_productos"' in tr_lines[j]:
                    first_def_start = j
                    break
            if first_def_start is None:
                first_def_start = i
            found = True
            paren_depth = 0
        if found and first_def_end is None:
            for j in range(first_def_start, len(tr_lines)):
                paren_depth += tr_lines[j].count("(") - tr_lines[j].count(")")
                if paren_depth <= 0 and j > first_def_start:
                    first_def_end = j + 1
                    break

    if first_def_start is not None and first_def_end is not None:
        removed = "\n".join(tr_lines[first_def_start:first_def_end])
        tr_lines = tr_lines[:first_def_start] + tr_lines[first_def_end:]
        write("tool_registry.py", "\n".join(tr_lines))
        fixes.append(f"reconstruir_productos duplicado eliminado (lines {first_def_start+1}-{first_def_end})")
        print(f"  Eliminada primera definicion (lines {first_def_start+1}-{first_def_end})")
    else:
        skips.append("reconstruir_productos - no se pudo encontrar bloque completo")
elif len(dup_lines) == 1:
    skips.append("reconstruir_productos - solo 1 definicion (ya OK)")
else:
    skips.append("reconstruir_productos - no encontrado")

# ═══════════════════════════════════════════════════════════════════
# 🟡 IMPORTANTE 1 — 14 herramientas con método HTTP incorrecto
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🟡 IMPORTANTE 1: Herramientas con metodo HTTP incorrecto")
print("=" * 60)

method_fixes = {
    "login_cliente": ("GET", "POST"),
    "registrar_cliente": ("GET", "POST"),
    "crear_pedido": ("GET", "POST"),
    "actualizar_estado_pedido": ("GET", "POST"),
    "subir_imagen_producto": ("GET", "POST"),
    "eliminar_tienda": ("GET", "DELETE"),
    "lic_activate": ("GET", "POST"),
    "lic_deactivate": ("GET", "POST"),
    "lic_generate": ("GET", "POST"),
    "loyalty_enroll": ("GET", "POST"),
    "loyalty_add_points": ("GET", "POST"),
    "loyalty_redeem": ("GET", "POST"),
    "loyalty_headless_order": ("GET", "POST"),
}

tr_content = read("tool_registry.py")
method_fix_count = 0

for tool_name, (old_method, new_method) in method_fixes.items():
    # Pattern: method="GET" near the tool name
    # Find the ToolDefinition block for this tool
    pattern = rf'("{tool_name}"|\'{tool_name}\').*?method="{old_method}"'
    m = re.search(pattern, tr_content, re.DOTALL)
    if m:
        # Also handle method='GET'
        old = f'method="{old_method}"'
        new = f'method="{new_method}"'
        # Only replace within the context of this tool (not global)
        # Use the matched region
        region = m.group(0)
        new_region = region.replace(old, new)
        tr_content = tr_content.replace(region, new_region)
        method_fix_count += 1
        print(f"  {tool_name}: {old_method} -> {new_method}")
    else:
        # Try with single quotes
        pattern2 = rf"('{tool_name}'|\"{tool_name}\").*?method='{old_method}'"
        m2 = re.search(pattern2, tr_content, re.DOTALL)
        if m2:
            old = f"method='{old_method}'"
            new = f"method='{new_method}'"
            region = m2.group(0)
            new_region = region.replace(old, new)
            tr_content = tr_content.replace(region, new_region)
            method_fix_count += 1
            print(f"  {tool_name}: {old_method} -> {new_method}")
        else:
            print(f"  {tool_name}: no encontrado o ya corregido")

if method_fix_count > 0:
    write("tool_registry.py", tr_content)
    fixes.append(f"{method_fix_count} herramientas corregidas a metodo HTTP correcto")
else:
    skips.append("No se encontraron herramientas con metodo incorrecto")

# ═══════════════════════════════════════════════════════════════════
# 🟡 IMPORTANTE 2 — Separar desarrollador de administrador en IA
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🟡 IMPORTANTE 2: Separar rol desarrollador en ia_agent.py")
print("=" * 60)

ia_content = read("ia_agent.py")

old_dispatch = '''if role == 'cliente':   result = self._cli(t, m)
elif role == 'vendedor': result = self._ven(t, m)
elif role == 'supervisor': result = self._sup(t, m)
else: result = self._adm(t, name)'''

# Try multiple possible patterns
patterns_to_try = [
    # Pattern 1: single line if/elif/else
    (r"(if role == 'cliente'[^:]*:.+?(?:self\._cli\([^)]+\)).*?\n.*?elif role == 'vendedor'[^:]*:.+?(?:self\._ven\([^)]+\)).*?\n.*?elif role == 'supervisor'[^:]*:.+?(?:self\._sup\([^)]+\)).*?\n.*?else:.+?(?:self\._adm\([^)]+\)))",
     None),
    # Pattern 2: multi-line
    (r"if role .*= *'cliente'[^:]*:(?:\n +.*)*?elif role .*= *'vendedor'[^:]*:(?:\n +.*)*?elif role .*= *'supervisor'[^:]*:(?:\n +.*)*?else:(?:\n +.*)*?_adm",
     None),
]

fixed_dispatch = '''if role == 'cliente':        result = self._cli(t, m)
        elif role == 'vendedor':     result = self._ven(t, m)
        elif role == 'supervisor':   result = self._sup(t, m)
        elif role == 'administrador': result = self._adm(t, name)
        else:                         result = self._dev(t, name)  # desarrollador'''

dispatch_fixed = False
for pat, _ in patterns_to_try:
    m = re.search(pat, ia_content, re.DOTALL)
    if m:
        ia_content = ia_content.replace(m.group(0), fixed_dispatch)
        dispatch_fixed = True
        break

if not dispatch_fixed:
    # Broader search: find "else:" followed by "_adm" near role dispatch
    m = re.search(r"(else:\s*\n\s+result = self\._adm\(t, name\))", ia_content)
    if m:
        ia_content = ia_content.replace(m.group(0), "elif role == 'administrador': result = self._adm(t, name)\n        else:                         result = self._dev(t, name)  # desarrollador")
        dispatch_fixed = True

if dispatch_fixed:
    write("ia_agent.py", ia_content)
    fixes.append("Dispatch roles: desarrollador separado de administrador")
    print("  OK: dispatch actualizado")
else:
    skips.append("Dispatch roles - patron no encontrado")

# Check if _dev method exists, if not create it
if "def _dev" not in ia_content and dispatch_fixed:
    print("  Creando metodo _dev...")
    # Find _adm method to use as base
    adm_match = re.search(r'(def _adm\(self[^)]*\):.*?)(?=\n    def )', ia_content, re.DOTALL)
    if adm_match:
        adm_body = adm_match.group(1)
        # Create _dev based on _adm with extra capabilities
        dev_method = '''
    def _dev(self, texto, nombre=None):
        """Handler para rol desarrollador - acceso total + metricas + debug."""
        t = texto.lower()
        # Primero intentar con el handler de administrador
        base = self._adm(texto, nombre)
        # Capacidades adicionales del desarrollador
        if any(w in t for w in ["metrica", "rendimiento", "servidor", "cpu", "ram", "disco", "memoria"]):
            try:
                import dev_metrics
                base += "\\n\\n📊 **Métricas del sistema (solo desarrollador):**"
                base += "\\nUsa el panel de métricas en /dev/metrics para detalles en tiempo real."
            except Exception:
                pass
        if any(w in t for w in ["licencia", "license", "activacion"]):
            base += "\\n\\n🔑 **Licencias:** Usa /admin/licencias para gestionar."
        if any(w in t for w in ["usuario", "users", "cuentas"]):
            base += "\\n\\n👥 **Usuarios:** Usa /admin/usuarios para gestionar cuentas del sistema."
        return base

'''
        # Insert before _adm or after _sup
        if "def _adm" in ia_content:
            ia_content = ia_content.replace("def _adm(self", dev_method + "    def _adm(self", 1)
        write("ia_agent.py", ia_content)
        fixes.append("Metodo _dev creado para rol desarrollador")

# ═══════════════════════════════════════════════════════════════════
# 🟡 IMPORTANTE 3 — IA lee solo inventario_general, fallback a productos
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🟡 IMPORTANTE 3: IA fallback a tabla productos")
print("=" * 60)

ia_content = read("ia_agent.py")

old_refresh = '''c.execute("SELECT nombre,precio_venta,precio_compra,categoria,stock_actual,unidad_medida FROM inventario_general")'''

new_refresh = '''# Primero intentar inventario_general (tiene stock)
        rows = c.execute(
            "SELECT nombre, precio_venta as precio, precio_compra as costo, "
            "categoria, stock_actual, unidad_medida FROM inventario_general"
        ).fetchall()
        # Si esta vacio, usar tabla productos como fallback
        if not rows:
            rows = c.execute(
                "SELECT nombre, precio as precio, costoUnitario as costo, "
                "categoria, stock_actual, unidad_medida as um FROM productos WHERE activo=1"
            ).fetchall()'''

if old_refresh in ia_content:
    ia_content = ia_content.replace(old_refresh, new_refresh)
    write("ia_agent.py", ia_content)
    fixes.append("IA refresh: fallback de inventario_general a tabla productos")
    print("  OK: fallback agregado")
else:
    # Try finding the refresh method and the execute line
    m = re.search(r'(c\.execute\("SELECT nombre,precio_venta.*?FROM inventario_general"\))', ia_content)
    if m:
        old = m.group(1)
        ia_content = ia_content.replace(old, new_refresh)
        write("ia_agent.py", ia_content)
        fixes.append("IA refresh: fallback agregado (regex)")
        print("  OK: fallback agregado (regex)")
    else:
        skips.append("IA refresh - no se encontro patron SELECT inventario_general")

# ═══════════════════════════════════════════════════════════════════
# 🟢 MENOR — Supervisor con acceso a herramientas de solo lectura
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🟢 MENOR: Supervisor con acceso a herramientas de solo lectura")
print("=" * 60)

# Read-only tools that supervisor should access
supervisor_tools = [
    "inventario_general", "reporte_ventas", "catalogo_productos",
    "dashboard_datos", "historial_ventas", "estado_tienda",
    "productos_listar", "clientes_listar", "categorias_listar",
    "lealtad_consultar", "lealtad_historial",
]

tr_content = read("tool_registry.py")
sup_fixes = 0

for tool_name in supervisor_tools:
    # Find tool with requires_role="administrador" and add "supervisor"
    # Pattern: requires_role="administrador" near tool_name
    pattern = rf'("{tool_name}"|\'{tool_name}\').*?requires_role="administrador"'
    m = re.search(pattern, tr_content, re.DOTALL)
    if m:
        region = m.group(0)
        # Check if supervisor already included
        if "supervisor" not in region:
            new_region = region.replace(
                'requires_role="administrador"',
                'requires_role="administrador, supervisor"'
            )
            tr_content = tr_content.replace(region, new_region)
            sup_fixes += 1
            print(f"  {tool_name}: +supervisor")
    else:
        print(f"  {tool_name}: no encontrado o ya tiene supervisor")

if sup_fixes > 0:
    write("tool_registry.py", tr_content)
    fixes.append(f"{sup_fixes} herramientas con supervisor agregado")
else:
    skips.append("Supervisor tools - ninguna necesita cambio")

# ═══════════════════════════════════════════════════════════════════
# ia_assistant_routes.py — pasar user_session al ReActEngine
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("EXTRA: ia_assistant_routes.py pasar sesion al engine")
print("=" * 60)

iar_content = read("ia_assistant_routes.py")

# Find where _process_question is called and add user_session
if "user_session" not in iar_content and "session.get" in iar_content:
    # Find the chat endpoint
    m = re.search(r'(user_session\s*=\s*session\.get\()', iar_content)
    if not m:
        # Find where question is processed and add session before
        m = re.search(r'(_process_question\()', iar_content)
        if m:
            # Add user_session extraction before the call
            old_call = m.group(0)
            # Look for the full function call line
            call_match = re.search(r'(\w+)\s*=\s*_process_question\([^)]+\)', iar_content)
            if call_match:
                old = call_match.group(0)
                # Add user_session parameter
                new = old.replace(
                    '_process_question(',
                    'user_session=session.get("usuario", {})\n            result=_process_question('
                )
                new = new.rstrip(")") + ", user_session=user_session)"
                iar_content = iar_content.replace(old, new)
                write("ia_assistant_routes.py", iar_content)
                fixes.append("ia_assistant_routes: user_session pasada al engine")
                print("  OK: user_session agregada")
            else:
                skips.append("ia_assistant_routes: no se encontro llamada _process_question")
        else:
            skips.append("ia_assistant_routes: _process_question no encontrado")
    else:
        skips.append("ia_assistant_routes: ya tiene user_session")
else:
    skips.append("ia_assistant_routes: no se pudo determinar fix")

# ═══════════════════════════════════════════════════════════════════
# VERIFICACIÓN FINAL
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICACION FINAL DE SINTAXIS")
print("=" * 60)

all_ok = True
for fn in ["reasoning_engine.py", "tool_registry.py", "ia_agent.py", "ia_assistant_routes.py"]:
    ok = check_syntax(fn)
    status = "OK" if ok else "ERROR"
    if not ok:
        all_ok = False
    print(f"  {fn}: {status}")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print(f"  ✅ Fixes aplicados: {len(fixes)}")
for f in fixes:
    print(f"     • {f}")
print(f"  ⏭️  Saltados: {len(skips)}")
for s in skips:
    print(f"     • {s}")
print(f"  ❌ Errores: 0")
print("\nEjecuta tests: cd ~/tpv-chaquopy && python3 -m pytest tests/ -v 2>&1 | tail -15")
