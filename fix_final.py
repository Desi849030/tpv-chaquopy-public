#!/usr/bin/env python3
"""Fix definitivo: ia_agent.py + ia_assistant_routes.py"""
import os, re

PY = os.path.expanduser("~/tpv-chaquopy/app/src/main/python")

# ═══ 1. Fix ia_agent.py refresh method ═══
p1 = os.path.join(PY, "ia_agent.py")
t1 = open(p1).read()

# Find broken refresh block between "prods = []" and "cls.cache"
m = re.search(r'(prods = \[\]).*?(cls\.cache = prods)', t1, re.DOTALL)
if m:
    old_block = m.group(0)
    new_block = """prods = []
        rows = c.execute(
            "SELECT nombre, precio_venta as precio, precio_compra as costo, "
            "categoria, stock_actual, unidad_medida FROM inventario_general"
        ).fetchall()
        if not rows:
            rows = c.execute(
                "SELECT nombre, precio as precio, costoUnitario as costo, "
                "categoria, stock_actual, unidad_medida as um FROM productos WHERE activo=1"
            ).fetchall()
        for r in rows:
            prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})

        names = {p['n'].lower() for p in prods}

        cls.cache = prods"""
    t1 = t1.replace(old_block, new_block)
    open(p1, 'w').write(t1)
    print("1. ia_agent.py refresh: OK")
else:
    print("1. ia_agent.py refresh: patron no encontrado")

# ═══ 2. Fix ia_assistant_routes.py ═══
p2 = os.path.join(PY, "ia_assistant_routes.py")
t2 = open(p2).read()

# Find the broken section and replace entirely
m2 = re.search(
    r'(data\[\'_memory\'\]\s*=\s*mem_ctx).*?(result\s*=\s*_process_question\()',
    t2, re.DOTALL
)
if m2:
    old2 = m2.group(0)
    # Find the closing ) of _process_question call
    call_end = t2.find(')', t2.find('user_session=user_session', m2.end()))
    if call_end > -1:
        full_old = t2[m2.start():call_end+1]
        indent = '        '
        new2 = f"""data['_memory'] = mem_ctx

{indent}user_session = session.get("usuario", {{}})
{indent}result = _process_question(sid, q, role=role, user_name=user_name, user_session=user_session)"""
        t2 = t2.replace(full_old, new2)
        open(p2, 'w').write(t2)
        print("2. ia_assistant_routes.py: OK")
    else:
        print("2. ia_assistant_routes.py: no se encontro fin de llamada")
else:
    print("2. ia_assistant_routes.py: patron no encontrado")

# ═══ 3. Verify syntax ═══
import ast
for fn, fp in [("ia_agent.py", p1), ("ia_assistant_routes.py", p2)]:
    try:
        ast.parse(open(fp).read())
        print(f"3. {fn}: SYNTAX OK")
    except SyntaxError as e:
        print(f"3. {fn}: ERROR linea {e.lineno}: {e.msg}")

print("\nDONE - ejecuta: cd ~/tpv-chaquopy && python3 -m pytest tests/ -v 2>&1 | tail -10")
