#!/usr/bin/env python3
"""Renombrar script_N.js a nombres descriptivos y mover a tpv/."""
import os, subprocess, sys

BASE = os.path.expanduser("~/tpv-chaquopy")
JS = os.path.join(BASE, "app/src/main/assets/frontend/static/js")
T = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")
TPV = os.path.join(JS, "tpv")

RENAMES = {
    "script_1.js":  ("tpv_pwa_register.js",      "// tpv_pwa_register.js — Registro del Service Worker para PWA"),
    "script_2.js":  ("tpv_boot_loader.js",        "// tpv_boot_loader.js — Pantalla de carga/splash y progreso de inicio"),
    "script_3.js":  ("tpv_estado_shim.js",        "// tpv_estado_shim.js — Declaración inicial de tpvState (shim global)"),
    "script_4.js":  ("tpv_config_central.js",     "// tpv_config_central.js — Configuración centralizada TPV_CONFIG (claves, versiones)"),
    "script_6.js":  ("tpv_export_helpers.js",     "// tpv_export_helpers.js — Utilidades: esMovil, csvSafe, descargar, fechaEnRango, exportarTPVCompleto"),
    "script_7.js":  ("tpv_tienda_cliente.js",     "// tpv_tienda_cliente.js — Tienda: clientes, pedidos, auth cliente, productos por tienda"),
    "script_9.js":  ("tpv_dashboard_supabase.js", "// tpv_dashboard_supabase.js — Dashboard KPIs, gráficos, descuentos, config Supabase"),
    "script_10.js": ("tpv_traduccion_i18n.js",    "// tpv_traduccion_i18n.js — Google Translate bidireccional ES/EN con persistencia"),
    "script_11.js": ("tpv_debugger.js",           "// tpv_debugger.js — Panel de debug inteligente + monitor Supabase + diagnóstico"),
    "script_12.js": ("tpv_ui_enhancements.js",    "// tpv_ui_enhancements.js — Dark mode, animaciones KPIs, notificaciones stock, submenús"),
}

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)

changed = 0

print("PASO 1: Renombrar y mover a tpv/...")
for old, (new, header) in sorted(RENAMES.items()):
    old_path = os.path.join(JS, old)
    new_path = os.path.join(TPV, new)
    if not os.path.exists(old_path):
        print(f"  OMITIR {old} (no existe)"); continue

    content = read(old_path)

    # Reemplazar primera línea de comentario por header
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("//") or line.startswith("/*") or line.startswith("/**"):
            lines[i] = header
            break
    content = '\n'.join(lines)

    write(new_path, content)
    os.remove(old_path)
    print(f"  {old} → tpv/{new}")
    changed += 1

print(f"\n  {changed} archivos renombrados")

print("\nPASO 2: Actualizar index.html...")
with open(T, "r", encoding="utf-8") as f:
    html = f.read()

for old, (new, _) in sorted(RENAMES.items()):
    # Buscar referencia antigua
    patterns = [
        (f'"/static/js/{old}"', f'"/static/js/tpv/{new}"'),
        (f'"/static/js/{old}"', f'"/static/js/tpv/{new}"'),
    ]
    for old_ref, new_ref in patterns:
        if old_ref in html:
            html = html.replace(old_ref, new_ref)
            print(f"  {old} → tpv/{new}")
            break

with open(T, "w", encoding="utf-8") as f:
    f.write(html)

print("\nPASO 3: Validar con Node.js...")
all_ok = True
for _, (new, _) in sorted(RENAMES.items()):
    path = os.path.join(TPV, new)
    if not os.path.exists(path): continue
    r = subprocess.run(["node","--check",path], capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        print(f"  OK {new}")
    else:
        err = r.stderr.strip().splitlines()[-1] if r.stderr else "?"
        print(f"  ERR {new}: {err}")
        all_ok = False

# También validar los que ya estaban en tpv/
print("\nPASO 4: Re-validar módulos existentes en tpv/...")
for f in sorted(os.listdir(TPV)):
    if not f.endswith('.js'): continue
    if f in [r[1] for r in RENAMES.values()]: continue  # ya validados
    path = os.path.join(TPV, f)
    r = subprocess.run(["node","--check",path], capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        print(f"  OK {f}")
    else:
        err = r.stderr.strip().splitlines()[-1] if r.stderr else "?"
        print(f"  ERR {f}: {err}")
        all_ok = False

print("\n" + "="*55)
if all_ok:
    print(f"TODOS OK — {changed} scripts renombrados")
    print(f"\nContenido de tpv/:")
    for f in sorted(os.listdir(TPV)):
        if f.endswith('.js'):
            lc = len(read(os.path.join(TPV, f)).splitlines())
            print(f"  {f} ({lc} líneas)")
    total = sum(1 for f in os.listdir(TPV) if f.endswith('.js'))
    print(f"\n  Total: {total} archivos en tpv/")
    print(f"  Archivos sueltos en js/: {len([f for f in os.listdir(JS) if f.endswith('.js')])}")
    print("\nDesplegar:")
    print("  cd ~/tpv-chaquopy && git add -A && git commit -m 'refactor: renombrar todos los script_N.js + mover a tpv/' && git push")
else:
    print("ERRORES — no desplegar")
    sys.exit(1)
