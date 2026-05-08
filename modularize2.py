#!/usr/bin/env python3
"""TPV Modularización v2.1 — Fix: funciones en columna 0 (script_8)."""
import os, re, subprocess, sys

BASE = os.path.join(os.path.expanduser("~"), "tpv-chaquopy")
JS_DIR = os.path.join(BASE, "app/src/main/assets/frontend/static/js")
TPL = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")
MDIR = os.path.join(JS_DIR, "tpv")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)

FUNC_RE = re.compile(r'^\s*(async\s+)?function\s+(\w+)\s*\(')

def parse_segments(code):
    lines = code.split('\n')
    segs = []; fstart = 0; fname = None
    for i, line in enumerate(lines):
        m = FUNC_RE.match(line)
        if m:
            segs.append((fname, fstart, i, lines[fstart:i]))
            fstart, fname = i, m.group(2)
    segs.append((fname, fstart, len(lines), lines[fstart:]))
    return segs

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
RESOLVE8 = {"a":"tpv_auth","ve":"tpv_vendedor","ad":"tpv_admin",
            "ti":"tpv_tienda","pr":"tpv_priv","se":"tpv_session",
            "us":"tpv_users","la":"tpv_lic_admin"}

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
RESOLVE5 = {"c":"tpv_core","q":"tpv_qr","p":"tpv_pos","v":"tpv_ventas",
            "i":"tpv_inventario","g":"tpv_gestion","n":"tpv_nomenclator",
            "l":"tpv_licencias","u":"tpv_utils"}

def assign(name, mp, res, fallback):
    if not name: return fallback
    for key, code in mp.items():
        if name == key or (key.endswith('_') and name.startswith(key)):
            return res[code]
    return fallback

HDR5 = {"tpv_core":"// tpv_core.js","tpv_qr":"// tpv_qr.js",
        "tpv_pos":"// tpv_pos.js","tpv_ventas":"// tpv_ventas.js",
        "tpv_inventario":"// tpv_inventario.js","tpv_gestion":"// tpv_gestion.js",
        "tpv_nomenclator":"// tpv_nomenclator.js","tpv_licencias":"// tpv_licencias.js",
        "tpv_utils":"// tpv_utils.js"}
HDR8 = {"tpv_auth":"// tpv_auth.js","tpv_vendedor":"// tpv_vendedor.js",
        "tpv_admin":"// tpv_admin.js","tpv_tienda":"// tpv_tienda.js",
        "tpv_priv":"// tpv_priv.js","tpv_session":"// tpv_session.js",
        "tpv_users":"// tpv_users.js","tpv_lic_admin":"// tpv_lic_admin.js"}

S5_ORDER = ["tpv_core","tpv_qr","tpv_pos","tpv_ventas","tpv_inventario",
            "tpv_gestion","tpv_nomenclator","tpv_licencias","tpv_utils"]
S8_ORDER = ["tpv_auth","tpv_vendedor","tpv_admin","tpv_tienda",
            "tpv_priv","tpv_session","tpv_users","tpv_lic_admin"]

def process(filepath, mp, res, fallback, order, hdrs, label):
    print(f"\n{'='*55}")
    code = read(filepath)
    nlines = len(code.splitlines())
    print(f"  {label}: {os.path.basename(filepath)} ({nlines} líneas)")
    print(f"{'='*55}")
    write(filepath + ".bak", code)

    segs = parse_segments(code)
    fnames = [s[0] for s in segs if s[0]]
    print(f"  Funciones detectadas: {len(fnames)}")

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
            err = r.stderr.strip().splitlines()[-1] if r.stderr else "?"
            print(f"  ERR {mod}.js — {err}")
            errors.append(mod)
    print(f"  Resultado: {ok}/{total} válidos")
    return ok == total and total > 0

# === Restaurar index.html ===
print("Restaurando index.html desde git...")
os.system(f"cd {BASE} && git checkout -- {os.path.relpath(TPL, BASE)}")

# === Ejecutar ===
print("\nTPV Modularización v2.1")
print("=" * 55)

ok5 = process(os.path.join(JS_DIR,"script_5.js"), MAP5, RESOLVE5, "tpv_core",
              S5_ORDER, HDR5, "Script 5")
ok8 = process(os.path.join(JS_DIR,"script_8.js"), MAP8, RESOLVE8, "tpv_auth",
              S8_ORDER, HDR8, "Script 8")

if ok5 and ok8:
    html = read(TPL)
    html = html.replace(
        '<script src="/static/js/script_5.js"></script>',
        '\n'.join(f'    <script src="/static/js/tpv/{m}.js"></script>' for m in S5_ORDER))
    html = html.replace(
        '<script src="/static/js/script_8.js"></script>',
        '\n'.join(f'    <script src="/static/js/tpv/{m}.js"></script>' for m in S8_ORDER))
    write(TPL, html)
    print(f"\n{'='*55}")
    print("OK Todos los módulos válidos + index.html actualizado")
    print("\n  cd ~/tpv-chaquopy && git add -A && git commit -m 'feat: modularización v2' && git push")
else:
    print("\nERROR: módulos inválidos. index.html NO modificado.")
    sys.exit(1)
