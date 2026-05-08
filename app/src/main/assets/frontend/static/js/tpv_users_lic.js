/**
 * tpv_users_lic.js — TPV ULTRA SMART v5.0
 * Usuarios, Licencias, Polling, Biometria
 * Extraido de script_8.js
 */

    // Cerrar SSE primero
    if (_sseConn) { try { _sseConn.close(); } catch(e){} _sseConn = null; }
    if (AUTH.pollingNotif) { clearInterval(AUTH.pollingNotif); AUTH.pollingNotif = null; }
    // Limpiar polling de vendedores si existe
    if (window._vendPolling) { clearInterval(window._vendPolling); window._vendPolling = null; }

    // Auto-backup con TIMEOUT de 3s MAXIMO (no bloquea el logout)
    try {
        showToast('💾 Guardando respaldo...', 'info');
        var backupCtrl = new AbortController();
        setTimeout(function(){ backupCtrl.abort(); }, 3000);
        await fetch('/api/auth/auto-backup', { method:'POST', credentials:'same-origin', signal: backupCtrl.signal });
    } catch(e) {
        // Timeout o error - no importa, continuar con el logout
    }

    // Logout del servidor (con timeout)
    try {
        var logoutCtrl = new AbortController();
        setTimeout(function(){ logoutCtrl.abort(); }, 2000);
        await fetch('/api/auth/logout', { method:'POST', signal: logoutCtrl.signal });
    } catch(e) {}

    // Limpiar panel debug al cerrar sesión
    if (typeof window._dbg_limpiar === 'function') window._dbg_limpiar();
    AUTH.usuario = null;
    localStorage.removeItem("tpv_rol");
    localStorage.removeItem("tpv_user");
    localStorage.removeItem("tpv_rol");
    localStorage.removeItem("tpv_user");
    // Resetear chat IA a Usuario
    if (typeof updateRoleDisplay === "function") updateRoleDisplay("cliente");
    _prevN = -1;

    document.getElementById('user-bar')?.classList.add('d-none');
    document.getElementById('notif-bell-wrap')?.classList.add('d-none');

    document.querySelectorAll('#main-nav-tabs li, #main-nav-tabs .nav-item').forEach(el => {
        el.style.display = '';
    });

    const ls = document.getElementById('login-screen');
    ls.classList.remove('d-none');
    ls.style.opacity = '0';
    requestAnimationFrame(() => { ls.style.transition = 'opacity .28s'; ls.style.opacity = '1'; });

    const appDiv = document.getElementById('tpv-app');
    if (appDiv) appDiv.style.display = 'none';

    document.getElementById('login-error').style.display  = 'none';
    document.getElementById('login-hint').style.display   = 'none';
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('login-username').focus();
}

// ══════════════════════════════════════════════════════════════
//  CAMPANA — POLLING PEDIDOS (cada 8 s)
// ══════════════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════════════
//  SSE — Server-Sent Events (reemplaza polling de 8 s)
// ══════════════════════════════════════════════════════════════
let _prevN = -1;
let _sseConn = null;

function _iniciarPolling() {
    // Limpiar conexión anterior si existe
    if (_sseConn) { try { _sseConn.close(); } catch(e){} _sseConn = null; }
    _prevN = -1;

    // Usar SSE si el navegador lo soporta
    if (typeof EventSource !== 'undefined') {
        _sseConn = new EventSource('/api/sse');

        _sseConn.onmessage = (e) => {
            try {
                const ev = JSON.parse(e.data);
                if (ev.tipo === 'pedido_nuevo' || ev.tipo === 'pedidos_update') {
                    _actualizarBadgePedidos(ev.pendientes || 0, ev.nuevos || 0);
                } else if (ev.tipo === 'venta_nueva') {
                    // Admin recibe ventas en tiempo real
                    if (window.AUTH?.usuario?.rol === 'administrador' || window.AUTH?.usuario?.rol === 'desarrollador') {
                        _admin_renderVendedores && _admin_renderVendedores(new Date().toISOString().split('T')[0]);
                    }
                } else if (ev.tipo === 'stock_update') {
                    window._adminGeneral = null; // invalidar caché
                }
            } catch(e2) {}
        };

        _sseConn.onerror = () => {
            // Si SSE falla, fallback a polling cada 15 s
            if (_sseConn) { _sseConn.close(); _sseConn = null; }
            if (!AUTH.pollingNotif) {
                AUTH.pollingNotif = setInterval(_pollPedidos, 15050);
                _pollPedidos();
            }
        };

        // Primera carga inmediata
        _pollPedidos();
    } else {
        // Navegador sin SSE: polling clásico 8 s
        AUTH.pollingNotif = setInterval(_pollPedidos, 8000);
        _pollPedidos();
    }
}

