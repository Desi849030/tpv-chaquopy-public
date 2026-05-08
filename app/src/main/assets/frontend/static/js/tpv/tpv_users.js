// tpv_users.js
async function auth_verNotificaciones() {
    const body = document.getElementById('notif-body');
    if (body) body.innerHTML = '<div class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm me-2"></div></div>';
    new bootstrap.Modal(document.getElementById('modal-notif')).show();
    try {
        const r   = await fetch('/api/pedidos?estado=pendiente');
        const d   = await r.json();
        const ped = d.pedidos || [];
        if (!ped.length) {
            body.innerHTML = '<div class="text-center py-4 text-success"><i class="bi bi-check-circle-fill" style="font-size:2rem"></i><br><br>Sin pedidos pendientes</div>';
            return;
        }
        body.innerHTML = ped.map(p => `
        <div class="d-flex justify-content-between align-items-center p-2 mb-2
                    rounded-3 bg-warning bg-opacity-10 border border-warning border-opacity-25">
            <div>
                <div class="fw-bold">🛒 #${(p.pedido_id||p.id||'').toString().slice(-6)}</div>
                <div class="text-muted small">${p.cliente_nombre||'Cliente'} · ${(p.items||[]).length} art.</div>
            </div>
            <div class="text-end">
                <div class="fw-bold text-success">$${parseFloat(p.total||0).toFixed(2)}</div>
                <div class="text-muted small">${new Date(p.fecha||Date.now()).toLocaleTimeString()}</div>
            </div>
        </div>`).join('');
    } catch(e) {
        if (body) body.innerHTML = '<div class="alert alert-danger">Error al cargar.</div>';
    }
}

// ══════════════════════════════════════════════════════════════
//  GESTIÓN DE USUARIOS
// ══════════════════════════════════════════════════════════════
function auth_abrirUsuarios() {
    const rol = AUTH.usuario?.rol;
    // Roles que puede crear cada uno
    const puede = {
        desarrollador: ['administrador','supervisor','vendedor'],
        administrador: ['supervisor','vendedor'],
        supervisor:    [],
        vendedor:      []
    };
    const roles = puede[rol] || [];

    const sel = document.getElementById('nu-rol');
    if (sel) {
        sel.innerHTML = '<option value="">— Seleccionar —</option>' +
            roles.map(r => `<option value="${r}">${ROL_INFO[r]?.label||r}</option>`).join('');
    }

    // Ocultar tab "Crear" si no puede crear
    document.getElementById('ut-crear-li')?.classList.toggle('d-none', roles.length === 0);

    auth_tab('lista');
    new bootstrap.Modal(document.getElementById('modal-usuarios')).show();
    _cargarUsuarios();
}

function auth_tab(t) {
    [['lista','up-lista','ut-lista'],
     ['crear','up-crear','ut-crear'],
     ['pw',   'up-pw',   'ut-pw']].forEach(([k, p, b]) => {
        document.getElementById(p)?.classList.toggle('d-none', k !== t);
        document.getElementById(b)?.classList.toggle('active', k === t);
    });
}

async function _cargarUsuarios() {
    const body = document.getElementById('u-lista-body');
    if (!body) return;
    body.innerHTML = '<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Cargando...</div>';
    try {
        const res  = await fetch('/api/usuarios', { credentials:'same-origin' });
        const data = await res.json();
        if (!res.ok) { body.innerHTML = `<div class="alert alert-warning">${data.error||'Sin acceso'}</div>`; return; }
        const usuarios = data.usuarios || [];
        if (!usuarios.length) {
            body.innerHTML = '<div class="text-center py-4 text-muted">No hay usuarios creados aún.</div>';
            return;
        }
        body.innerHTML = usuarios.map(u => {
            const ri = ROL_INFO[u.rol] || { color:'#6c757d', label:u.rol, icono:'bi-person' };
            return `
            <div class="u-card">
                <div class="d-flex align-items-center gap-2">
                    <i class="bi ${ri.icono}" style="color:${ri.color};font-size:1.25rem;flex-shrink:0"></i>
                    <div>
                        <div class="fw-semibold">${u.nombre}</div>
                        <div class="text-muted small">@${u.username}${u.ultimo_acceso?` · ${u.ultimo_acceso}`:''}</div>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-2 flex-shrink-0">
                    <span class="u-pill" style="background:${ri.color}22;color:${ri.color};border:1px solid ${ri.color}55">
                        ${ri.label}
                    </span>
                    <button class="btn btn-sm btn-outline-danger" title="Desactivar"
                            onclick="auth_desactivar('${u.usuario_id}','${u.nombre.replace(/'/g,"\\'")}')">
                        <i class="bi bi-person-x-fill"></i>
                    </button>
                </div>
            </div>`;
        }).join('');
    } catch(e) {
        body.innerHTML = '<div class="alert alert-danger">Error de conexión.</div>';
    }
}

