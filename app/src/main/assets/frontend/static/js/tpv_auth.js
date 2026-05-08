/**
 * tpv_auth.js — TPV ULTRA SMART v5.0
 * Autenticacion: login, logout, tabs por rol, sesion cliente
 * Extraido de script_8.js
 */

// ══════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════

async function _auth_init(intentos = 0) {
    if (typeof bootstrap === 'undefined') {
        if (intentos < 30) setTimeout(() => _auth_init(intentos + 1), 150);
        return;
    }
    try {
        const ctrl = new AbortController();
        setTimeout(() => ctrl.abort(), 4000);
        const res  = await fetch('/api/auth/me', { signal: ctrl.signal, credentials: 'same-origin' });
        const data = await res.json();
        if (res.ok && data.autenticado && data.usuario) {
            AUTH.usuario = data.usuario; localStorage.setItem("tpv_rol", data.usuario.rol || "vendedor"); localStorage.setItem("tpv_user", JSON.stringify(data.usuario));
            _auth_mostrarApp();
            return;
        }
    } catch(e) {}
    auth_setModo('staff');
    // Auto-fill desarrollador username
    var uf=document.getElementById('login-username');
    if(uf)uf.value='usuario';
}

// ══════════════════════════════════════════════════════════════
//  MODO LOGIN: STAFF / CLIENTE
// ══════════════════════════════════════════════════════════════
function auth_setModo(modo) {
    const panelStaff   = document.getElementById('panel-staff');
    const panelCliente = document.getElementById('panel-cliente');
    const btnStaff     = document.getElementById('modo-staff-btn');
    const btnCliente   = document.getElementById('modo-cliente-btn');
    document.getElementById('login-error').style.display = 'none';
    if (modo === 'staff') {
        panelStaff.style.display   = '';
        panelCliente.style.display = 'none';
        btnStaff.style.background  = '#0d6efd';
        btnStaff.style.color       = 'white';
        btnCliente.style.background= 'transparent';
        btnCliente.style.color     = '#64748b';
        setTimeout(() => document.getElementById('login-username')?.focus(), 50);
    } else {
        panelStaff.style.display   = 'none';
        panelCliente.style.display = '';
        btnCliente.style.background= '#0d6efd';
        btnCliente.style.color     = 'white';
        btnStaff.style.background  = 'transparent';
        btnStaff.style.color       = '#64748b';
        setTimeout(() => document.getElementById('cli-email')?.focus(), 50);
    }
}

function auth_cliTab(tab) {
    const panelLogin = document.getElementById('cli-panel-login');
    const panelReg   = document.getElementById('cli-panel-reg');
    const btnLogin   = document.getElementById('cli-tab-login');
    const btnReg     = document.getElementById('cli-tab-reg');
    document.getElementById('login-error').style.display = 'none';
    if (tab === 'login') {
        panelLogin.style.display = ''; panelReg.style.display = 'none';
        btnLogin.style.color = '#0d6efd'; btnLogin.style.borderBottom = '2px solid #0d6efd'; btnLogin.style.fontWeight = '700';
        btnReg.style.color   = '#94a3b8'; btnReg.style.borderBottom   = '2px solid transparent'; btnReg.style.fontWeight = '600';
        setTimeout(() => document.getElementById('cli-email')?.focus(), 50);
    } else {
        panelLogin.style.display = 'none'; panelReg.style.display = '';
        btnReg.style.color   = '#0d6efd'; btnReg.style.borderBottom   = '2px solid #0d6efd'; btnReg.style.fontWeight = '700';
        btnLogin.style.color = '#94a3b8'; btnLogin.style.borderBottom = '2px solid transparent'; btnLogin.style.fontWeight = '600';
        setTimeout(() => document.getElementById('reg-nombre')?.focus(), 50);
    }
}

