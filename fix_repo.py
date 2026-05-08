#!/usr/bin/env python3
"""Fix completo: restaurar index.html + modularizar limpio."""
import os, subprocess, sys

BASE = os.path.expanduser("~/tpv-chaquopy")
T = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=BASE)
    return r.stdout.strip()

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)

print("PASO 1: Restaurar index.html desde commit funcional (9b92bde)...")
idx = run("git show 9b92bde:app/src/main/assets/frontend/templates/index.html")
write(T, idx)
print(f"  Restaurado: {len(idx.splitlines())} líneas")

print("\nPASO 2: Eliminar burbuja dark mode si existe...")
c = read(T)
import re
c2 = re.sub(r'\n<!-- .*?[Dd]ark [Mm]ode.*?-->.*?<!-- .*?[Dd]ark [Mm]ode.*?-->\n', '\n', c, flags=re.DOTALL)
if c2 != c:
    write(T, c2); print("  Burbuja eliminada")
else:
    print("  Burbuja no encontrada (ya limpia)")

print("\nPASO 3: Eliminar indicador offline...")
c = read(T)
c2 = re.sub(r'\s*<!-- Indicador de estado offline -->\s*<div id="offline-indicator"[^>]*>.*?</div>\s*', '\n', c2 if 'c2' in dir() else c, flags=re.DOTALL)
write(T, c2)
print("  Offline eliminado")

print("\nPASO 4: Reemplazar script_5.js por 9 módulos tpv/...")
c = read(T)
S5_MODS = [
    "tpv/tpv_core.js", "tpv/tpv_qr.js", "tpv/tpv_pos.js",
    "tpv/tpv_ventas.js", "tpv/tpv_inventario.js", "tpv/tpv_gestion.js",
    "tpv/tpv_nomenclator.js", "tpv/tpv_licencias.js", "tpv/tpv_utils.js"
]
old5 = '    <script src="/static/js/script_5.js"></script>'
new5 = '\n'.join(f'    <script src="/static/js/{m}"></script>' for m in S5_MODS)
if old5 in c:
    c = c.replace(old5, new5)
    print("  script_5.js → 9 módulos tpv/ OK")
else:
    print("  ERROR: no se encontró script_5.js")
    sys.exit(1)

print("\nPASO 5: Reemplazar script_8.js por 8 módulos tpv/...")
S8_MODS = [
    "tpv/tpv_auth.js", "tpv/tpv_vendedor.js", "tpv/tpv_admin.js",
    "tpv/tpv_tienda.js", "tpv/tpv_priv.js", "tpv/tpv_session.js",
    "tpv/tpv_users.js", "tpv/tpv_lic_admin.js"
]
old8 = '    <script src="/static/js/script_8.js"></script>'
new8 = '\n'.join(f'    <script src="/static/js/{m}"></script>' for m in S8_MODS)
if old8 in c:
    c = c.replace(old8, new8)
    print("  script_8.js → 8 módulos tpv/ OK")
else:
    print("  ERROR: no se encontró script_8.js")
    sys.exit(1)

write(T, c)

print("\nPASO 6: Validar todos los módulos con Node.js...")
JS = os.path.join(BASE, "app/src/main/assets/frontend/static/js")
all_ok = True
for m in S5_MODS + S8_MODS:
    path = os.path.join(JS, m)
    r = subprocess.run(["node","--check",path], capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        print(f"  OK {m}")
    else:
        print(f"  ERR {m}: {r.stderr.strip()[-80:]}")
        all_ok = False

print("\nPASO 7: Ocultar offline-indicator en CSS...")
css_path = os.path.join(BASE, "app/src/main/assets/frontend/static/css/style_5.css")
css = read(css_path)
if ".offline-indicator" in css and "display:none" not in css.split(".offline-indicator")[1].split("}")[0]:
    css = css.replace(
        ".offline-indicator {",
        ".offline-indicator { display: none !important; /* oculto */")
    write(css_path, css)
    print("  CSS offline ocultado")
else:
    print("  Ya oculto o no encontrado")

print("\n" + "="*50)
if all_ok:
    print("TODOS LOS MÓDULOS VALIDADOS")
    print(f"\nindex.html: {len(read(T).splitlines())} líneas")
    print("\nReferencias de scripts:")
    for line in read(T).splitlines():
        if '<script src="/static/js/' in line and 'lib' not in line:
            print(f"  {line.strip()}")
    print("\nPara desplegar:")
    print("  cd ~/tpv-chaquopy && git add -A && git commit -m 'fix: repo completo — 17 módulos + scripts + CSS restaurados' && git push")
else:
    print("HAY ERRORES — no desplegar")
    print("Para revertir:")
    print("  cd ~/tpv-chaquopy && git checkout 9b92bde -- app/src/main/assets/frontend/templates/index.html")