function _actualizarBadgePedidos(n, nuevos) {
    const badge = document.getElementById('bell-badge');
    const btn   = document.querySelector('.bell-btn');
    if (badge) { badge.textContent = n; badge.classList.toggle('d-none', n === 0); }
    if (btn)   btn.classList.toggle('ring', n > 0);
    const tb = document.getElementById('tienda-pedidos-badge');
    if (tb) { tb.textContent = n; tb.classList.toggle('d-none', n === 0); }
    if (nuevos > 0) _toastPedido(nuevos);
    _prevN = n;
}

async function _pollPedidos() {
    if (!AUTH.usuario) return;
    try {
        const r    = await fetch('/api/pedidos?estado=pendiente', { signal: AbortSignal.timeout(4000) });
        if (!r.ok) return;
        const data = await r.json();
        const n    = (data.pedidos || []).length;
        const nuevos = (_prevN >= 0 && n > _prevN) ? n - _prevN : 0;
        _actualizarBadgePedidos(n, nuevos);
    } catch(e) {}
}

function _toastPedido(cant) {
    document.querySelector('.toast-ped')?.remove();
    const t = document.createElement('div');
    t.className = 'toast-ped';
    t.innerHTML = `<div style="font-size:1.7rem">🔔</div>
        <div><div class="fw-bold">${cant} pedido${cant>1?'s':''} nuevo${cant>1?'s':''}</div>
        <div class="text-muted" style="font-size:.82rem">Toca para ver</div></div>
        <button onclick="this.closest('.toast-ped').remove();document.getElementById('tienda-tab')?.click()"
                style="background:none;border:none;cursor:pointer;font-size:1.1rem;color:#94a3b8">✕</button>`;
    document.body.appendChild(t);
    setTimeout(() => t?.remove(), 7000);
}

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

function lic_abrir() {
    lic_tab('lista');
    new bootstrap.Modal(document.getElementById('modal-licencias')).show();
    _lic_cargarLista();
    _lic_cargarAdmins();
}

function lic_tab(t) {
    [['lista','lp-lista','lt-lista'],
     ['crear','lp-crear','lt-crear']].forEach(([k,p,b]) => {
        document.getElementById(p)?.classList.toggle('d-none', k!==t);
        document.getElementById(b)?.classList.toggle('active', k===t);
    });
}

function lic_actualizarDias() {
    const tipo = document.getElementById('lic-tipo')?.value;
    const dias = document.getElementById('lic-dias');
    if (!dias) return;
    const val = _LIC_DIAS[tipo];
    if (val)  { dias.value = val; dias.disabled = (tipo !== 'personalizada'); }
    else        dias.disabled = false;
}

async function _lic_cargarAdmins() {
    try {
        const res  = await fetch('/api/usuarios', { credentials:'same-origin' });
        const data = await res.json();
        const lista = document.getElementById('lic-admin-lista');
        if (!lista) return;
        const admins = (data.usuarios||[]).filter(u => u.rol==='administrador');
        lista.innerHTML = admins.length
            ? admins.map(a => `
                <button type="button" class="list-group-item list-group-item-action py-1 small"
                        onclick="document.getElementById('lic-admin-id').value='${a.usuario_id}';
                                 document.getElementById('lic-admin-lista').innerHTML=''">
                    <strong>${a.nombre}</strong>
                    <span class="text-muted ms-1">@${a.username}</span>
                    <code class="float-end text-muted" style="font-size:.68rem">${a.usuario_id}</code>
                </button>`).join('')
            : '<div class="list-group-item text-muted small">Sin administradores registrados.</div>';
    } catch(e) {}
}

