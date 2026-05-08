#!/usr/bin/env python3
"""TPV Modularización v2 — Split script_5.js / script_8.js en módulos seguros."""
import os, re, subprocess, sys

BASE = os.path.join(os.path.expanduser("~"), "tpv-chaquopy")
JS_DIR = os.path.join(BASE, "app/src/main/assets/frontend/static/js")
TPL = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")
MDIR = os.path.join(JS_DIR, "tpv")

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def write(p, c):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)

FUNC_RE = re.compile(r'^\s+(async\s+)?function\s+(\w+)\s*\(')

def parse_segments(code):
    lines = code.split('\n')
    segs = []
    fstart, fname = 0, None
    for i, line in enumerate(lines):
        m = FUNC_RE.match(line)
        if m:
            segs.append((fname, fstart, i, lines[fstart:i]))
            fstart, fname = i, m.group(2)
    segs.append((fname, fstart, len(lines), lines[fstart:]))
    return segs

MAP5 = {
    "getSecretKey":"c","getDefaultState":"c","loadState":"c","saveState":"c",
    "saveStateServidor":"c","initializeUI":"c","refreshAllUI":"c",
    "handleTabChange":"c","showToast":"c","conf_setLanguage":"c","conf_setTheme":"c",
    "conf_handleExport":"g","conf_handleImport":"g",
    "cliente_":"q","catalogo_":"c","tpv_":"p",
    "ventas_":"v","registros_":"v","caja_":"v","inv_":"i",
    "gestion_":"g","realizar_exportacion_xlsx":"g",
    "exportar_":"g","mostrar_info_aprendizaje":"g","limpiar_memoria_aprendizaje":"g",
    "nom_":"n",
    "lic_getRemainingDays":"l","lic_getTimeUnitText":"l",
    "lic_activateLicense":"l","lic_checkLicense":"l",
    "activar_licencia":"l","eliminar_licencia":"l","mostrar_info_licencia":"l",
    "copyOverlayClientId":"l",
    "agregar_log":"u","actualizar_logs":"u","limpiar_logs":"u","copiarTexto":"u",
    "eliminar_":"v",
}
MAP8 = {
    "_auth_init":"a","auth_setModo":"a","auth_cliTab":"a",
    "auth_loginCliente":"a","auth_registrarCliente":"a",
    "_auth_mostrarAppCliente":"a","_auth_aplicarTabsCliente":"a",
    "auth_togglePw":"a","auth_login":"a","_loginErr":"a",
    "_auth_mostrarApp":"a","_auth_aplicarTabs":"a",
    "auth_biometric_check":"a","auth_biometric":"a",
    "_setup_vendedor":"ve","_vend_":"ve",
    "_setup_admin_inventario":"ad","_setup_supervisor_inventario":"ad",
    "_admin_":"ad",
    "cfg_":"ti",
    "priv_":"pr","g_previewImg":"pr","g_quitarImg":"pr",
    "auth_logout":"se","_iniciarPolling":"se",
    "_actualizarBadgePedidos":"se","_pollPedidos":"se","_toastPedido":"se",
    "auth_verNotificaciones":"us","auth_abrirUsuarios":"us",
    "auth_tab":"us","_cargarUsuarios":"us","auth_crearUsuario":"us",
    "auth_desactivar":"us","auth_cambiarPw":"us","_toast":"us",
    "lic_abrir":"la","lic_tab":"la","lic_actualizarDias":"la",
    "_lic_":"la","lic_crear":"la","lic_copiarClave":"la","lic_revocar":"la",
    "gestion_previewImagen":"la","gestion_limpiarImagen":"la",
    "gestion_mostrarPreviewExistente":"la",
    "_auth":"a","auth_":"a",
}
RESOLVE5 = {"c":"tpv_core","q":"tpv_qr","p":"tpv_pos","v":"tpv_ventas",
            "i":"tpv_inventario","g":"tpv_gestion","n":"tpv_nomenclator",
            "l":"tpv_licencias","u":"tpv_utils"}
RESOLVE8 = {"a":"tpv_auth","ve":"tpv_vendedor","ad":"tpv_admin",
            "ti":"tpv_tienda","pr":"tpv_priv","se":"tpv_session",
            "us":"tpv_users","la":"tpv_lic_admin"}

def assign(name, mp, res, fallback):
    if not name: return fallback
    for key, code in mp.items():
        if name == key or (key.endswith('_') and name.startswith(key)):
            return res[code]
    return fallback