async function auth_crearUsuario() {
    const nombre = document.getElementById('nu-nombre')?.value.trim();
    const user   = document.getElementById('nu-user')?.value.trim();
    const pw     = document.getElementById('nu-pw')?.value;
    const rol    = document.getElementById('nu-rol')?.value;
    if (!nombre || !user || !pw || !rol) { _toast('Completa todos los campos.','warning'); return; }
    try {
        const res  = await fetch('/api/usuarios/crear', {
            method:'POST', headers:{'Content-Type':'application/json'},
            credentials:'same-origin',
            body: JSON.stringify({ nombre, username:user, password:pw, rol })
        });
        const data = await res.json();
        if (res.ok && data.ok) {
            _toast(`✅ Usuario "${user}" creado.`,'success');
            ['nu-nombre','nu-user','nu-pw'].forEach(id => { const el=document.getElementById(id); if(el) el.value=''; });
            document.getElementById('nu-rol').value = '';
            auth_tab('lista'); _cargarUsuarios();
        } else _toast(data.error||'Error al crear.','danger');
    } catch(e) { _toast('Error de conexión.','danger'); }
}

async function auth_desactivar(id, nombre) {
    if (!confirm(`¿Desactivar a "${nombre}"?\nNo podrá iniciar sesión.`)) return;
    try {
        const res  = await fetch(`/api/usuarios/${id}`, { method:'DELETE', credentials:'same-origin' });
        const data = await res.json();
        if (res.ok) { _toast(`✅ "${nombre}" desactivado.`,'success'); _cargarUsuarios(); }
        else _toast(data.error||'Error.','danger');
    } catch(e) { _toast('Error de conexión.','danger'); }
}

async function auth_cambiarPw() {
    const act = document.getElementById('pw-act')?.value;
    const nw  = document.getElementById('pw-new')?.value;
    const con = document.getElementById('pw-con')?.value;
    if (!act || !nw || !con) { _toast('Completa todos los campos.','warning'); return; }
    if (nw !== con) { _toast('Las contraseñas nuevas no coinciden.','warning'); return; }
    if (nw.length < 4) { _toast('Mínimo 4 caracteres.','warning'); return; }
    try {
        const res  = await fetch('/api/auth/cambiar-password', {
            method:'POST', headers:{'Content-Type':'application/json'},
            credentials:'same-origin',
            body: JSON.stringify({ password_actual:act, password_nueva:nw })
        });
        const data = await res.json();
        if (res.ok && data.ok) {
            _toast('✅ Contraseña cambiada.','success');
            ['pw-act','pw-new','pw-con'].forEach(id => { const el=document.getElementById(id); if(el) el.value=''; });
        } else _toast(data.error||'Error.','danger');
    } catch(e) { _toast('Error de conexión.','danger'); }
}

function _toast(msg, type) {
    if (typeof showToast === 'function') showToast(msg, type);
    else console.log('[Toast]', msg);
}

// ══════════════════════════════════════════════════════════════
//  LICENCIAS (solo Desarrollador)
// ══════════════════════════════════════════════════════════════
const _LIC_DIAS = { diaria:1, mensual:30, anual:365, ilimitada:99999 };

