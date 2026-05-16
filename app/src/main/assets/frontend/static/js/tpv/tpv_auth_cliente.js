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
    if(uf)
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

