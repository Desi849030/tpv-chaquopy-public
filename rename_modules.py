#!/usr/bin/env python3
"""Renombrar módulos tpv/ a nombres más robustos."""
import os, subprocess, sys

BASE = os.path.expanduser("~/tpv-chaquopy")
JS = os.path.join(BASE, "app/src/main/assets/frontend/static/js")
T = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")

RENAMES = {
    # --- De script_5.js ---
    "tpv_core.js":          "tpv_estado_sync.js",
    "tpv_qr.js":            "tpv_qr_etiquetas.js",
    "tpv_pos.js":           "tpv_punto_venta.js",
    "tpv_ventas.js":        "tpv_ventas_registros.js",
    "tpv_inventario.js":    "tpv_inventario_stock.js",
    "tpv_gestion.js":       "tpv_gestion_productos.js",
    "tpv_nomenclator.js":   "tpv_nomenclador.js",
    "tpv_licencias.js":     "tpv_licencias_activacion.js",
    "tpv_utils.js":         "tpv_utilidades.js",
    # --- De script_8.js ---
    "tpv_auth.js":          "tpv_autenticacion.js",
    "tpv_vendedor.js":      "tpv_vendedor_modulo.js",
    "tpv_admin.js":         "tpv_admin_inventario.js",
    "tpv_tienda.js":        "tpv_config_tienda.js",
    "tpv_priv.js":          "tpv_privacidad.js",
    "tpv_session.js":       "tpv_sesion_polling.js",
    "tpv_users.js":         "tpv_gestion_usuarios.js",
    "tpv_lic_admin.js":     "tpv_admin_licencias.js",
}

# Header actualizados
HEADERS = {
    "tpv_estado_sync.js":        "// tpv_estado_sync.js — Estado global, IndexedDB, sincronización servidor, config UI",
    "tpv_qr_etiquetas.js":       "// tpv_qr_etiquetas.js — Generación QR y etiquetas para clientes",
    "tpv_punto_venta.js":        "// tpv_punto_venta.js — Catálogo, carrito, pagos, escáner QR",
    "tpv_ventas_registros.js":   "// tpv_ventas_registros.js — Ventas del día, registros, cierres de caja",
    "tpv_inventario_stock.js":   "// tpv_inventario_stock.js — Inventario diario y control de stock",
    "tpv_gestion_productos.js":  "// tpv_gestion_productos.js — CRUD productos, categorías, import/export Excel",
    "tpv_nomenclador.js":        "// tpv_nomenclador.js — Denominaciones de moneda para caja",
    "tpv_licencias_activacion.js": "// tpv_licencias_activacion.js — Activación y validación de licencias",
    "tpv_utilidades.js":         "// tpv_utilidades.js — Helpers: logs, copiar texto, eliminaciones",
    "tpv_autenticacion.js":      "// tpv_autenticacion.js — Login, roles, tabs, biometría",
    "tpv_vendedor_modulo.js":    "// tpv_vendedor_modulo.js — Vista y funciones del rol vendedor",
    "tpv_admin_inventario.js":   "// tpv_admin_inventario.js — Admin: inventario, vendedores, gastos",
    "tpv_config_tienda.js":      "// tpv_config_tienda.js — Configuración de datos de la tienda",
    "tpv_privacidad.js":         "// tpv_privacidad.js — Configuración de privacidad y datos personales",
    "tpv_sesion_polling.js":     "// tpv_sesion_polling.js — Sesión, logout, polling de pedidos",
    "tpv_gestion_usuarios.js":   "// tpv_gestion_usuarios.js — CRUD de usuarios y roles",
    "tpv_admin_licencias.js":    "// tpv_admin_licencias.js — Administración y revocación de licencias",
}

tpv = os.path.join(JS, "tpv")
changed = 0

print("PASO 1: Renombrar archivos y actualizar headers...")
for old, new in sorted(RENAMES.items()):
    old_path = os.path.join(tpv, old)
    new_path = os.path.join(tpv, new)
    if not os.path.exists(old_path):
        print(f"  OMITIR {old} (no existe)"); continue
    
    with open(old_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Actualizar header (primera línea que empieza con //)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("//"):
            lines[i] = HEADERS.get(new, f"// {new}")
            break
    content = '\n'.join(lines)
    
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.remove(old_path)
    print(f"  {old} → {new}")
    changed += 1

print(f"\n  {changed} archivos renombrados")

print("\nPASO 2: Actualizar referencias en index.html...")
with open(T, "r", encoding="utf-8") as f:
    html = f.read()

for old, new in RENAMES.items():
    old_ref = f'"/static/js/tpv/{old}"'
    new_ref = f'"/static/js/tpv/{new}"'
    if old_ref in html:
        html = html.replace(old_ref, new_ref)
        print(f"  {old} → {new}")
    else:
        print(f"  (no ref) {old}")

with open(T, "w", encoding="utf-8") as f:
    f.write(html)

print("\nPASO 3: Validar con Node.js...")
all_ok = True
for new in sorted(RENAMES.values()):
    path = os.path.join(tpv, new)
    if not os.path.exists(path): continue
    r = subprocess.run(["node","--check",path], capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        print(f"  OK {new}")
    else:
        print(f"  ERR {new}: {r.stderr.strip()[-60:]}")
        all_ok = False

print("\n" + "="*55)
if all_ok:
    print(f"TODOS OK — {changed} módulos renombrados")
    print("\nReferencias finales:")
    for line in html.splitlines():
        if '/tpv/' in line and '<script' in line:
            name = line.split('/tpv/')[1].split('"')[0]
            print(f"  {name}")
    print("\nDesplegar:")
    print("  cd ~/tpv-chaquopy && git add -A && git commit -m 'refactor: renombrar módulos tpv a nombres descriptivos' && git push")
else:
    print("ERRORES — no desplegar")
