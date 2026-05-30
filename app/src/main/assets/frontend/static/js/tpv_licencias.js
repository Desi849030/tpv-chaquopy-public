// Módulo de Licencias - Solo desarrollador
setTimeout(function() {
  if (typeof window.currentUser !== 'undefined' && window.currentUser && window.currentUser.rol === 'desarrollador') {
    agregarBotonLicencias();
  } else {
    fetch('/api/auth/me').then(function(r) { return r.json(); }).then(function(d) {
      if (d.usuario && d.usuario.rol === 'desarrollador') {
        window.currentUser = d.usuario;
        agregarBotonLicencias();
      }
    });
  }
}, 1500);

function agregarBotonLicencias() {
  var nav = document.getElementById('nav-bar');
  if (!nav) return;
  if (document.getElementById('btn-licencias')) return;
  var btn = document.createElement('button');
  btn.id = 'btn-licencias';
  btn.className = 'nav-btn';
  btn.textContent = '📜 Licencias';
  btn.onclick = mostrarPanelLicencias;
  nav.appendChild(btn);
}

function mostrarPanelLicencias() {
  var existente = document.getElementById('panel-licencias-tpv');
  if (existente) { existente.remove(); return; }
  var div = document.createElement('div');
  div.id = 'panel-licencias-tpv';
  div.style.cssText = 'position:fixed;top:60px;left:50%;transform:translateX(-50%);width:95%;max-width:900px;max-height:80vh;overflow-y:auto;z-index:500;background:#1e293b;border:2px solid #6366f1;border-radius:16px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.5)';
  div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><h3 style="color:white;margin:0">📜 Gestión de Licencias</h3><button onclick="var p=document.getElementById(\'panel-licencias-tpv\');if(p)p.remove()" style="background:rgba(255,255,255,.1);border:none;color:white;width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:1.2rem">X</button></div>' +
    '<button onclick="mostrarFormLicencia()" style="background:#6366f1;border:none;color:white;padding:10px 20px;border-radius:20px;cursor:pointer;margin-bottom:16px;font-weight:600">+ Asignar Licencia</button>' +
    '<div id="licencias-lista">Cargando...</div>';
  document.body.appendChild(div);
  cargarLicencias();
}

function mostrarFormLicencia() {
  var form = document.createElement('div');
  form.id = 'form-licencia';
  form.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center';
  form.innerHTML = '<div style="background:#1e293b;border:2px solid #6366f1;border-radius:16px;padding:24px;width:90%;max-width:400px">' +
    '<h3 style="color:white;margin-bottom:16px">Asignar Licencia</h3>' +
    '<label style="color:#94a3b8;font-size:.75rem">Admin ID</label><input id="lic-admin" value="usr-001" style="width:100%;padding:10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-bottom:10px">' +
    '<label style="color:#94a3b8;font-size:.75rem">Días</label><input id="lic-dias" type="number" value="30" min="1" max="365" style="width:100%;padding:10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-bottom:10px">' +
    '<label style="color:#94a3b8;font-size:.75rem">Tipo</label><select id="lic-tipo" style="width:100%;padding:10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-bottom:10px"><option value="anual">Anual</option><option value="mensual">Mensual</option></select>' +
    '<div style="display:flex;gap:8px"><button onclick="crearLicencia()" style="flex:1;padding:10px;background:#6366f1;border:none;border-radius:8px;color:white;font-weight:600;cursor:pointer">Asignar</button><button onclick="var f=document.getElementById(\'form-licencia\');if(f)f.remove()" style="flex:1;padding:10px;background:#334155;border:none;border-radius:8px;color:white;cursor:pointer">Cancelar</button></div></div>';
  document.body.appendChild(form);
  form.onclick = function(e) { if (e.target === form) form.remove(); };
}

function crearLicencia() {
  var admin = document.getElementById('lic-admin').value;
  var dias = document.getElementById('lic-dias').value;
  var tipo = document.getElementById('lic-tipo').value;
  fetch('/api/admin/licencias/crear', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({admin_id: admin, dias: parseInt(dias), tipo: tipo, admin_nombre: 'Administrador'})
  }).then(function(r) { return r.json(); }).then(function(d) {
    alert(d.ok ? 'Licencia creada. Expira: ' + d.expira : 'Error');
    if (d.ok) {
      var f = document.getElementById('form-licencia');
      if (f) f.remove();
      cargarLicencias();
    }
  });
}

function cargarLicencias() {
  var lista = document.getElementById('licencias-lista');
  if (!lista) return;
  fetch('/api/admin/licencias').then(function(r) { return r.json(); }).then(function(d) {
    if (d.licencias && d.licencias.length > 0) {
      var html = '<table style="width:100%;border-collapse:collapse;color:white;font-size:.8rem"><tr style="background:#0f172a"><th style="padding:8px">Admin</th><th style="padding:8px">Tipo</th><th style="padding:8px">Días</th><th style="padding:8px">Expira</th><th style="padding:8px">Estado</th><th style="padding:8px"></th></tr>';
      d.licencias.forEach(function(l) {
        html += '<tr style="border-bottom:1px solid #334155"><td style="padding:8px">'+l.admin_nombre+'</td><td style="padding:8px">'+l.tipo+'</td><td style="padding:8px">'+l.dias+'</td><td style="padding:8px">'+l.fecha_expira+'</td><td style="padding:8px"><span style="background:'+(l.activa?'rgba(16,185,129,.2);color:#10b981':'rgba(239,68,68,.2);color:#ef4444')+';padding:3px 8px;border-radius:10px;font-size:.7rem;font-weight:700">'+(l.activa?'Activa':'Revocada')+'</span></td><td style="padding:8px">'+(l.activa?'<button onclick="revocarLicencia(\''+l.id+'\')" style="background:rgba(239,68,68,.2);color:#ef4444;border:none;padding:5px 10px;border-radius:8px;cursor:pointer;font-size:.7rem">Revocar</button>':'')+'</td></tr>';
      });
      html += '</table>';
      lista.innerHTML = html;
    } else {
      lista.innerHTML = '<p style="color:#94a3b8;text-align:center;padding:20px">No hay licencias registradas</p>';
    }
  });
}

function revocarLicencia(id) {
  if (!confirm('¿Revocar esta licencia?')) return;
  fetch('/api/admin/licencias/'+id+'/revocar', {method:'PUT'}).then(function() { cargarLicencias(); });
}
