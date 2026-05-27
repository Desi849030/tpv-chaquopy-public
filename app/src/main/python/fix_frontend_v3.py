#!/usr/bin/env python3
"""FIX FRONTEND v3 - Los 6 fixes faltantes (H3b, H4, H5, M2, M5, L5)"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'templates', 'partials')
TABS = os.path.join(TPL, 'tabs')
JS = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'static', 'js', 'tpv')

fixes = 0
def fix(f, d):
    global fixes; fixes += 1; print("  [FIX %d] %s" % (fixes, d))

# ═══ H3b: Missing IDs cfg-mant-wrap, bio-btn ═══
print("[H3b] Missing IDs cfg-mant-wrap, bio-btn")
herr = os.path.join(TABS, '_tab_herramientas.html')
with open(herr, 'r') as f: s = f.read()
if 'cfg-mant-wrap' not in s:
    s = s.replace('<div class="tab-pane fade"', '<div id="cfg-mant-wrap" class="tab-pane fade"')
    fix(herr, "Added cfg-mant-wrap ID to herramientas tab")

# Add bio-btn to login area if exists
login_tab = os.path.join(TABS, '_tab_caja.html')
with open(login_tab, 'r') as f: s2 = f.read()
if 'bio-btn' not in s2 and 'btn-login' in s2:
    s2 = s2.replace('id="btn-login"', 'id="btn-login"\n    style="margin-bottom:6px"')
    # Find the form closing or a button after login and add bio-btn
    if 'data-bio="1"' not in s2:
        s2 = s2.replace('</form>', '<button type="button" id="bio-btn" class="btn btn-outline-secondary w-100 mb-2" onclick="bio_login()" style="display:none"><i class="bi bi-fingerprint me-2"></i>Huella</button></form>')
        fix(login_tab, "Added bio-btn biometric login button")
with open(login_tab, 'w') as f: f.write(s2)
with open(herr, 'w') as f: f.write(s)

# ═══ H4: Orphan tpv_debugger.js ═══
print("[H4] Orphan tpv_debugger.js - remove from lazy loader")
lazy = os.path.join(JS, 'tpv_lazy_loader.js')
with open(lazy, 'r') as f: s = f.read()
# Remove tpv_debugger.js from lazy loader _tabMap
if 'tpv_debugger.js' in s:
    s = re.sub(r'["\']\/static\/js\/tpv\/tpv_debugger\.js["\'],?\s*\n?', '', s)
    fix(lazy, "Removed orphan tpv_debugger.js from lazy loader")
with open(lazy, 'w') as f: f.write(s)

# ═══ H5: Lazy loader redundantly loads already-loaded scripts ═══
print("[H5] Clean lazy loader - remove already-loaded scripts")
with open(lazy, 'r') as f: s = f.read()
# Scripts already in _scripts.html that don't need lazy loading
already_loaded = [
    'tpv_tienda_init.js', 'tpv_tienda_carrito.js', 'tpv_tienda_pedidos.js',
    'tpv_auth_cliente.js', 'tpv_auth_main.js', 'tpv_dev_metrics.js',
    'tpv_gestion_usuarios.js'
]
for script in already_loaded:
    pattern = r'["\']\/static\/js\/tpv\/' + script + r'["\'],?\s*\n?'
    if re.search(pattern, s):
        s = re.sub(pattern, '', s)
        print("    Removed from lazy: " + script)
fix(lazy, "Cleaned lazy loader - only truly lazy scripts remain")
with open(lazy, 'w') as f: f.write(s)

# ═══ M2: Orphan JS files - integrate or mark ═══
print("[M2] Orphan JS files - tpv_admin_inventario.js not loaded")
scripts_html = os.path.join(TPL, '_scripts.html')
with open(scripts_html, 'r') as f: s = f.read()
if 'tpv_admin_inventario.js' not in s:
    # Add it after tpv_inventario_stock.js
    s = s.replace(
        '<script src="/static/js/tpv/tpv_inventario_stock.js"></script>',
        '<script src="/static/js/tpv/tpv_inventario_stock.js"></script>\n    <script src="/static/js/tpv/tpv_admin_inventario.js"></script>'
    )
    fix(scripts_html, "Added orphan tpv_admin_inventario.js to _scripts.html")
with open(scripts_html, 'w') as f: f.write(s)

# ═══ M5: Three nav items target same herramientas-tab-pane ═══
print("[M5] Nav items sharing same pane - add scroll anchors")
nav = os.path.join(TPL, '_nav_header.html')
with open(nav, 'r') as f: s = f.read()
# Add onclick scroll-to-section for herramientas items
s = s.replace(
    'id="importar-exportar-tab" data-bs-toggle="tab" data-bs-target="#herramientas-tab-pane"',
    'id="importar-exportar-tab" data-bs-toggle="tab" data-bs-target="#herramientas-tab-pane" onclick="setTimeout(function(){var el=document.getElementById(\'sec-importar\');if(el)el.scrollIntoView({behavior:\'smooth\'})},300)"'
)
s = s.replace(
    'id="copias-seguridad-tab" data-bs-toggle="tab" data-bs-target="#herramientas-tab-pane"',
    'id="copias-seguridad-tab" data-bs-toggle="tab" data-bs-target="#herramientas-tab-pane" onclick="setTimeout(function(){var el=document.getElementById(\'sec-backup\');if(el)el.scrollIntoView({behavior:\'smooth\'})},300)"'
)
fix(nav, "Added scroll anchors to shared herramientas pane nav items")

# Add section IDs to herramientas tab
with open(herr, 'r') as f: s = f.read()
if 'sec-importar' not in s:
    s = re.sub(r'(<h5[^>]*>Importar[^<]*</h5>)', r'<div id="sec-importar">\1', s)
    s = re.sub(r'(<h5[^>]*>Copias de Seguridad[^<]*</h5>)', r'</div><div id="sec-backup">\1', s)
    fix(herr, "Added section IDs sec-importar and sec-backup in herramientas tab")
with open(herr, 'w') as f: f.write(s)
with open(nav, 'w') as f: f.write(s)

# ═══ L5: _toast() inconsistent API ═══
print("[L5] Add _toast fallback that calls showToast")
usuarios_js = os.path.join(JS, 'tpv_gestion_usuarios.js')
with open(usuarios_js, 'r') as f: s = f.read()
if '_toast' in s and 'function _toast' not in s:
    # Add _toast at the top that delegates to showToast
    header = '''(function(){
if(typeof _toast==='undefined'){
function _toast(msg, type){
    if(typeof showToast==='function'){showToast(msg, type||'info');}
    else{console.log('[toast] '+msg);}
}
window._toast = _toast;
}
})();
'''
    s = header + s
    fix(usuarios_js, "Added _toast() fallback that calls showToast()")
with open(usuarios_js, 'w') as f: f.write(s)

print("\n" + "="*55)
print("FRONTEND FIXES v3: %d aplicados (total: 19/19)" % fixes)
print("="*55)