async function _lic_cargarLista() {
    const body = document.getElementById('lic-lista-body');
    if (!body) return;
    body.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div></div>';
    try {
        const res  = await fetch('/api/licencias', { credentials:'same-origin' });
        const data = await res.json();
        const lics = data.licencias || [];
        if (!lics.length) {
            body.innerHTML = '<div class="text-center text-muted py-4"><i class="bi bi-key" style="font-size:2rem"></i><br>Sin licencias generadas.</div>';
            return;
        }
        const hoy = new Date().toISOString().split('T')[0];
        body.innerHTML = lics.map(l => {
            const ilim  = l.tipo === 'ilimitada';
            const venc  = !ilim && l.fecha_expira < hoy;
            const color = ilim ? '#7c3aed' : venc ? '#dc2626' : '#059669';
            const icono = ilim ? '♾️' : venc ? '❌' : '✅';
            return `
            <div class="p-2 mb-2 rounded-3"
                 style="background:${color}0f;border:1px solid ${color}33">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1 me-2">
                        <div class="fw-bold">${icono} ${l.admin_nombre}
                            <span class="badge ms-1 text-white" style="background:${color};font-size:.62rem">${l.tipo.toUpperCase()}</span>
                        </div>
                        <div class="text-muted small">
                            ${l.fecha_inicio} → ${ilim ? '∞ Ilimitada' : l.fecha_expira}
                            &nbsp;·&nbsp;<code style="font-size:.68rem">${l.licencia_id}</code>
                        </div>
                        ${l.notas ? `<div class="text-muted small fst-italic">${l.notas}</div>` : ''}
                        ${l.clave_activacion ? `
                        <div class="mt-1 pt-1" style="border-top:1px dashed ${color}44">
                            <small class="fw-semibold" style="color:${color}">Clave de activación:</small>
                            <div class="input-group input-group-sm mt-1">
                                <input type="text" class="form-control font-monospace"
                                       value="${l.clave_activacion}" readonly
                                       style="font-size:.63rem;background:#f8f9fa">
                                <button class="btn btn-outline-secondary btn-sm" title="Copiar clave"
                                        onclick="navigator.clipboard?.writeText('${l.clave_activacion}').then(()=>_toast('✅ Clave copiada al portapapeles','success'))">
                                    <i class="bi bi-clipboard-fill"></i>
                                </button>
                            </div>
                        </div>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger flex-shrink-0 ms-1" title="Revocar licencia"
                            onclick="lic_revocar('${l.licencia_id}','${l.admin_nombre.replace(/'/g,"\\'")}')">
                        <i class="bi bi-x-circle-fill"></i>
                    </button>
                </div>
            </div>`;
        }).join('');
    } catch(e) {
        body.innerHTML = '<div class="alert alert-danger">Error al cargar.</div>';
    }
}

// SHA-256 helper (disponible también en tpv_auth scope)
const _lic_sha256 = async (text) =>
    Array.from(new Uint8Array(await crypto.subtle.digest(
        'SHA-256', new TextEncoder().encode(text)
    ))).map(b => b.toString(16).padStart(2,'0')).join('');

async function lic_crear() {
    const admin_id   = document.getElementById('lic-admin-id')?.value.trim();
    const cliente_id = document.getElementById('lic-cliente-id')?.value.trim();
    const tipo       = document.getElementById('lic-tipo')?.value;
    const dias       = parseInt(document.getElementById('lic-dias')?.value) || 365;
    const notas      = document.getElementById('lic-notas')?.value.trim();

    if (!admin_id)   { _toast('Selecciona un administrador.','warning'); return; }
    if (!cliente_id) { _toast('Ingresa el ID Cliente del dispositivo del administrador.','warning');
                       document.getElementById('lic-cliente-id')?.focus(); return; }

    // Ocultar resultado previo
    const wrap = document.getElementById('lic-resultado-wrap');
    if (wrap) wrap.style.display = 'none';

    try {
        // 1. Calcular clave primero para enviarla al servidor también
        const secretKey = (typeof getSecretKey === 'function') ? getSecretKey() : 'MySuperSecretKeyForTPVApp2024';
        let claveActivacion;
        if (tipo === 'ilimitada') {
            claveActivacion = await _lic_sha256('admin' + secretKey);
        } else {
            claveActivacion = await _lic_sha256(cliente_id + secretKey + dias + 'dias');
        }

        // 2. Guardar en DB (registro histórico con clave)
        const res  = await fetch('/api/licencias/crear', {
            method:'POST', headers:{'Content-Type':'application/json'},
            credentials:'same-origin',
            body: JSON.stringify({ admin_id, tipo, dias, notas, cliente_id,
                                   clave_activacion: claveActivacion })
        });
        const data = await res.json();
        if (!res.ok || !data.ok) { _toast(data.mensaje||'Error al guardar','danger'); return; }

        // 3. Mostrar resultado
        const claveEl = document.getElementById('lic-clave-generada');
        if (claveEl) claveEl.value = claveActivacion;
        if (wrap)    wrap.style.display = '';

        _toast(`✅ Licencia ${tipo} generada para ${data.admin_nombre}`, 'success');
        _lic_cargarLista();

    } catch(e) { _toast('Error de conexión: ' + e.message, 'danger'); }
}

function lic_copiarClave() {
    const el = document.getElementById('lic-clave-generada');
    if (!el || !el.value) return;
    navigator.clipboard?.writeText(el.value).then(() => {
        _toast('✅ Clave copiada al portapapeles', 'success');
    }).catch(() => {
        el.select();
        document.execCommand('copy');
        _toast('✅ Clave copiada', 'success');
    });
}

async function lic_revocar(licencia_id, nombre) {
    if (!confirm(`¿Revocar licencia de "${nombre}"?`)) return;
    try {
        const res = await fetch(`/api/licencias/${licencia_id}`, { method:'DELETE', credentials:'same-origin' });
        if (res.ok) { _toast('Licencia revocada','success'); _lic_cargarLista(); }
        else _toast((await res.json()).mensaje||'Error','danger');
    } catch(e) {}
}

// ══════════════════════════════════════════════════════════════
//  VISTA PREVIA DE IMAGEN EN MODAL PRODUCTO
// ══════════════════════════════════════════════════════════════

function gestion_previewImagen(input) {
    const file = input?.files?.[0];
    const wrap = document.getElementById('gestion-img-preview-wrap');
    const img  = document.getElementById('gestion-img-preview');
    if (!file || !wrap || !img) return;
    const reader = new FileReader();
    reader.onload = e => {
        img.src = e.target.result;
        wrap.classList.remove('d-none');
        // Limpiar URL si se elige archivo local
        const urlInput = document.getElementById('gestion-producto-imagen-url');
        if (urlInput) urlInput.value = '';
    };
    reader.readAsDataURL(file);
}

function gestion_limpiarImagen() {
    const wrap  = document.getElementById('gestion-img-preview-wrap');
    const img   = document.getElementById('gestion-img-preview');
    const file  = document.getElementById('gestion-producto-imagen-local');
    if (wrap) wrap.classList.add('d-none');
    if (img)  img.src = '';
    if (file) file.value = '';
}

// Cuando se carga un producto a editar con imagen existente, mostrar preview
function gestion_mostrarPreviewExistente(urlImagen) {
    if (!urlImagen) return;
    const wrap = document.getElementById('gestion-img-preview-wrap');
    const img  = document.getElementById('gestion-img-preview');
    if (wrap && img) {
        img.src = urlImagen;
        wrap.classList.remove('d-none');
    }
}

// ============================================================
// LOGIN BIOMETRICO (TPVNative bridge)
// ============================================================
function auth_biometric_check() {
    try {
        var saved = JSON.parse(localStorage.getItem("tpv_user") || "{}");
        var hasCreds = saved && saved.username && saved.rol;
        if (typeof TPVNative !== "undefined" && TPVNative.isAvailable && TPVNative.isAvailable() && hasCreds) {
            var btn = document.getElementById("bio-btn");
            if (btn) { btn.style.display = ""; btn.textContent = "Huella / Rostro"; }
        }
    } catch(e) { /* biometria no disponible */ }
}

function auth_biometric() {
    var btn = document.getElementById("bio-btn");
    if (!btn) return;
    btn.disabled = true; btn.textContent = "Verificando...";
    if (typeof TPVNative === "undefined" || !TPVNative.authenticate) {
        btn.disabled = false; btn.textContent = "Huella / Rostro";
        _loginErr("Biometria no disponible en este dispositivo."); return;
    }
    window.onBiometricCallback = function(result) {
        btn.disabled = false;
        if (result && result.success) {
            var user = JSON.parse(localStorage.getItem("tpv_user") || "{}");
            if (user.rol && user.username) {
                AUTH.usuario = user;
                _auth_mostrarApp();
                return;
            }
        }
        btn.textContent = "Huella / Rostro";
        if (result) _loginErr(result.message || "Verificacion fallida. Use su contrasena.");
    };
    try {
        TPVNative.authenticate("TPV Ultra Smart", "Verificacion de identidad", "Usa tu huella o rostro para entrar");
    } catch(e) {
        btn.disabled = false; btn.textContent = "Huella / Rostro";
        _loginErr("Error de biometria: " + e.message);
    }
}

document.addEventListener("DOMContentLoaded", function() { setTimeout(auth_biometric_check, 1000); });
