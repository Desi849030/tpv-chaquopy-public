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
            AUTH.usuario = data.usuario; tpvStorage.setItem("tpv_rol", data.usuario.rol || "vendedor"); tpvStorage.setJSON("tpv_user", data.usuario);
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
function auth_biometric_check() {
    try {
        var saved = JSON.parse(tpvStorage.getItem("tpv_user") || "{}");
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
            var user = JSON.parse(tpvStorage.getItem("tpv_user") || "{}");
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

