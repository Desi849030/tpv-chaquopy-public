#!/usr/bin/env python3
"""FIX SEGUROS - Solo cambios probados que no rompen HTML"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'templates', 'partials')
TABS = os.path.join(TPL, 'tabs')
JS = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'static', 'js', 'tpv')
n = 0

def r(f, d):
    global n; n += 1; print("  [%d] %s" % (n, d))

# === 1. _scripts.html: quitar </body> (simple replace) ===
print("[1] _scripts.html")
p = os.path.join(TPL, '_scripts.html')
with open(p, 'r') as f: s = f.read()
antes = s.count('</body>')
s = s.replace('</body>', '')
r(p, "Eliminado </body> (%d encontrados)" % antes)
with open(p, 'w') as f: f.write(s)

# === 2. _scripts.html: quitar Google Translate roto (multilinea literal) ===
with open(p, 'r') as f: s = f.read()
gt_block = '''<script type="text/javascript"
<!-- Google Translate removed -->
    onerror="(function(){ console.warn('Google Translate no disponible (sin conexion)'); var s=_langGuardado(); _actualizarBotonesLang(s); })()">
</script>'''
if gt_block in s:
    s = s.replace(gt_block, '')
    r(p, "Eliminado bloque Google Translate roto")
elif 'Google Translate removed' in s:
    # Fallback: remove everything between markers
    lines = s.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if 'Google Translate removed' in line:
            skip = True
            continue
        if skip and line.strip().startswith('</script>'):
            skip = False
            continue
        if skip:
            continue
        new_lines.append(line)
    s = '\n'.join(new_lines)
    r(p, "Eliminado GT roto (fallback multilinea)")
with open(p, 'w') as f: f.write(s)

# === 3. _scripts.html: fix licencias ID ===
with open(p, 'r') as f: s = f.read()
if 'cfg-licencias-tab' in s:
    s = s.replace('cfg-licencias-tab', 'licencias-tab')
    r(p, "cfg-licencias-tab -> licencias-tab")
with open(p, 'w') as f: f.write(s)

# === 4. tpv_estado_shim.js: migrar localStorage ===
print("[2] tpv_estado_shim.js")
shim = os.path.join(JS, 'tpv_estado_shim.js')
with open(shim, 'r') as f: s = f.read()
antes = s.count('localStorage.')
s = s.replace('localStorage.setItem(', 'tpvStorage.setItem(')
s = s.replace('localStorage.getItem(', 'tpvStorage.getItem(')
despues = s.count('localStorage.')
r(shim, "localStorage->tpvStorage (%d reemplazos)" % (antes - despues))
with open(shim, 'w') as f: f.write(s)

# === 5. _nav_header.html: agregar offline-indicator ===
print("[3] _nav_header.html")
nav = os.path.join(TPL, '_nav_header.html')
with open(nav, 'r') as f: s = f.read()
if 'offline-indicator' not in s:
    s = s.replace(
        '<div id="network-status">',
        '<div id="offline-indicator" style="display:none" class="badge bg-danger"><i class="bi bi-wifi-off"></i> Offline</div>\n                <div id="network-status">'
    )
    r(nav, "Agregado offline-indicator")
with open(nav, 'w') as f: f.write(s)

# === 6. _head.html: quitar CSS duplicada tpv_ia_pro.css ===
print("[4] _head.html")
head = os.path.join(TPL, '_head.html')
with open(head, 'r') as f: s = f.read()
if s.count('tpv_ia_pro.css') > 1:
    # Keep only the FIRST occurrence (in head, before body renders)
    idx1 = s.find("tpv_ia_pro.css")
    idx2 = s.find("tpv_ia_pro.css", idx1 + 20)
    if idx2 > 0:
        line_start = s.rfind('\n', 0, idx2) + 1
        line_end = s.find('\n', idx2)
        if line_end < 0: line_end = len(s)
        s = s[:line_start] + s[line_end:]
        r(head, "Eliminada tpv_ia_pro.css duplicada")
with open(head, 'w') as f: f.write(s)

# === 7. _head.html: quitar skip-nav del head ===
with open(head, 'r') as f: s = f.read()
if '<a href="#tpv-app" class="skip-nav">' in s:
    s = s.replace('<a href="#tpv-app" class="skip-nav">Ir al contenido</a>\n', '')
    r(head, "Eliminado skip-nav del <head>")
with open(head, 'w') as f: f.write(s)

# === 8. _modals.html: agregar modals faltantes ===
print("[5] _modals.html")
modals = os.path.join(TPL, '_modals.html')
with open(modals, 'r') as f: s = f.read()
if 'modal-usuarios' not in s:
    s += '''
<!-- Modal Gestion Usuarios -->
<div class="modal fade" id="modal-usuarios" tabindex="-1">
  <div class="modal-dialog modal-lg"><div class="modal-content">
    <div class="modal-header"><h5 class="modal-title"><i class="bi bi-people me-2"></i>Gestionar Usuarios</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body">
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#ut-lista">Lista</a></li>
        <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#up-crear">Crear</a></li>
        <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#pw-act">Cambiar Clave</a></li>
      </ul>
      <div class="tab-content">
        <div class="tab-pane fade show active" id="ut-lista"><div id="u-lista-body"></div></div>
        <div class="tab-pane fade" id="up-crear">
          <div class="mb-2"><label>Nombre</label><input id="nu-nombre" class="form-control"></div>
          <div class="mb-2"><label>Usuario</label><input id="nu-user" class="form-control"></div>
          <div class="mb-2"><label>Clave</label><input id="nu-pw" type="password" class="form-control"></div>
          <div class="mb-2"><label>Rol</label><select id="nu-rol" class="form-control"><option value="vendedor">Vendedor</option><option value="administrador">Administrador</option><option value="desarrollador">Desarrollador</option></select></div>
          <button class="btn btn-primary" onclick="crear_usuario()">Crear</button>
        </div>
        <div class="tab-pane fade" id="pw-act">
          <div class="mb-2"><label>Usuario</label><input id="pw-act-user" class="form-control"></div>
          <div class="mb-2"><label>Nueva Clave</label><input id="pw-new" type="password" class="form-control"></div>
          <div class="mb-2"><label>Confirmar</label><input id="pw-con" type="password" class="form-control"></div>
          <button class="btn btn-primary" onclick="cambiar_clave_admin()">Cambiar</button>
        </div>
      </div>
    </div>
  </div></div>
</div>
'''
    r(modals, "Agregado modal-usuarios")
if 'modal-notif' not in s:
    s += '''
<!-- Modal Notificaciones -->
<div class="modal fade" id="modal-notif" tabindex="-1">
  <div class="modal-dialog"><div class="modal-content">
    <div class="modal-header"><h5 class="modal-title"><i class="bi bi-bell me-2"></i>Notificaciones</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body"><div id="notif-body"><p class="text-muted">Sin notificaciones.</p></div></div>
  </div></div>
</div>
'''
    r(modals, "Agregado modal-notif")
with open(modals, 'w') as f: f.write(s)

print("\n" + "="*55)
print("FIXES SEGUROS: %d aplicados" % n)
print("="*55)
