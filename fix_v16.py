#!/usr/bin/env python3
"""v16 - Fix: IA limits, import stock=0, confidence 90+, role pre-login"""
import os, re, sys

BASE = os.path.join(os.path.expanduser('~'), 'tpv-chaquopy')
JS5 = os.path.join(BASE, 'app/src/main/assets/frontend/static/js/script_5.js')
IA_UI = os.path.join(BASE, 'app/src/main/assets/frontend/static/lib/ia_assistant_ui.js')
AGENT = os.path.join(BASE, 'app/src/main/python/ia_agent.py')

# ============================================================
# FIX 1-3: script_5.js
# ============================================================
print("=== FIX script_5.js ===")
with open(JS5, 'r', encoding='utf-8', errors='ignore') as f:
    js = f.read()

original = js

# 1. Header detection: no requiere 'producto', acepta precio||cantidad
js = js.replace(
    "if (coincidencias >= 2 && colsEncontradas.producto !== undefined && colsEncontradas.precio !== undefined) {",
    "if (coincidencias >= 2 && (colsEncontradas.producto !== undefined || colsEncontradas.precio !== undefined || colsEncontradas.cantidad !== undefined)) {"
)

# 2. Confidence: 6 -> 4 para llegar a 90%+ con 4 headers
old_conf = "resultado.confianza = Math.min(coincidencias / 6, 1);"
if old_conf in js:
    js = js.replace(old_conf, "resultado.confianza = Math.min(coincidencias / 4, 1.0);")
    print("  OK confidence 6->4")
else:
    print("  WARN confidence pattern not found exact, trying alternatives...")
    js = re.sub(
        r'resultado\.confianza\s*=\s*Math\.min\(coincidencias\s*/\s*6,\s*1\)',
        'resultado.confianza = Math.min(coincidencias / 4, 1.0)',
        js
    )
    print("  OK confidence fixed via regex" if js != original else "  ERROR confidence not fixed")

# 2b. Map 'producto' -> 'nombre' in colsEncontrados (header detection)
old_map = "colsEncontradas[tipo] = j;"
new_map = "colsEncontradas[tipo === 'producto' ? 'nombre' : tipo] = j;"
if old_map in js:
    js = js.replace(old_map, new_map, 1)
    print("  OK header mapping producto->nombre")
else:
    print("  WARN header mapping pattern not found")

# 3. Stock override: preserve stock_actual from Excel import
js = js.replace(
    "stock_actual: stockMap[p.id] ?? 0",
    "stock_actual: p.stock_actual || stockMap[p.id] || 0"
)

if js != original:
    with open(JS5, 'w', encoding='utf-8') as f:
        f.write(js)
    print("  OK script_5.js written")
else:
    print("  SKIP no changes script_5.js")

# ============================================================
# FIX 4: ia_assistant_ui.js - Role pre-login
# ============================================================
print("\n=== FIX ia_assistant_ui.js ===")
with open(IA_UI, 'r', encoding='utf-8', errors='ignore') as f:
    ia = f.read()

old_role = "var currentRole = (typeof AUTH!=='undefined'&&AUTH.usuario&&AUTH.usuario.rol)?AUTH.usuario.rol:localStorage.getItem('tpv_rol')||'cliente';"
new_role = "var currentRole = (typeof AUTH!=='undefined'&&AUTH.usuario&&AUTH.usuario.rol)?AUTH.usuario.rol:'cliente';"
if old_role in ia:
    ia = ia.replace(old_role, new_role)
    with open(IA_UI, 'w', encoding='utf-8') as f:
        f.write(ia)
    print("  OK role pre-login: siempre cliente antes de login")
else:
    print("  WARN role pattern not found")

# ============================================================
# FIX 5: ia_agent.py - IA limits
# ============================================================
print("\n=== FIX ia_agent.py ===")
with open(AGENT, 'r', encoding='utf-8') as f:
    agent = f.read()

original = agent

# Default search limit 5 -> 10
agent = agent.replace("def search(cls, query, limit=5):", "def search(cls, query, limit=10):")

# P.search(t, 5) -> P.search(t, 10) in _sup and _adm
agent = re.sub(r'P\.search\(t,\s*5\)', 'P.search(t, 10)', agent)

# Display limits: prods[:5] -> prods[:10], prods[:6] -> prods[:10]
agent = agent.replace('prods[:5]', 'prods[:10]')
agent = agent.replace('prods[:6]', 'prods[:10]')

# Rows limits: rows[:10] -> rows[:20], rows[:15] -> rows[:20]
agent = agent.replace('rows[:10]', 'rows[:20]')
agent = agent.replace('rows[:15]', 'rows[:20]')

if agent != original:
    with open(AGENT, 'w', encoding='utf-8') as f:
        f.write(agent)
    print("  OK ia_agent.py limits increased")
else:
    print("  SKIP no changes ia_agent.py")

# ============================================================
# VALIDATE
# ============================================================
print("\n=== SYNTAX CHECK ===")
try:
    import py_compile
    py_compile.compile(AGENT, doraise=True)
    print("  OK ia_agent.py sin SyntaxError")
except SyntaxError as e:
    print("  ERROR: " + str(e))
    sys.exit(1)

# ============================================================
# CHECKS
# ============================================================
print("\n=== FINAL CHECKS ===")
with open(JS5, 'r', encoding='utf-8', errors='ignore') as f:
    js5 = f.read()

has_header_fix = "colsEncontradas.producto !== undefined || colsEncontradas.precio !== undefined || colsEncontradas.cantidad !== undefined" in js5
has_conf4 = "coincidencias / 4" in js5
has_name_map = "tipo === 'producto' ? 'nombre' : tipo" in js5
has_stock_fix = "p.stock_actual || stockMap[p.id] || 0" in js5

print("  " + ("OK" if has_header_fix else "ERROR") + " Header detection fix")
print("  " + ("OK" if has_conf4 else "ERROR") + " Confidence divisor 4")
print("  " + ("OK" if has_name_map else "ERROR") + " Header mapping producto->nombre")
print("  " + ("OK" if has_stock_fix else "ERROR") + " Stock override fix")

with open(IA_UI, 'r', encoding='utf-8', errors='ignore') as f:
    ia2 = f.read()
has_role_fix = "?AUTH.usuario.rol:'cliente'" in ia2
print("  " + ("OK" if has_role_fix else "ERROR") + " Role pre-login cliente")

with open(AGENT, 'r', encoding='utf-8') as f:
    ag = f.read()
print("  OK limit=10: " + str("limit=10" in ag))
print("  OK search(t,10): " + str(ag.count("P.search(t, 10)")) + " usos")
print("  OK prods[:10]: " + str(ag.count("prods[:10]")) + " usos")
print("  OK rows[:20]: " + str(ag.count("rows[:20]")) + " usos")

print("\n" + "="*55)
print("  v16 FIXES APPLIED")
print("="*55)
print("  1. Header detection: acepta precio||cantidad")
print("  2. Confidence: 4/4=100% (4+ headers detectados)")
print("  3. Header mapping: producto->nombre (consistente)")
print("  4. Stock: preserva stock_actual del Excel")
print("  5. Role pre-login: siempre cliente")
print("  6. IA limits: search 10, display 10/20")
print("="*55)