HDR5 = {"tpv_core":"// tpv_core.js — Estado, IndexedDB, sincronización, config, UI init",
        "tpv_qr":"// tpv_qr.js — QR y etiquetas para clientes",
        "tpv_pos":"// tpv_pos.js — Catálogo, carrito, pagos, escáner",
        "tpv_ventas":"// tpv_ventas.js — Ventas, registros, cierres de caja",
        "tpv_inventario":"// tpv_inventario.js — Inventario y stock",
        "tpv_gestion":"// tpv_gestion.js — Productos, categorías, import/export",
        "tpv_nomenclator":"// tpv_nomenclator.js — Denominaciones de moneda",
        "tpv_licencias":"// tpv_licencias.js — Licencias y activación",
        "tpv_utils":"// tpv_utils.js — Helpers: logs, copiar, utilidades"}
HDR8 = {"tpv_auth":"// tpv_auth.js — Autenticación, roles, tabs, biometría",
        "tpv_vendedor":"// tpv_vendedor.js — Módulo vendedor",
        "tpv_admin":"// tpv_admin.js — Admin inventario, vendedores, gastos",
        "tpv_tienda":"// tpv_tienda.js — Configuración de tienda",
        "tpv_priv":"// tpv_priv.js — Privacidad y config personal",
        "tpv_session":"// tpv_session.js — Sesión, polling, logout",
        "tpv_users":"// tpv_users.js — Gestión de usuarios",
        "tpv_lic_admin":"// tpv_lic_admin.js — Administración de licencias"}

S5_ORDER = ["tpv_core","tpv_qr","tpv_pos","tpv_ventas","tpv_inventario",
            "tpv_gestion","tpv_nomenclator","tpv_licencias","tpv_utils"]
S8_ORDER = ["tpv_auth","tpv_vendedor","tpv_admin","tpv_tienda",
            "tpv_priv","tpv_session","tpv_users","tpv_lic_admin"]

def process(filepath, mp, res, fallback, order, hdrs, label):
    print(f"\n{'='*55}")
    print(f"  {label}: {os.path.basename(filepath)} ({len(read(filepath).splitlines())} líneas)")
    print(f"{'='*55}")

    write(filepath + ".bak", read(filepath))
    print(f"  Backup: {os.path.basename(filepath)}.bak")

    segs = parse_segments(read(filepath))
    mods = {}
    for name, start, end, code_lines in segs:
        m = assign(name, mp, res, fallback)
        mods.setdefault(m, []).extend(code_lines)

    ok = 0; total = 0; errors = []
    for mod in order:
        if mod not in mods:
            print(f"  - {mod}: vacío, saltando")
            continue
        content = hdrs.get(mod,"") + "\n" + '\n'.join(mods[mod]) + '\n'
        out = os.path.join(MDIR, f"{mod}.js")
        write(out, content)
        total += 1
        r = subprocess.run(["node","--check",out], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            lc = content.count('\n')
            print(f"  OK {mod}.js ({lc} líneas)")
            ok += 1
        else:
            err = r.stderr.strip().splitlines()[-1] if r.stderr else "unknown error"
            print(f"  ERROR {mod}.js — {err}")
            errors.append(mod)

    print(f"\n  Resultado: {ok}/{total} válidos")
    if errors:
        print(f"  Con errores: {', '.join(errors)}")
    return ok == total and total > 0

def update_index():
    html = read(TPL)
    old5 = '<script src="/static/js/script_5.js"></script>'
    old8 = '<script src="/static/js/script_8.js"></script>'
    if old5 not in html or old8 not in html:
        print("ERROR: No se encontraron las etiquetas <script> en index.html"); return False
    new5 = '\n'.join(f'    <script src="/static/js/tpv/{m}.js"></script>' for m in S5_ORDER)
    new8 = '\n'.join(f'    <script src="/static/js/tpv/{m}.js"></script>' for m in S8_ORDER)
    html = html.replace(old5, new5).replace(old8, new8)
    write(TPL, html)
    print("OK index.html actualizado con referencias a módulos")
    return True

# === MAIN ===
print("TPV Modularización v2.0")
print("=" * 55)

ok5 = process(os.path.join(JS_DIR,"script_5.js"), MAP5, RESOLVE5, "tpv_core",
              S5_ORDER, HDR5, "Script 5")
ok8 = process(os.path.join(JS_DIR,"script_8.js"), MAP8, RESOLVE8, "tpv_auth",
              S8_ORDER, HDR8, "Script 8")

if ok5 and ok8:
    print(f"\n{'='*55}")
    print("OK Todos los módulos validados correctamente")
    if update_index():
        print("\nDesplegar con:")
        print("  cd ~/tpv-chaquopy && git add -A && git commit -m 'feat: modularización script_5 + script_8' && git push")
        print("\nSi algo falla, restaurar:")
        print("  cp app/.../script_5.js.bak app/.../script_5.js")
        print("  cp app/.../script_8.js.bak app/.../script_8.js")
        print("  git checkout -- app/.../index.html")
    else:
        sys.exit(1)
else:
    print(f"\nERROR: Hay errores de sintaxis. index.html NO fue modificado.")
    print("Los archivos .bak conservan los originales.")
    sys.exit(1)