async function auth_loginCliente() {
    const email = document.getElementById('cli-email')?.value.trim();
    const pw    = document.getElementById('cli-pw')?.value;
    document.getElementById('login-error').style.display = 'none';
    if (!email || !pw) { _loginErr('Introduce tu email y contrasena.'); return; }
    const btnTxt = document.getElementById('cli-lbtn-txt');
    const btnSpin = document.getElementById('cli-lbtn-spin');
    if (btnTxt) btnTxt.style.display = 'none';
    if (btnSpin) btnSpin.style.display = '';
    try {
        const res  = await fetch('/api/clientes/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password:pw}), credentials:'same-origin' });
        const data = await res.json();
        if (res.ok && data.ok) {
            AUTH.usuario = { usuario_id:data.cliente.id, username:data.cliente.email, nombre:data.cliente.nombre, rol:'cliente', imagen:data.cliente.imagen||'' };
            _auth_mostrarAppCliente();
        } else { _loginErr(data.error || 'Email o contrasena incorrectos.'); document.getElementById('cli-pw').value = ''; }
    } catch(e) { _loginErr('Sin conexion con el servidor.'); document.getElementById('login-hint').style.display = ''; }
    finally { if (btnTxt) btnTxt.style.display = ''; if (btnSpin) btnSpin.style.display = 'none'; }
}

async function auth_registrarCliente() {
    const nombre   = document.getElementById('reg-nombre')?.value.trim();
    const email    = document.getElementById('reg-email')?.value.trim();
    const telefono = document.getElementById('reg-telefono')?.value.trim();
    const pw       = document.getElementById('reg-pw')?.value;
    document.getElementById('login-error').style.display = 'none';
    if (!nombre || !email || !pw) { _loginErr('Nombre, email y contrasena son obligatorios.'); return; }
    if (pw.length < 4) { _loginErr('La contrasena debe tener minimo 4 caracteres.'); return; }
    if (!email.includes('@')) { _loginErr('Email invalido.'); return; }
    const btnTxt = document.getElementById('reg-btn-txt');
    const btnSpin = document.getElementById('reg-btn-spin');
    if (btnTxt) btnTxt.style.display = 'none';
    if (btnSpin) btnSpin.style.display = '';
    try {
        const res  = await fetch('/api/clientes/registrar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({nombre,email,password:pw,telefono}), credentials:'same-origin' });
        const data = await res.json();
        if (res.ok && data.ok) { document.getElementById('cli-email').value = email; document.getElementById('cli-pw').value = pw; await auth_loginCliente(); }
        else { _loginErr(data.error || 'No se pudo crear la cuenta.'); }
    } catch(e) { _loginErr('Sin conexion con el servidor.'); }
    finally { if (btnTxt) btnTxt.style.display = ''; if (btnSpin) btnSpin.style.display = 'none'; }
}

function _auth_mostrarAppCliente() {
    const ls = document.getElementById('login-screen');
    if (ls) { ls.style.opacity = '0'; setTimeout(() => ls.classList.add('d-none'), 290); }
    const u  = AUTH.usuario;
    const ub = document.getElementById('user-bar');
    if (ub) ub.classList.remove('d-none');
    const icon  = document.getElementById('ub-icon');
    const name  = document.getElementById('ub-name');
    const badge = document.getElementById('ub-badge');
    if (icon)  { icon.className = 'bi bi-person-circle'; icon.style.color = '#059669'; }
    if (name)  name.textContent = u.nombre;
    if (badge) { badge.textContent = 'Cliente'; badge.style.cssText = 'background:#d1fae5;color:#059669;border:1px solid #6ee7b7'; }
    document.getElementById('btn-usuarios')?.classList.add('d-none');
    document.getElementById('btn-licencias')?.classList.add('d-none');
    document.getElementById('notif-bell-wrap')?.classList.add('d-none');
    const appDiv = document.getElementById('tpv-app');
    if (appDiv) appDiv.style.display = '';
    function _lanzarCliente() {
        if (typeof bootstrap === 'undefined') { setTimeout(_lanzarCliente, 100); return; }
        if (typeof loadState === 'function') {
            loadState().then(() => {
                try { if (typeof initializeUI === 'function') initializeUI(); } catch(e) { dbg && dbg('❌ initializeUI CRASH (cliente): '+e.message); }
                setTimeout(_auth_aplicarTabsCliente, 300);
            }).catch(e => {
                dbg && dbg('❌ loadState CRASH (cliente): '+e.message);
                setTimeout(_auth_aplicarTabsCliente, 300);
            });
        } else {
            try { if (typeof initializeUI === 'function') initializeUI(); } catch(e) {}
            setTimeout(_auth_aplicarTabsCliente, 300);
        }
    }
    _lanzarCliente();
}

function _auth_aplicarTabsCliente() {
    // Aplicar clase de rol al body
    const rol = AUTH.usuario?.rol || 'cliente';
    document.body.className = document.body.className
        .replace(/\brol-\S+/g, '').trim();
    document.body.classList.add(`rol-${rol}`);

    // Usar ACCESO_TABS con rol 'cliente' — misma lógica que _auth_aplicarTabs
    Object.entries(ACCESO_TABS).forEach(([tabId, roles]) => {
        const tab = document.getElementById(tabId);
        if (!tab) return;
        const li    = tab.closest('li');
        const puede = roles.includes(rol);
        if (li) li.style.display = puede ? '' : 'none';
        else    tab.style.display = puede ? '' : 'none';
    });
    document.querySelectorAll('#main-nav-tabs .nav-item.dropdown').forEach(dd => {
        const items = dd.querySelectorAll('li');
        const hayVisible = [...items].some(li => li.style.display !== 'none' && !li.querySelector('hr') && li.querySelector('a,button'));
        dd.style.display = hayVisible ? '' : 'none';
    });
    setTimeout(() => document.getElementById('tienda-tab')?.click(), 350);
}


// ══════════════════════════════════════════════════════════════
//  TOGGLE CONTRASEÑA (ojito)
// ══════════════════════════════════════════════════════════════
function auth_togglePw(btn) {
    const input = btn.closest('.pw-wrap')?.querySelector('input') ||
                  document.getElementById('login-password');
    const icon  = btn.querySelector('i');
    if (!input || !icon) return;
    const mostrar  = input.type === 'password';
    input.type     = mostrar ? 'text' : 'password';
    icon.className = mostrar ? 'bi bi-eye' : 'bi bi-eye-slash';
}

// ══════════════════════════════════════════════════════════════
//  LOGIN
// ══════════════════════════════════════════════════════════════
async function auth_login() {
    const usr = document.getElementById('login-username')?.value.trim();
    const pw  = document.getElementById('login-password')?.value;
    document.getElementById('login-error').style.display  = 'none';
    document.getElementById('login-hint').style.display   = 'none';

    if (!usr || !pw) { _loginErr('Introduce usuario y contraseña.'); return; }

    document.getElementById('login-btn').disabled = true;
    document.getElementById('lbtn-txt').style.display  = 'none';
    document.getElementById('lbtn-spin').style.display = '';

    try {
        const ctrl = new AbortController();
        setTimeout(() => ctrl.abort(), 10000);
        const res  = await fetch('/api/auth/login', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ username:usr, password:pw }),
            signal: ctrl.signal, credentials:'same-origin'
        });
        const data = await res.json();
        if (res.ok && data.ok) {
            AUTH.usuario = data.usuario; localStorage.setItem("tpv_rol", data.usuario.rol || "vendedor"); localStorage.setItem("tpv_user", JSON.stringify(data.usuario));
            _auth_mostrarApp();
        } else {
            _loginErr(data.error || 'Usuario o contraseña incorrectos.');
            document.getElementById('login-password').value = '';
            document.getElementById('login-password').focus();
        }
    } catch(e) {
        _loginErr(e.name === 'AbortError' ? 'El servidor tardó demasiado.' : 'Sin conexión con el servidor.');
        document.getElementById('login-hint').style.display = '';
    } finally {
        document.getElementById('login-btn').disabled = false;
        document.getElementById('lbtn-txt').style.display  = '';
        document.getElementById('lbtn-spin').style.display = 'none';
    }
}

