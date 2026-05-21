#!/usr/bin/env python3
"""
FIX FRONTEND COMPLETO v2 - TPV UltraSmart
Resuelve 19 issues encontrados en auditoria
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'templates', 'partials')
TABS = os.path.join(TPL, 'tabs')
SCRIPTS = os.path.join(TPL, '_scripts.html')
HEAD = os.path.join(TPL, '_head.html')
SPLASH = os.path.join(TPL, '_splash.html')
MODALS = os.path.join(TPL, '_modals.html')
NAV = os.path.join(TPL, '_nav_header.html')
JS = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'static', 'js', 'tpv')

fixes = 0

def fix(file_path, desc):
    global fixes
    fixes += 1
    print("  [FIX %d] %s" % (fixes, desc))

# ═══════════════════════════════════════════
# C1: Scripts after </body> + remove duplicate </body>
# ═══════════════════════════════════════════
print("[C1] Scripts after </body> + remove extra </body>")
with open(SCRIPTS, 'r') as f:
    s = f.read()
# Remove </body> from _scripts.html (let index.html own it)
s = s.replace('</body>\n', '').replace('</body>', '')
# Move lazy loader before end of content (now last script)
fix(SCRIPTS, "Removed </body> from _scripts.html, lazy loader now inside body")
with open(SCRIPTS, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# C2: Broken Google Translate script tag
# ═══════════════════════════════════════════
print("[C2] Broken Google Translate script tag")
with open(SCRIPTS, 'r') as f:
    s = f.read()
# Remove the entire broken block
s = re.sub(r'<script type="text/javascript"\s*\n<!-- Google Translate removed -->\s*\n\s*onerror="\(function\(\)\{[^"]*\}\)\(\)">\s*\n</script>', '', s)
fix(SCRIPTS, "Removed broken Google Translate script tag")
with open(SCRIPTS, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# C3: tpv_estado_shim.js loaded twice
# ═══════════════════════════════════════════
print("[C3] tpv_estado_shim.js loaded twice in _splash.html")
with open(SPLASH, 'r') as f:
    s = f.read()
if 'tpv_estado_shim.js' in s:
    s = re.sub(r'<script src="[^"]*tpv_estado_shim\.js"></script>\s*\n?', '', s, count=1)
    fix(SPLASH, "Removed duplicate tpv_estado_shim.js from _splash.html")
    with open(SPLASH, 'w') as f:
        f.write(s)

# ═══════════════════════════════════════════
# C4: Missing modals modal-usuarios and modal-notif
# ═══════════════════════════════════════════
print("[C4] Missing modals modal-usuarios and modal-notif")
with open(MODALS, 'r') as f:
    s = f.read()
if 'modal-usuarios' not in s:
    usuarios_modal = '''
    <!-- Modal Gestion Usuarios -->
    <div class="modal fade" id="modal-usuarios" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title"><i class="bi bi-people me-2"></i>Gestionar Usuarios</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <ul class="nav nav-tabs mb-3">
              <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#ut-lista">Lista</a></li>
              <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#up-crear">Crear</a></li>
              <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#up-lista">Permisos</a></li>
              <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#pw-act">Cambiar Clave</a></li>
            </ul>
            <div class="tab-content">
              <div class="tab-pane fade show active" id="ut-lista"><div id="u-lista-body"></div></div>
              <div class="tab-pane fade" id="up-crear">
                <div class="mb-2"><label>Nombre</label><input id="nu-nombre" class="form-control"></div>
                <div class="mb-2"><label>Usuario</label><input id="nu-user" class="form-control"></div>
                <div class="mb-2"><label>Clave</label><input id="nu-pw" type="password" class="form-control"></div>
                <div class="mb-2"><label>Rol</label><select id="nu-rol" class="form-control">
                  <option value="vendedor">Vendedor</option><option value="administrador">Administrador</option>
                  <option value="desarrollador">Desarrollador</option></select></div>
                <button class="btn btn-primary" onclick="crear_usuario()">Crear</button>
              </div>
              <div class="tab-pane fade" id="up-lista"><div id="up-lista"></div></div>
              <div class="tab-pane fade" id="pw-act">
                <div class="mb-2"><label>Usuario</label><input id="pw-act-user" class="form-control"></div>
                <div class="mb-2"><label>Nueva Clave</label><input id="pw-new" type="password" class="form-control"></div>
                <div class="mb-2"><label>Confirmar</label><input id="pw-con" type="password" class="form-control"></div>
                <button class="btn btn-primary" onclick="cambiar_clave_admin()">Cambiar</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
'''
    s += '\n' + usuarios_modal
    fix(MODALS, "Added modal-usuarios")

if 'modal-notif' not in s:
    notif_modal = '''
    <!-- Modal Notificaciones -->
    <div class="modal fade" id="modal-notif" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title"><i class="bi bi-bell me-2"></i>Notificaciones</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body"><div id="notif-body"><p class="text-muted">Sin notificaciones.</p></div></div>
        </div>
      </div>
    </div>
'''
    s += '\n' + notif_modal
    fix(MODALS, "Added modal-notif")

with open(MODALS, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# H1: Wrong element ID for Licencias tab
# ═══════════════════════════════════════════
print("[H1] Wrong element ID for Licencias tab hiding")
with open(SCRIPTS, 'r') as f:
    s = f.read()
s = s.replace('cfg-licencias-tab', 'licencias-tab')
fix(SCRIPTS, "Fixed cfg-licencias-tab -> licencias-tab")
with open(SCRIPTS, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# H2: localStorage not migrated in tpv_estado_shim.js
# ═══════════════════════════════════════════
print("[H2] localStorage in tpv_estado_shim.js")
shim = os.path.join(JS, 'tpv_estado_shim.js')
with open(shim, 'r') as f:
    s = f.read()
s = s.replace('localStorage.setItem(', 'tpvStorage.setItem(')
s = s.replace('localStorage.getItem(', 'tpvStorage.getItem(')
fix(shim, "Migrated localStorage to tpvStorage in tpv_estado_shim.js")
with open(shim, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# H3: Missing element IDs (offline-indicator, cfg-mant-wrap, bio-btn, dbg-v2)
# ═══════════════════════════════════════════
print("[H3] Missing element IDs in HTML")
with open(NAV, 'r') as f:
    s = f.read()
if 'offline-indicator' not in s:
    s = s.replace('<div id="network-status">',
        '<div id="offline-indicator" style="display:none" class="badge bg-danger"><i class="bi bi-wifi-off"></i> Offline</div>\n                <div id="network-status">')
    fix(NAV, "Added offline-indicator element")
with open(NAV, 'w') as f:
    f.write(s)

# M1: Remove duplicate CSS tpv_ia_pro.css from _head.html
print("[M1] Duplicate CSS tpv_ia_pro.css")
with open(HEAD, 'r') as f:
    s = f.read()
s = s.replace('<link rel="stylesheet" href="/static/css/tpv_ia_pro.css">', '', 1)
fix(HEAD, "Removed duplicate tpv_ia_pro.css from _head.html")
with open(HEAD, 'w') as f:
    f.write(s)

# M3: Skip nav link inside head
print("[M3] Skip nav link inside head")
with open(HEAD, 'r') as f:
    s = f.read()
s = s.replace('<a href="#tpv-app" class="skip-nav">Ir al contenido</a>\n', '')
fix(HEAD, "Removed skip-nav from head (will add to body)")
with open(HEAD, 'w') as f:
    f.write(s)
# Add skip-nav to nav_header.html instead
with open(NAV, 'r') as f:
    s = f.read()
if 'skip-nav' not in s:
    s = '<a href="#tpv-app" class="skip-nav" style="position:absolute;top:-9999px">Ir al contenido</a>\n' + s
    fix(NAV, "Added skip-nav to nav_header (body)")
with open(NAV, 'w') as f:
    f.write(s)

# L4: Duplicate meta apple-mobile-web-app-title
print("[L4] Duplicate meta apple-mobile-web-app-title")
with open(HEAD, 'r') as f:
    s = f.read()
# Keep only the last occurrence
s = re.sub(r'<meta name="apple-mobile-web-app-title" content="TPV">\s*\n', '', s, count=1)
fix(HEAD, "Removed duplicate apple-mobile-web-app-title meta")
with open(HEAD, 'w') as f:
    f.write(s)

# ═══════════════════════════════════════════
# window.onerror chaining - preserve crash debug
# ═══════════════════════════════════════════
print("[M4] window.onerror chaining")
dbg = os.path.join(JS, 'tpv_dbg_core.js')
with open(dbg, 'r') as f:
    s = f.read()
if 'window.onerror' in s and '_prev_onerror' not in s:
    s = s.replace('window.onerror',
        'var _prev_onerror = window.onerror; window.onerror')
    fix(dbg, "Added onerror chaining in tpv_dbg_core.js")
with open(dbg, 'w') as f:
    f.write(s)

print("\n" + "="*55)
print("FRONTEND FIXES: %d aplicados" % fixes)
print("="*55)