function _loginErr(msg) {
    const d = document.getElementById('login-error');
    const m = document.getElementById('login-error-msg');
    if (d && m) { m.textContent = msg; d.style.display = 'flex'; }
}

// ══════════════════════════════════════════════════════════════
//  MOSTRAR APP TRAS LOGIN
// ══════════════════════════════════════════════════════════════
function _auth_mostrarApp() {
    dbg('🔑 _auth_mostrarApp() - usuario: '+(AUTH.usuario?.username||'?')+' rol: '+(AUTH.usuario?.rol||'?'));
    var _x=document.getElementById('login-screen-static');if(_x)_x.style.display='none';
    const ls = document.getElementById('login-screen');
    if(ls){ls.style.transition='opacity .28s';ls.style.opacity='0';setTimeout(()=>ls.classList.add('d-none'),290);}
    dbg('📋 login-screen: '+(ls?'OK':'null')+' user-bar: '+(document.getElementById('user-bar')?'OK':'null'));

    const u  = AUTH.usuario;
    const ri = ROL_INFO[u.rol] || { color:'#6c757d', icono:'bi-person', label:u.rol };
    const ub = document.getElementById('user-bar');
    if(ub) ub.classList.remove('d-none');

    const icon  = document.getElementById('ub-icon');
    const name  = document.getElementById('ub-name');
    const badge = document.getElementById('ub-badge');
    if (icon)  { icon.className = `bi ${ri.icono}`; icon.style.color = ri.color; }
    if (name)  name.textContent = u.nombre;
    if (badge) {
        badge.textContent = ri.label;
        badge.style.cssText = `background:${ri.color}28;color:${ri.color};border:1px solid ${ri.color}55`;
    }

    // Botones según rol
    const btnU = document.getElementById('btn-usuarios');
    const btnL = document.getElementById('btn-licencias');
    const btnD = document.getElementById('btn-debug-toggle');
    // Usuarios: solo admin y dev ven la gestión completa
    if (btnU) btnU.classList.toggle('d-none', !['desarrollador','administrador'].includes(u.rol));
    // Licencias: solo desarrollador
    if (btnL) btnL.classList.toggle('d-none', u.rol !== 'desarrollador');
    // Debug toggle: solo desarrollador
    if (btnD) btnD.classList.toggle('d-none', u.rol !== 'desarrollador');

    // Campana
    document.getElementById('notif-bell-wrap')?.classList.remove('d-none');
    _iniciarPolling();

    // Mostrar el container principal de la app
    const appDiv = document.getElementById('tpv-app');
    if (appDiv) appDiv.style.display = '';

    // Cargar app y aplicar permisos
    if (typeof loadState === 'function') {
        loadState().then(() => {
            dbg('✅ loadState completó — llamando initializeUI...');
            try {
                if (typeof initializeUI === 'function') initializeUI();
                dbg('✅ initializeUI OK');
            } catch(e) { dbg('❌ initializeUI CRASH: '+e.message); }
            try {
                conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
                dbg('✅ updateUITranslations OK');
            } catch(e) { dbg('❌ updateUITranslations CRASH: '+e.message); }
            setTimeout(function() {
                _auth_aplicarTabs();
                // Debugger se activa dentro de _auth_aplicarTabs para desarrollador
            }, 300);
        }).catch(e => dbg('❌ loadState CRASH: '+e.message));
    }
}

// ══════════════════════════════════════════════════════════════
//  CONTROL DE TABS POR ROL
// ══════════════════════════════════════════════════════════════
function _auth_aplicarTabs() {
    const rol = AUTH.usuario?.rol;
    if (!rol) return;

    // Aplicar clase de rol al body para CSS role-based visibility
    document.body.className = document.body.className
        .replace(/\brol-\S+/g, '').trim();
    document.body.classList.add(`rol-${rol}`);

    // Auto-activar debug panel para desarrollador
    if (rol === 'desarrollador') {
        setTimeout(function(){
            try {
                // Asegura que el panel existe en el DOM
                var p = document.getElementById('dbg-v2');
                if (p) p.style.display = '';
                // Resetea estado interno y reactiva
                if (window._DBG) window._DBG.activo = false;
                if (typeof window.tpvDebugger === 'object' && window.tpvDebugger.activar) {
                    window.tpvDebugger.activar();
                } else if (typeof window._dbg_mostrar === 'function') {
                    window._dbg_mostrar();
                }
            } catch(e) {}
        }, 600);
    }

    // Aplicar visibilidad a cada tab
    Object.entries(ACCESO_TABS).forEach(([tabId, roles]) => {
        const tab = document.getElementById(tabId);
        if (!tab) return;
        const li    = tab.closest('li');
        const puede = roles.includes(rol);
        if (li) li.style.display = puede ? '' : 'none';
        else    tab.style.display = puede ? '' : 'none';
    });

    // Ocultar menús dropdown que quedaron completamente vacíos
    document.querySelectorAll('#main-nav-tabs .nav-item.dropdown').forEach(dd => {
        const items = dd.querySelectorAll('li');
        const hayVisible = [...items].some(li =>
            li.style.display !== 'none' && !li.querySelector('hr') && li.querySelector('a,button')
        );
        dd.style.display = hayVisible ? '' : 'none';
    });

    // Si la tab activa quedó oculta → ir al tab por defecto según rol
    const activePane = document.querySelector('.tab-pane.active.show');
    if (activePane) {
        const tabId  = activePane.id.replace('-pane','');
        const tabBtn = document.getElementById(tabId);
        const li     = tabBtn?.closest('li');
        if (li && li.style.display === 'none') {
            // Vendedor → va directo a su inventario
            const defaultTab = rol === 'vendedor'
                ? 'inv-inventario-tab'
                : 'tpv-caja-tab';
            document.getElementById(defaultTab)?.click();
        }
    }
    // Vendedor: asegurarse de que su tab por defecto sea Inventario
    if (rol === 'vendedor') {
        setTimeout(() => document.getElementById('inv-inventario-tab')?.click(), 350);
    }

    // Sección "Nombre del Sistema TPV": solo admin/dev
    const cfgTpvName = document.getElementById('cfg-tpv-name-wrap');
    if (cfgTpvName) cfgTpvName.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // Sección "Datos de la Tienda" en Configuración: solo admin/dev
    const cfgTienda = document.getElementById('cfg-tienda-wrap');
    if (cfgTienda) cfgTienda.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // Sección "Mantenimiento" en Configuración: solo admin/dev
    const cfgMant = document.getElementById('cfg-mant-wrap');
    if (cfgMant) cfgMant.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // Configuraciones especiales por rol
    priv_mostrarMenu(rol);  // v6.11.0: mostrar menú de privilegios
    if (rol === 'vendedor')                                 _setup_vendedor();
    if (['administrador','desarrollador'].includes(rol))    _setup_admin_inventario();
    if (['supervisor'].includes(rol))                       _setup_supervisor_inventario();
    if (['administrador','desarrollador'].includes(rol))    cfg_cargarTienda();

    console.log(`[Auth] Tabs aplicados — rol: ${rol}`);
}

// ══════════════════════════════════════════════════════════════
//  SETUP INVENTARIO — VENDEDOR
//  Reemplaza el contenido de inv-inventario-tab-pane con
//  la vista de su lista diaria + columna de conteo final
// ══════════════════════════════════════════════════════════════
function _setup_vendedor() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane) return;

