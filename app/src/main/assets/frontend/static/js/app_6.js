/**
 * tpv-auth.js — TPV ULTRA SMART v5.0
 * Autenticación + Control de pestañas por rol
 *
 * JERARQUÍA DE ROLES Y ACCESO:
 * ────────────────────────────────────────────────────────
 * DESARROLLADOR → todo sin límites + licencias
 * ADMINISTRADOR → su tienda completa (NO licencias, NO configurar entorno)
 *   Catálogo: Vista Principal, Gestión Productos, Categorías,
 *             Inventario (Almacén + Vendedores), QR, Importar/Exportar
 *   Ventas:   Ventas Hoy, Nomenclador, Exportar Excel
 *   Registros: Historial, Copias de Seguridad
 *   Tienda, Configuración (Apariencia), Herramientas
 *   Usuarios: crea Supervisor y Vendedor
 *
 * SUPERVISOR → solo lectura/reportes
 *   Catálogo: Vista Principal
 *   Ventas:   Ventas Hoy, Nomenclador, Exportar Excel
 *   Registros: Historial
 *   Tienda, Configuración (Apariencia)
 *   Usuarios: solo ve lista + cambia su contraseña
 *
 * VENDEDOR → solo vender
 *   Catálogo: Vista Principal
 *   Orden Actual
 *   Ventas: Ventas Hoy (solo las suyas)
 *   Mi Inventario (su lista diaria con conteo final)
 *   Tienda
 *   Configuración (Apariencia)
 * ────────────────────────────────────────────────────────
 */

window.AUTH = { usuario: null, pollingNotif: null };


// ══════════════════════════════════════════════════════════════
//  v8.0 — LIMPIEZA ATOMICA DE ESTADO DE USUARIO
// ══════════════════════════════════════════════════════════════
function _tpv_limpiarEstadoUsuarioAnterior() {
    try {
        // 1. Variables globales de identidad
        window.TPV_ROL = null;
        window.TPV_USER = null;
        window.TPV_USER_ID = null;
        window.TPV_AUTH = false;

        // 2. Chat: limpiar UI completa
        window._tpvChatSaludado = false;
        window._tpvChatInteract = false;
        var chatBox = document.getElementById('chat-box');
        if (chatBox) chatBox.style.display = 'none';
        var chatMsgs = document.getElementById('chat-msgs');
        if (chatMsgs) chatMsgs.innerHTML = '';
        var chatSug = document.getElementById('chat-sug');
        if (chatSug) chatSug.innerHTML = '';
        var chatSub = document.getElementById('chat-head-sub');
        if (chatSub) chatSub.textContent = '';

        // 3. sessionStorage completo
        try { sessionStorage.clear(); } catch(e) {}

        // 4. localStorage especifico del usuario
        try {
            var claves = [];
            for (var i = 0; i < localStorage.length; i++) {
                var k = localStorage.key(i);
                if (k && (k.indexOf('chat_history_') === 0 ||
                          k.indexOf('carrito_') === 0 ||
                          k.indexOf('user_pref_') === 0 ||
                          k === 'ultimo_usuario' ||
                          k === 'tpv_auth_token')) {
                    claves.push(k);
                }
            }
            claves.forEach(function(k) { localStorage.removeItem(k); });
        } catch(e) {}

        // 5. tpvState
        if (window.tpvState) {
            try {
                tpvState.usuarioActual = null;
                if (Array.isArray(tpvState.carrito)) tpvState.carrito = [];
            } catch(e) {}
        }

        // 6. Notificar a modulos reactivos
        try {
            window.dispatchEvent(new CustomEvent('tpv_role_changed', {detail: {usuario: null}}));
        } catch(e) {}

        console.log('[TPV v8] Estado usuario anterior limpiado');
    } catch (e) {
        console.warn('[TPV v8] Error al limpiar estado:', e);
    }
}
window._tpv_limpiarEstadoUsuarioAnterior = _tpv_limpiarEstadoUsuarioAnterior;

const ROL_INFO = {
    desarrollador: { color:'#7c3aed', icono:'bi-code-slash',    label:'Desarrollador' },
    administrador: { color:'#4f46e5', icono:'bi-shield-fill',   label:'Administrador' },
    supervisor:    { color:'#0891b2', icono:'bi-eye-fill',       label:'Supervisor'    },
    vendedor:      { color:'#059669', icono:'bi-bag-check-fill', label:'Vendedor'      }
};

// Qué tabs ve cada rol. Todos los no listados se ocultan.
// 'todos' = todos los roles
const ACCESO_TABS = {
    // ── PRODUCTOS / GESTIÓN ───────────────────────────────────────────────────
    'tpv-caja-tab':           ['desarrollador','administrador','supervisor','vendedor','cliente'],
    'dashboard-tab':          ['desarrollador','administrador','supervisor'],
    'gestion-productos-tab':  ['desarrollador','administrador'],
    'gestion-categorias-tab': ['desarrollador','administrador'],
    'importar-exportar-tab':  ['desarrollador','administrador'],  // redirige a herramientas
    'cliente-qr-tab':         ['desarrollador','administrador'],
    // ── INVENTARIO ───────────────────────────────────────────────────────────
    'inv-inventario-tab':     ['desarrollador','administrador','vendedor','supervisor'],
    // ── VENTAS ───────────────────────────────────────────────────────────────
    'orden-actual-tab':       ['desarrollador','administrador','supervisor','vendedor','cliente'],
    'ventas-hoy-tab':         ['desarrollador','administrador','supervisor','vendedor'],
    'exportar-ventas-tab':    ['desarrollador','administrador','supervisor'],
    // ── REGISTROS ────────────────────────────────────────────────────────────
    'registros-tab':          ['desarrollador','administrador','supervisor'],
    'copias-seguridad-tab':   ['desarrollador','administrador'],  // redirige a herramientas
    // ── TIENDA ───────────────────────────────────────────────────────────────
    'tienda-tab':             ['desarrollador','administrador','supervisor','vendedor','cliente'],
    // ── CONFIGURACIÓN ────────────────────────────────────────────────────────
    'conf-config-tab':        ['desarrollador','administrador','supervisor','vendedor'],
    'nom-nomenclador-tab':    ['desarrollador','administrador','supervisor'],
    'herramientas-tab':       ['desarrollador','administrador'],
    'licencias-tab':          ['desarrollador'],
};

// ══════════════════════════════════════════════════════════════
//  CSS
// ══════════════════════════════════════════════════════════════
const _css = document.createElement('style');
_css.textContent = `
#login-screen {
    position:fixed;inset:0;z-index:9999;
    background:linear-gradient(135deg,#1e1b4b 0%,#4338ca 55%,#6366f1 100%);
    display:flex;align-items:center;justify-content:center;
    padding:1rem;overflow-y:auto;
}
.login-card {
    background:white;border-radius:1.5rem;
    padding:2.5rem 2rem;width:100%;max-width:420px;
    box-shadow:0 25px 60px rgba(0,0,0,.45);
    animation:loginIn .35s ease;
}
@keyframes loginIn{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:translateY(0)}}
.login-logo{
    width:72px;height:72px;border-radius:50%;
    background:linear-gradient(135deg,#4f46e5,#6366f1);
    color:white;font-size:2rem;
    display:flex;align-items:center;justify-content:center;
    margin:0 auto 1rem;box-shadow:0 8px 20px rgba(79,70,229,.38);
}
.login-title{text-align:center;font-weight:800;color:#1e293b;margin:0;font-size:1.6rem}
.login-sub{text-align:center;color:#64748b;font-size:.88rem;margin-bottom:1.5rem}
.login-error{
    background:#fee2e2;border:1px solid #fca5a5;color:#dc2626;
    border-radius:.75rem;padding:.8rem 1rem;margin-bottom:1rem;font-size:.88rem;
    display:flex;align-items:flex-start;gap:.5rem;
}
.login-error i{flex-shrink:0;margin-top:2px}
.login-hint{
    background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;
    border-radius:.75rem;padding:.8rem 1rem;margin-bottom:1rem;font-size:.83rem;
}
.login-hint code{background:#dbeafe;padding:.1rem .3rem;border-radius:.3rem;font-size:.82rem}
.login-field{margin-bottom:1rem}
.login-field label{display:block;font-weight:600;color:#374151;margin-bottom:.4rem;font-size:.88rem}
.pw-wrap{position:relative}
.login-input{
    width:100%;padding:.75rem 1rem;border-radius:.75rem;
    border:2px solid #e2e8f0;font-size:1rem;outline:none;
    transition:border-color .2s;box-sizing:border-box;background:white;
}
.login-input:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.18)}
.pw-eye{
    position:absolute;right:.75rem;top:50%;transform:translateY(-50%);
    background:none;border:none;cursor:pointer;color:#94a3b8;
    padding:.3rem;font-size:1rem;line-height:1;transition:color .15s;
}
.pw-eye:hover{color:#4f46e5}
.login-btn{
    width:100%;padding:.85rem;border:none;border-radius:.75rem;
    background:linear-gradient(135deg,#4f46e5,#6366f1);color:white;
    font-size:1rem;font-weight:700;cursor:pointer;margin-top:.25rem;
    transition:transform .15s,box-shadow .15s;
    box-shadow:0 4px 14px rgba(79,70,229,.38);
}
.login-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 6px 20px rgba(79,70,229,.48)}
.login-btn:disabled{opacity:.65;cursor:not-allowed}
.login-footer{text-align:center;color:#94a3b8;font-size:.78rem;margin-top:1.25rem}
/* Barra usuario */
#user-bar{
    background:linear-gradient(90deg,#1e293b,#0f172a);
    color:white;padding:.45rem 1rem;
    position:sticky;top:0;z-index:1000;
}
.ub-inner{display:flex;justify-content:space-between;align-items:center;max-width:1200px;margin:auto;gap:.5rem}
.ub-info{display:flex;align-items:center;gap:.4rem;font-size:.88rem;min-width:0;flex:1}
.ub-badge{padding:.18rem .55rem;border-radius:999px;font-size:.7rem;font-weight:700;text-transform:uppercase;flex-shrink:0}
.ub-actions{display:flex;gap:.4rem;flex-shrink:0}
.ub-btn{
    background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);
    color:white;padding:.3rem .65rem;border-radius:.5rem;
    font-size:.78rem;cursor:pointer;transition:background .15s;white-space:nowrap;
}
.ub-btn:hover{background:rgba(255,255,255,.22)}
.ub-btn.out:hover{background:rgba(220,53,69,.55);border-color:#dc3545}
/* Campana */
#notif-bell-wrap{display:flex;align-items:center}
.bell-btn{
    width:36px;height:36px;padding:0;
    display:flex;align-items:center;justify-content:center;
    border-radius:50%!important;font-size:1rem;
}
.bell-btn.ring{
    animation:bRing .5s ease infinite alternate;
    background:#ffc107!important;color:#1e293b!important;border-color:#ffc107!important;
}
@keyframes bRing{from{transform:rotate(-14deg)}to{transform:rotate(14deg)}}
/* Toast pedido */
.toast-ped{
    position:fixed;bottom:1rem;right:1rem;z-index:10000;
    background:white;border-radius:1rem;padding:.9rem 1.1rem;
    box-shadow:0 8px 28px rgba(0,0,0,.18);border-left:4px solid #f59e0b;
    display:flex;align-items:center;gap:.65rem;max-width:280px;
    animation:slideR .28s ease;
}
@keyframes slideR{from{opacity:0;transform:translateX(90px)}to{opacity:1;transform:translateX(0)}}
/* Modal usuarios */
.u-card{
    display:flex;align-items:center;justify-content:space-between;
    padding:.7rem .9rem;border-radius:.7rem;margin-bottom:.45rem;
    background:#f8fafc;border:1px solid #e2e8f0;gap:.5rem;
}
.u-pill{padding:.18rem .55rem;border-radius:999px;font-size:.7rem;font-weight:700;text-transform:uppercase}
`;
document.head.appendChild(_css);

// ══════════════════════════════════════════════════════════════
//  HTML INYECTADO
// ══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {

        // Pantalla login
    const ls = document.createElement('div');
    ls.id = 'login-screen';
    ls.innerHTML = `
    <div class="login-card" style="max-width:440px">
        <div class="login-logo"><i class="bi bi-shop-window"></i></div>
        <h2 class="login-title">TPV Ultra Smart</h2>
        <div style="display:flex;background:#f1f5f9;border-radius:.75rem;padding:4px;margin-bottom:1.2rem">
            <button id="modo-staff-btn" onclick="auth_setModo('staff')"
                style="flex:1;padding:.5rem;border:none;border-radius:.6rem;font-weight:600;font-size:.88rem;cursor:pointer;background:#4f46e5;color:white">
                <i class="bi bi-person-badge me-1"></i>Personal
            </button>
            <button id="modo-cliente-btn" onclick="auth_setModo('cliente')"
                style="flex:1;padding:.5rem;border:none;border-radius:.6rem;font-weight:600;font-size:.88rem;cursor:pointer;background:transparent;color:#64748b">
                <i class="bi bi-bag-heart me-1"></i>Cliente
            </button>
        </div>
        <div id="login-error" class="login-error" style="display:none">
            <i class="bi bi-exclamation-triangle-fill"></i>
            <div id="login-error-msg"></div>
        </div>
        <div id="login-hint" class="login-hint" style="display:none">
            <strong>Flask no responde.</strong> Abre Pydroid3 y ejecuta:<br>
            <code>python app.py</code>
        </div>
        <div id="panel-staff" style="display:none">
            <p class="login-sub" style="margin-bottom:1rem">Acceso para empleados</p>
            <div class="login-field">
                <label><i class="bi bi-person me-1"></i>Usuario</label>
                <input id="login-username" class="login-input" type="text" placeholder="Usuario" autocomplete="username">
            </div>
            <div class="login-field">
                <label><i class="bi bi-lock me-1"></i>Contrasena</label>
                <div class="pw-wrap">
                    <input id="login-password" class="login-input" type="password" placeholder="••••••••"
                           autocomplete="current-password" style="padding-right:3rem">
                    <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1">
                        <i class="bi bi-eye-slash"></i>
                    </button>
                </div>
            </div>
            <button id="login-btn" class="login-btn" onclick="auth_login()">
                <span id="lbtn-txt"><i class="bi bi-box-arrow-in-right me-2"></i>Entrar</span>
                <span id="lbtn-spin" style="display:none"><span class="spinner-border spinner-border-sm me-2"></span>Verificando...</span>
            </button>
            <button id="login-bio-btn" class="login-btn" style="display:none;margin-top:.6rem;background:linear-gradient(135deg,#0ea5e9,#06b6d4)" onclick="auth_loginBiometrico()">
                <i class="bi bi-fingerprint me-2"></i>Entrar con huella / rostro
            </button>
            <div class="login-footer"><i class="bi bi-shield-lock me-1"></i>Acceso restringido al personal</div>
        </div>
        <div id="panel-cliente" style="display:none">
            <div style="display:flex;border-bottom:2px solid #e2e8f0;margin-bottom:1rem">
                <button id="cli-tab-login" onclick="auth_cliTab('login')"
                    style="flex:1;padding:.55rem;border:none;background:none;font-weight:700;font-size:.88rem;cursor:pointer;color:#4f46e5;border-bottom:2px solid #4f46e5;margin-bottom:-2px">
                    <i class="bi bi-box-arrow-in-right me-1"></i>Iniciar sesion
                </button>
                <button id="cli-tab-reg" onclick="auth_cliTab('registro')"
                    style="flex:1;padding:.55rem;border:none;background:none;font-weight:600;font-size:.88rem;cursor:pointer;color:#94a3b8;border-bottom:2px solid transparent;margin-bottom:-2px">
                    <i class="bi bi-person-plus me-1"></i>Registrarse
                </button>
            </div>
            <div id="cli-panel-login">
                <div class="login-field">
                    <label><i class="bi bi-envelope me-1"></i>Email</label>
                    <input id="cli-email" class="login-input" type="email" placeholder="tu@email.com" autocomplete="email">
                </div>
                <div class="login-field">
                    <label><i class="bi bi-lock me-1"></i>Contrasena</label>
                    <div class="pw-wrap">
                        <input id="cli-pw" class="login-input" type="password" placeholder="••••••••" style="padding-right:3rem">
                        <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1">
                            <i class="bi bi-eye-slash"></i>
                        </button>
                    </div>
                </div>
                <button class="login-btn" onclick="auth_loginCliente()">
                    <span id="cli-lbtn-txt"><i class="bi bi-bag-heart me-2"></i>Entrar a la tienda</span>
                    <span id="cli-lbtn-spin" style="display:none"><span class="spinner-border spinner-border-sm me-2"></span>Verificando...</span>
                </button>
                <div class="login-footer" style="margin-top:.8rem">
                    Sin cuenta: <a href="#" onclick="auth_cliTab('registro');return false" style="color:#4f46e5;font-weight:600">Registrate gratis</a>
                </div>
            </div>
            <div id="cli-panel-reg" style="display:none">
                <div class="login-field">
                    <label><i class="bi bi-person me-1"></i>Nombre completo</label>
                    <input id="reg-nombre" class="login-input" type="text" placeholder="Tu nombre">
                </div>
                <div class="login-field">
                    <label><i class="bi bi-envelope me-1"></i>Email</label>
                    <input id="reg-email" class="login-input" type="email" placeholder="tu@email.com">
                </div>
                <div class="login-field">
                    <label>Telefono (opcional)</label>
                    <input id="reg-telefono" class="login-input" type="tel" placeholder="+1 555 000 0000">
                </div>
                <div class="login-field">
                    <label><i class="bi bi-lock me-1"></i>Contrasena</label>
                    <div class="pw-wrap">
                        <input id="reg-pw" class="login-input" type="password" placeholder="Minimo 4 caracteres" style="padding-right:3rem">
                        <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1">
                            <i class="bi bi-eye-slash"></i>
                        </button>
                    </div>
                </div>
                <button class="login-btn" onclick="auth_registrarCliente()"
                    style="background:linear-gradient(135deg,#059669,#047857)">
                    <span id="reg-btn-txt"><i class="bi bi-person-check me-2"></i>Crear cuenta</span>
                    <span id="reg-btn-spin" style="display:none"><span class="spinner-border spinner-border-sm me-2"></span>Creando cuenta...</span>
                </button>
                <div class="login-footer" style="margin-top:.8rem">
                    Ya tienes cuenta: <a href="#" onclick="auth_cliTab('login');return false" style="color:#4f46e5;font-weight:600">Inicia sesion</a>
                </div>
            </div>
        </div>
    </div>`;
    document.body.insertBefore(ls, document.body.firstChild);

    // Barra de usuario
    const ub = document.createElement('div');
    ub.id = 'user-bar';
    ub.className = 'd-none';
    ub.innerHTML = `
    <div class="ub-inner">
        <div class="ub-info">
            <i id="ub-icon" class="bi bi-person-circle"></i>
            <span id="ub-name" class="fw-semibold text-truncate">—</span>
            <span id="ub-badge" class="ub-badge">—</span>
        </div>
        <div class="ub-actions">
            <button id="btn-licencias" class="ub-btn d-none" onclick="lic_abrir()"
                    style="background:rgba(124,58,237,.25);border-color:rgba(124,58,237,.5)">
                <i class="bi bi-key-fill me-1"></i><span class="d-none d-sm-inline">Licencias</span>
            </button>
            <button id="btn-usuarios" class="ub-btn d-none" onclick="auth_abrirUsuarios()">
                <i class="bi bi-people-fill me-1"></i><span class="d-none d-sm-inline">Usuarios</span>
            </button>
            <button id="btn-debug-toggle" class="ub-btn d-none"
                    onclick="if(window.tpvDebugger)tpvDebugger.activar();else window._dbg_mostrar()"
                    style="background:rgba(34,197,94,.15);border-color:rgba(34,197,94,.4)"
                    title="Mostrar/Ocultar panel de debug">
                <i class="bi bi-bug-fill me-1"></i><span class="d-none d-sm-inline" id="btn-debug-label">Debug</span>
            </button>
            <button class="ub-btn out" onclick="auth_logout()">
                <i class="bi bi-box-arrow-right me-1"></i><span class="d-none d-sm-inline">Salir</span>
            </button>
        </div>
    </div>`;
    document.body.insertBefore(ub, document.body.firstChild);

    // Campana de notificaciones
    const ns = document.getElementById('network-status');
    if (ns) {
        const bw = document.createElement('div');
        bw.id = 'notif-bell-wrap';
        bw.className = 'me-2 d-none';
        bw.innerHTML = `
        <button class="btn btn-sm btn-outline-warning bell-btn position-relative"
                onclick="auth_verNotificaciones()" title="Pedidos pendientes">
            <i class="bi bi-bell-fill"></i>
            <span id="bell-badge"
                  class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger d-none"
                  style="font-size:.58rem">0</span>
        </button>`;
        ns.parentNode.insertBefore(bw, ns);
    }

    // Modales
    document.body.insertAdjacentHTML('beforeend', `

    <!-- Modal Gestión Usuarios -->
    <div class="modal fade" id="modal-usuarios" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header text-white fw-bold"
               style="background:linear-gradient(135deg,#4f46e5,#6366f1)">
            <span><i class="bi bi-people-fill me-2"></i>Gestión de Usuarios</span>
            <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-0">
            <ul class="nav nav-tabs px-3 pt-2">
              <li class="nav-item"><button class="nav-link active" id="ut-lista" onclick="auth_tab('lista')"><i class="bi bi-list-ul me-1"></i>Lista</button></li>
              <li class="nav-item" id="ut-crear-li"><button class="nav-link" id="ut-crear" onclick="auth_tab('crear')"><i class="bi bi-person-plus-fill me-1"></i>Crear</button></li>
              <li class="nav-item"><button class="nav-link" id="ut-pw" onclick="auth_tab('pw')"><i class="bi bi-key-fill me-1"></i>Mi Contraseña</button></li>
            </ul>
            <div id="up-lista" class="p-3">
              <div id="u-lista-body" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm me-2"></div>Cargando...
              </div>
            </div>
            <div id="up-crear" class="p-3 d-none">
              <div class="row g-3">
                <div class="col-12 col-sm-6">
                  <label class="form-label fw-semibold">Nombre completo</label>
                  <input id="nu-nombre" class="form-control" placeholder="Ej: Juan Pérez">
                </div>
                <div class="col-12 col-sm-6">
                  <label class="form-label fw-semibold">Usuario (login)</label>
                  <input id="nu-user" class="form-control" placeholder="ej: juan.perez" autocomplete="off">
                </div>
                <div class="col-12 col-sm-6">
                  <label class="form-label fw-semibold">Contraseña</label>
                  <div class="pw-wrap">
                    <input id="nu-pw" class="form-control" type="password" placeholder="Mínimo 4 caracteres"
                           style="padding-right:2.5rem" autocomplete="new-password">
                    <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1">
                      <i class="bi bi-eye-slash"></i>
                    </button>
                  </div>
                </div>
                <div class="col-12 col-sm-6">
                  <label class="form-label fw-semibold">Rol</label>
                  <select id="nu-rol" class="form-select">
                    <option value="">— Seleccionar —</option>
                  </select>
                </div>
                <div class="col-12">
                  <button class="btn btn-primary w-100 fw-bold" onclick="auth_crearUsuario()">
                    <i class="bi bi-person-plus-fill me-2"></i>Crear Usuario
                  </button>
                </div>
              </div>
            </div>
            <div id="up-pw" class="p-3 d-none">
              <div class="row g-3" style="max-width:360px;margin:auto">
                <div class="col-12">
                  <label class="form-label fw-semibold">Contraseña actual</label>
                  <div class="pw-wrap">
                    <input id="pw-act" class="form-control" type="password" style="padding-right:2.5rem">
                    <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1"><i class="bi bi-eye-slash"></i></button>
                  </div>
                </div>
                <div class="col-12">
                  <label class="form-label fw-semibold">Nueva contraseña</label>
                  <div class="pw-wrap">
                    <input id="pw-new" class="form-control" type="password" style="padding-right:2.5rem">
                    <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1"><i class="bi bi-eye-slash"></i></button>
                  </div>
                </div>
                <div class="col-12">
                  <label class="form-label fw-semibold">Confirmar nueva contraseña</label>
                  <div class="pw-wrap">
                    <input id="pw-con" class="form-control" type="password" style="padding-right:2.5rem">
                    <button type="button" class="pw-eye" onclick="auth_togglePw(this)" tabindex="-1"><i class="bi bi-eye-slash"></i></button>
                  </div>
                </div>
                <div class="col-12">
                  <button class="btn btn-warning w-100 fw-bold" onclick="auth_cambiarPw()">
                    <i class="bi bi-key-fill me-2"></i>Cambiar Contraseña
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Licencias (solo Desarrollador) -->
    <div class="modal fade" id="modal-licencias" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header text-white fw-bold"
               style="background:linear-gradient(135deg,#7c3aed,#5b21b6)">
            <span><i class="bi bi-key-fill me-2"></i>Gestión de Licencias</span>
            <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-0">
            <ul class="nav nav-tabs px-3 pt-2">
              <li class="nav-item"><button class="nav-link active" id="lt-lista" onclick="lic_tab('lista')"><i class="bi bi-list-ul me-1"></i>Licencias</button></li>
              <li class="nav-item"><button class="nav-link" id="lt-crear" onclick="lic_tab('crear')"><i class="bi bi-plus-circle-fill me-1"></i>Asignar</button></li>
            </ul>
            <div id="lp-lista" class="p-3">
              <div id="lic-lista-body" class="text-center text-muted py-3">
                <div class="spinner-border spinner-border-sm"></div>
              </div>
            </div>
            <div id="lp-crear" class="p-3 d-none">
              <div class="row g-3" style="max-width:500px;margin:auto">

                <!-- Paso 1: Seleccionar admin -->
                <div class="col-12">
                  <label class="form-label fw-bold">
                    <i class="bi bi-person-badge-fill me-1 text-primary"></i>Administrador
                  </label>
                  <input type="text" id="lic-admin-id" class="form-control"
                         placeholder="Selecciona de la lista o pega el ID...">
                  <div id="lic-admin-lista" class="list-group mt-1"
                       style="max-height:140px;overflow-y:auto"></div>
                </div>

                <!-- Paso 2: ID cliente del dispositivo del admin -->
                <div class="col-12">
                  <label class="form-label fw-bold">
                    <i class="bi bi-phone-fill me-1 text-info"></i>
                    ID Cliente del dispositivo del Admin
                    <span class="badge bg-info ms-1" style="font-size:.65rem">REQUERIDO</span>
                  </label>
                  <input type="text" id="lic-cliente-id" class="form-control font-monospace"
                         placeholder="El admin lo ve en: Configuración → Licencias → ID Cliente">
                  <div class="text-muted small mt-1">
                    <i class="bi bi-info-circle me-1"></i>
                    Pídele al administrador que abra su TPV, vaya a
                    <strong>Configuración → Licencias</strong> y te envíe su <strong>ID Cliente</strong>.
                  </div>
                </div>

                <!-- Paso 3: Tipo y duración -->
                <div class="col-6">
                  <label class="form-label fw-bold">Tipo</label>
                  <select id="lic-tipo" class="form-select" onchange="lic_actualizarDias()">
                    <option value="diaria">Diaria (1 día)</option>
                    <option value="mensual">Mensual (30 días)</option>
                    <option value="anual" selected>Anual (365 días)</option>
                    <option value="personalizada">Personalizada</option>
                    <option value="ilimitada">Ilimitada (∞)</option>
                  </select>
                </div>
                <div class="col-6">
                  <label class="form-label fw-bold">Días</label>
                  <input type="number" id="lic-dias" class="form-control" value="365" min="1">
                </div>

                <!-- Notas -->
                <div class="col-12">
                  <label class="form-label fw-bold">Notas (opcional)</label>
                  <input type="text" id="lic-notas" class="form-control"
                         placeholder="Ej: Pago recibido — Mensual marzo">
                </div>

                <!-- Botón generar -->
                <div class="col-12">
                  <button class="btn w-100 fw-bold text-white" onclick="lic_crear()"
                          style="background:#7c3aed">
                    <i class="bi bi-key-fill me-2"></i>Generar Clave de Licencia
                  </button>
                </div>

                <!-- Resultado: clave generada (oculto hasta generar) -->
                <div class="col-12" id="lic-resultado-wrap" style="display:none">
                  <div class="alert alert-success border-0"
                       style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #22c55e!important">
                    <div class="fw-bold text-success mb-2">
                      <i class="bi bi-check-circle-fill me-2"></i>¡Licencia generada!
                    </div>
                    <label class="form-label small fw-bold text-dark mb-1">
                      Clave para el Administrador — cópiala y envíasela:
                    </label>
                    <div class="input-group">
                      <input type="text" id="lic-clave-generada" class="form-control font-monospace"
                             readonly style="font-size:.72rem;background:#fff">
                      <button class="btn btn-success" onclick="lic_copiarClave()" title="Copiar clave">
                        <i class="bi bi-clipboard-fill"></i>
                      </button>
                    </div>
                    <div class="text-muted small mt-2">
                      <i class="bi bi-arrow-right-circle me-1"></i>
                      El admin debe pegar esta clave en
                      <strong>Configuración → Licencias → Activar</strong>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Notificaciones Pedidos -->
    <div class="modal fade" id="modal-notif" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-warning">
            <h5 class="modal-title fw-bold text-dark">
              <i class="bi bi-bell-fill me-2"></i>Pedidos Pendientes
            </h5>
            <button class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" id="notif-body">
            <div class="text-center py-3 text-muted">Cargando...</div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary" data-bs-dismiss="modal"
                    onclick="document.getElementById('tienda-tab')?.click()">
              <i class="bi bi-shop me-1"></i>Ir a Tienda
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Inventario Vendedores (Admin) -->
    <div class="modal fade" id="modal-inv-vendedores" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-xl">
        <div class="modal-content">
          <div class="modal-header" style="background:linear-gradient(135deg,#059669,#047857);color:white">
            <h5 class="modal-title fw-bold">
              <i class="bi bi-people-fill me-2"></i>Inventario Diario de Vendedores
            </h5>
            <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" id="inv-vendedores-body">
            <div class="text-center py-4 text-muted">
              <div class="spinner-border me-2"></div>Cargando...
            </div>
          </div>
        </div>
      </div>
    </div>`);

    _auth_init();
});

// ══════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════
async function _auth_init(intentos = 0) {
    if (typeof bootstrap === 'undefined') {
        if (intentos < 30) setTimeout(() => _auth_init(intentos + 1), 150);
        return;
    }
    // Siempre pedir login al abrir (no entrar automático aunque haya sesión).
    // Cerrar cualquier sesión previa del servidor para forzar autenticación.
    try {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
    } catch(e) {}
    auth_setModo('staff');
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
        btnStaff.style.background  = '#4f46e5';
        btnStaff.style.color       = 'white';
        btnCliente.style.background= 'transparent';
        btnCliente.style.color     = '#64748b';
        setTimeout(() => document.getElementById('login-username')?.focus(), 50);
        try { auth_bioActualizarBoton(); } catch(e) {}
    } else {
        panelStaff.style.display   = 'none';
        panelCliente.style.display = '';
        btnCliente.style.background= '#4f46e5';
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
        btnLogin.style.color = '#4f46e5'; btnLogin.style.borderBottom = '2px solid #4f46e5'; btnLogin.style.fontWeight = '700';
        btnReg.style.color   = '#94a3b8'; btnReg.style.borderBottom   = '2px solid transparent'; btnReg.style.fontWeight = '600';
        setTimeout(() => document.getElementById('cli-email')?.focus(), 50);
    } else {
        panelLogin.style.display = 'none'; panelReg.style.display = '';
        btnReg.style.color   = '#4f46e5'; btnReg.style.borderBottom   = '2px solid #4f46e5'; btnReg.style.fontWeight = '700';
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
            // v8.0: limpieza atomica ANTES de asignar nuevo usuario
            try { _tpv_limpiarEstadoUsuarioAnterior(); } catch(e){}
            AUTH.usuario = data.usuario;
            // Entrar de inmediato (no bloquear el login con la oferta de huella).
            _auth_mostrarApp();
            // Ofrecer registrar huella DESPUÉS, sin bloquear la entrada.
            setTimeout(function () {
                (async function () {
                    try {
                        if (await auth_bioDisponible() && !localStorage.getItem(_BIO_KEY)) {
                            var quiere = (typeof tpvConfirm === 'function')
                                ? await tpvConfirm({ title: 'Acceso con huella', message: '¿Activar inicio de sesión con huella/rostro en este dispositivo?', okText: 'Activar', cancelText: 'Ahora no' })
                                : false;
                            if (quiere) await auth_bioRegistrar(usr);
                        }
                    } catch (e) {}
                })();
            }, 1200);
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

// ══════════════════════════════════════════════════════════════
//  BIOMETRÍA EN EL LOGIN (WebAuthn + puente Android nativo)
//  Funciona si el móvil/navegador lo permite. En el APK, MainActivity
//  puede exponer window.AndroidBiometric para usar la huella nativa.
// ══════════════════════════════════════════════════════════════
var _BIO_KEY = 'tpv_bio_cred';

// Biometría nativa de Android via puente TPVNative (BiometricPrompt).
async function auth_bioDisponible() {
    try {
        if (window.TPVNative && typeof window.TPVNative.canAuthenticate === 'function') {
            return !!window.TPVNative.canAuthenticate();
        }
    } catch (e) {}
    return false;
}

// Mostrar el botón de huella si el dispositivo lo permite Y hay usuario recordado.
async function auth_bioActualizarBoton() {
    var btn = document.getElementById('login-bio-btn');
    if (!btn) return;
    var disponible = await auth_bioDisponible();
    var hayCred = false;
    try { hayCred = !!localStorage.getItem(_BIO_KEY); } catch (e) {}
    btn.style.display = (disponible && hayCred) ? '' : 'none';
}

// Identificador estable del dispositivo (para emitir/revocar tokens por device).
function _bioDeviceId() {
    try {
        var id = localStorage.getItem('tpv_bio_device');
        if (!id) {
            id = 'dev-' + Math.random().toString(36).slice(2, 10) + '-' + Date.now().toString(36);
            localStorage.setItem('tpv_bio_device', id);
        }
        return id;
    } catch (e) { return 'dev-unknown'; }
}

// Tras un login con contraseña, pedir al servidor un TOKEN de dispositivo.
// El token (no la contraseña) es lo que la huella desbloquea después.
// Requiere sesión activa: el endpoint /api/auth/bio/registrar exige login.
async function auth_bioRegistrar(username) {
    try {
        if (!(await auth_bioDisponible())) return false;
        var res = await fetch('/api/auth/bio/registrar', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ device: _bioDeviceId() })
        });
        var data = await res.json();
        if (res.ok && data.ok && data.token) {
            localStorage.setItem(_BIO_KEY, JSON.stringify({ u: username, t: data.token }));
            return true;
        }
    } catch (e) {}
    return false;
}

// Iniciar sesión con huella: lanza el BiometricPrompt nativo y, si tiene éxito,
// canjea el token de dispositivo (sin contraseñas hardcodeadas).
async function auth_loginBiometrico() {
    var raw;
    try { raw = JSON.parse(localStorage.getItem(_BIO_KEY) || 'null'); } catch (e) {}
    if (!raw || !raw.t) {
        // Credencial del formato antiguo (solo usuario, sin token): migrar.
        try { localStorage.removeItem(_BIO_KEY); } catch (e) {}
        _loginErr('Entra con tu contraseña una vez para reactivar la huella.');
        return;
    }
    if (!(window.TPVNative && typeof window.TPVNative.authenticate === 'function')) {
        _loginErr('Biometría no disponible en este dispositivo.'); return;
    }
    // El resultado llega por el callback window.onBiometricCallback (lo pone Java).
    window.onBiometricCallback = async function (r) {
        try {
            if (r && r.success) {
                var res = await fetch('/api/auth/bio/login', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({ token: raw.t })
                });
                var data = await res.json();
                if (res.ok && data.ok) { AUTH.usuario = data.usuario; _auth_mostrarApp(); }
                else {
                    // Token revocado/expirado: limpiar y pedir contraseña.
                    try { localStorage.removeItem(_BIO_KEY); } catch (e) {}
                    _loginErr((data && data.error) || 'Huella desactivada. Entra con contraseña.');
                }
            } else {
                _loginErr((r && r.message) || 'Autenticación biométrica cancelada.');
            }
        } catch (e) { _loginErr('Error en login biométrico.'); }
    };
    try {
        window.TPVNative.authenticate('Iniciar sesión', 'Usa tu huella o rostro', 'TPV UltraSmart');
    } catch (e) { _loginErr('No se pudo abrir el lector biométrico.'); }
}

// Desactivar la huella en este dispositivo (revoca el token en el servidor).
async function auth_bioDesactivar() {
    try {
        await fetch('/api/auth/bio/revocar', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ device: _bioDeviceId() })
        });
    } catch (e) {}
    try { localStorage.removeItem(_BIO_KEY); } catch (e) {}
    if (typeof showToast === 'function') showToast('Huella desactivada en este dispositivo', 'info');
}
window.auth_bioDesactivar = auth_bioDesactivar;


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
                // El AGENTE es quien da la bienvenida (no un cartel). Se abre solo
                // y saluda por nombre y rol. Más dinámico y proactivo.
        // v8.2: El chat NO se auto-abre. Usuario debe pulsar el boton.
            } catch(e) {}
            try {
                conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
                dbg('✅ updateUITranslations OK');
            } catch(e) { dbg('❌ updateUITranslations CRASH: '+e.message); }
            setTimeout(function() {
                _auth_aplicarTabs();
                if (window.AUTH?.usuario?.rol === 'desarrollador') {
                    if (typeof window.tpvDebugger === 'object' && window.tpvDebugger.activar) {
                        window.tpvDebugger.activar();
                    } else if (typeof window._dbg_mostrar === 'function') {
                        window._dbg_mostrar();
                    }
                }
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

    // Sección "Mi Tienda" en Configuración: solo admin/dev
    const cfgTienda = document.getElementById('cfg-tienda-wrap');
    if (cfgTienda) cfgTienda.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // Sección "Mantenimiento" en Configuración: solo admin/dev
    const cfgMant = document.getElementById('cfg-mant-wrap');
    if (cfgMant) cfgMant.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // Configuraciones especiales por rol
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

    const tabBtn = document.getElementById('inv-inventario-tab');
    if (tabBtn) { const s = tabBtn.querySelector('span'); if(s) s.textContent='Mi Inventario'; }

    pane.innerHTML = `
    <div class="glass-card">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h5 class="mb-0 fw-bold"><i class="bi bi-clipboard2-check-fill me-2 text-success"></i>Mi Inventario del Día</h5>
        <div class="d-flex gap-2 align-items-center flex-wrap">
          <input type="date" id="vend-fecha" class="form-control form-control-sm" style="width:150px" onchange="_vend_cargar()">
          <button class="btn btn-sm btn-outline-primary" onclick="_vend_cargar()"><i class="bi bi-arrow-clockwise"></i></button>
        </div>
      </div>
      <div class="alert alert-info py-2 small mb-3">
        <i class="bi bi-info-circle me-1"></i>
        Anota el <strong>Conteo Final</strong> al terminar. Los cálculos se actualizan automáticamente.
        Pulsa <strong>Guardar</strong> para conservar los datos y <strong>Cerrar Día</strong> para registrar el cierre.
      </div>
      <div class="table-responsive">
        <table class="table table-bordered table-striped text-center align-middle" style="font-size:.9rem">
          <thead class="table-dark">
            <tr>
              <th>#</th><th class="text-start">Producto</th><th>U/M</th>
              <th>C. Inicial</th><th>Vendido</th>
              <th style="background:#92400e;color:#fef9c3">C. Final</th>
              <th>I. Venta</th><th>P. Costo</th>
              <th style="color:#fbbf24">Comisión</th>
              <th style="color:#86efac">G. Neta</th>
            </tr>
          </thead>
          <tbody id="vend-inv-body">
            <tr><td colspan="10" class="py-4 text-muted">
              <div class="spinner-border spinner-border-sm me-2"></div>Cargando...
            </td></tr>
          </tbody>
          <tfoot class="fw-bold" style="background:#1e293b;color:#f1f5f9">
            <tr>
              <td colspan="3" class="text-end py-2">TOTALES</td>
              <td id="vt-cinicial">0</td>
              <td id="vt-vendido">0</td>
              <td id="vt-cfinal">0</td>
              <td id="vt-iventa">$0.00</td>
              <td id="vt-costo">$0.00</td>
              <td id="vt-comision" class="text-warning">$0.00</td>
              <td id="vt-gneta" class="text-success">$0.00</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <div class="d-flex gap-2 justify-content-end mt-3 flex-wrap">
        <button class="btn btn-outline-info btn-sm fw-bold" onclick="_vend_mostrarHistorial()">
          <i class="bi bi-clock-history me-1"></i>Historial
        </button>
        <button class="btn btn-success fw-bold" onclick="_vend_guardarConteos()">
          <i class="bi bi-floppy-fill me-2"></i>Guardar Conteos
        </button>
        <button class="btn btn-warning fw-bold" onclick="_vend_cerrarDia()">
          <i class="bi bi-door-closed-fill me-2"></i>Cerrar Día
        </button>
      </div>
      <!-- Panel historial de cierres -->
      <div id="vend-historial-panel" class="mt-4 d-none">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="fw-bold mb-0"><i class="bi bi-journal-text me-2 text-info"></i>Historial de Cierres</h6>
          <button class="btn btn-sm btn-outline-secondary" onclick="document.getElementById('vend-historial-panel').classList.add('d-none')">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div id="vend-historial-body" class="text-center py-3 text-muted">
          <div class="spinner-border spinner-border-sm"></div> Cargando...
        </div>
      </div>
    </div>`;

    const fInp = document.getElementById('vend-fecha');
    if (fInp) fInp.value = new Date().toISOString().split('T')[0];
    _vend_cargar();
    _vend_cargarHistorial();
}

async function _vend_cargarHistorial() {
    const uid = AUTH.usuario.usuario_id;
    try {
        const res  = await fetch(`/api/inventario/diario/historial/${uid}`, { credentials:'same-origin' });
        const data = await res.json();
        const hist = data.historial || [];

        // Crear/buscar contenedor historial
        const pane = document.getElementById('inv-inventario-tab-pane');
        if (!pane) return;
        let hw = document.getElementById('vend-historial-wrap');
        if (!hw) {
            hw = document.createElement('div');
            hw.id = 'vend-historial-wrap';
            pane.appendChild(hw);
        }

        if (!hist.length) { hw.innerHTML = ''; return; }

        const rows = hist.map(c => `<tr>
          <td>${c.fecha}</td>
          <td class="text-primary fw-bold">$${parseFloat(c.total_ventas||0).toFixed(2)}</td>
          <td class="text-secondary">$${parseFloat(c.total_costo||0).toFixed(2)}</td>
          <td class="fw-bold ${parseFloat(c.ganancia_neta||0)>=0?'text-success':'text-danger'}">
              $${parseFloat(c.ganancia_neta||0).toFixed(2)}</td>
        </tr>`).join('');

        hw.innerHTML = `<div class="glass-card mt-3">
          <h6 class="fw-bold mb-2"><i class="bi bi-clock-history me-2 text-info"></i>Historial de Cierres</h6>
          <div class="table-responsive">
          <table class="table table-sm table-hover text-center align-middle" style="font-size:.85rem">
            <thead class="table-dark">
              <tr><th>Fecha</th><th>I.Venta</th><th>Costo</th><th>G.Neta</th></tr>
            </thead>
            <tbody>${rows}</tbody>
          </table></div>
        </div>`;
    } catch(e) {}
}

let _vend_conteos = {};
let _vend_items   = [];

async function _vend_cargar() {
    const body = document.getElementById('vend-inv-body');
    if (!body) return;
    _vend_conteos = {};
    _vend_items   = [];

    const uid  = AUTH.usuario.usuario_id;
    const fInp = document.getElementById('vend-fecha');
    const hoy  = fInp?.value || new Date().toISOString().split('T')[0];

    try {
        const res  = await fetch(`/api/inventario/diario/${uid}?fecha=${hoy}`, { credentials:'same-origin' });
        const data = await res.json();
        _vend_items = data.inventario || [];

        if (!_vend_items.length) {
            body.innerHTML = `<tr><td colspan="9" class="py-5 text-muted text-center">
              <i class="bi bi-inbox" style="font-size:2rem"></i><br>Sin productos asignados para este día.
            </td></tr>`;
            _vend_totales();
            return;
        }

        body.innerHTML = _vend_items.map((p, i) => {
            const pct     = (tpvState.config?.globalProfitPercent || 0) / 100;
            const cfinal  = p.cant_final ?? (p.cant_asignada - p.cant_vendida);
            const iventa  = (p.cant_vendida) * (p.precio_venta  || 0);
            const costoT  = (p.cant_vendida) * (p.precio_costo  || 0);
            const gb      = (p.precio_venta || 0) - (p.precio_costo || 0);
            const comision = (p.cant_vendida) * (gb > 0 ? gb * pct : 0);
            const gneta   = iventa - costoT - comision;
            const pid     = p.producto_id;
            _vend_conteos[pid] = cfinal;
            return `<tr>
              <td>${i+1}</td>
              <td class="text-start fw-semibold">${p.nombre}</td>
              <td>${p.um || 'Un'}</td>
              <td>${p.cant_asignada}</td>
              <td class="fw-bold">${p.cant_vendida}</td>
              <td>
                <input type="number" min="0" step="0.01"
                       id="vf-${pid}"
                       class="form-control form-control-sm text-center"
                       style="width:80px;margin:auto;border:2px solid #f59e0b;font-weight:700"
                       value="${cfinal}"
                       oninput="_vend_conteos['${pid}']=+this.value;_vend_totales()">
              </td>
              <td class="money-column">$${iventa.toFixed(2)}</td>
              <td class="money-column">$${costoT.toFixed(2)}</td>
              <td class="fw-bold text-warning">$${comision.toFixed(2)}</td>
              <td class="fw-bold money-column ${gneta >= 0 ? 'text-success' : 'text-danger'}">$${gneta.toFixed(2)}</td>
            </tr>`;
        }).join('');

        _vend_totales();
    } catch(e) {
        body.innerHTML = `<tr><td colspan="9" class="text-danger py-3 text-center">Error al cargar inventario.</td></tr>`;
    }
}

function _vend_totales() {
    let tCInicial=0, tVendido=0, tCFinal=0, tIventa=0, tCosto=0, tComision=0, tGneta=0;
    const pct = (tpvState.config?.globalProfitPercent || 0) / 100;
    _vend_items.forEach(p => {
        const cfinal   = _vend_conteos[p.producto_id] ?? (p.cant_asignada - p.cant_vendida);
        const iv       = (p.cant_vendida) * (p.precio_venta  || 0);
        const co       = (p.cant_vendida) * (p.precio_costo  || 0);
        const gb       = (p.precio_venta || 0) - (p.precio_costo || 0);
        const com      = (p.cant_vendida) * (gb > 0 ? gb * pct : 0);
        tCInicial  += p.cant_asignada;
        tVendido   += p.cant_vendida;
        tCFinal    += parseFloat(cfinal) || 0;
        tIventa    += iv;
        tCosto     += co;
        tComision  += com;
        tGneta     += iv - co - com;
    });
    const s = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    s('vt-cinicial', tCInicial);
    s('vt-vendido',  tVendido);
    s('vt-cfinal',   parseFloat(tCFinal.toFixed(2)));
    s('vt-iventa',   '$' + tIventa.toFixed(2));
    s('vt-costo',    '$' + tCosto.toFixed(2));
    s('vt-comision', '$' + tComision.toFixed(2));
    const gEl = document.getElementById('vt-gneta');
    if (gEl) { gEl.textContent = '$' + tGneta.toFixed(2); gEl.className = tGneta >= 0 ? 'text-success' : 'text-danger'; }
}

async function _vend_guardarConteos() {
    const uid     = AUTH.usuario.usuario_id;
    const cambios = Object.entries(_vend_conteos);
    if (!cambios.length) { _toast('Sin cambios pendientes.', 'info'); return; }

    let ok = 0;
    for (const [pid, cant] of cambios) {
        try {
            const r = await fetch('/api/inventario/diario/conteo', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ vendedor_id: uid, producto_id: pid, cant_final: cant })
            });
            if (r.ok) ok++;
        } catch(e) {}
    }
    _toast(`\u2705 ${ok} conteo${ok !== 1 ? 's' : ''} guardado${ok !== 1 ? 's' : ''}`, 'success');
}

async function _vend_cerrarDia() {
    const uid  = AUTH.usuario.usuario_id;
    const fInp = document.getElementById('vend-fecha');
    const hoy  = fInp?.value || new Date().toISOString().split('T')[0];

    if (!_vend_items.length) { _toast('No hay inventario para cerrar.', 'warning'); return; }
    if (!(await tpvConfirm(`\u00bfCerrar el d\u00eda ${hoy}?\n\nEsto registrar\u00e1 el resumen de ventas.\nAseg\u00farate de haber anotado todos los conteos finales.`))) return;

    // Guardar conteos primero
    await _vend_guardarConteos();

    // Calcular totales del cierre
    let tVentas = 0, tCosto = 0, tGneta = 0;
    _vend_items.forEach(p => {
        const iv = p.cant_vendida * (p.precio_venta  || 0);
        const co = p.cant_vendida * (p.precio_costo  || 0);
        tVentas += iv;
        tCosto  += co;
        tGneta  += iv - co;
    });

    try {
        const res  = await fetch('/api/inventario/diario/cierre', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                vendedor_id:  uid,
                fecha:        hoy,
                total_ventas: tVentas,
                total_costo:  tCosto,
                ganancia_neta: tGneta,
                items:        _vend_items.map(p => ({
                    producto_id:   p.producto_id,
                    nombre:        p.nombre,       // necesario para traspaso
                    um:            p.um || 'Un',
                    cant_asignada: p.cant_asignada,
                    cant_vendida:  p.cant_vendida,
                    cant_final:    parseFloat(_vend_conteos[p.producto_id] ?? p.cant_final ?? 0),
                    precio_venta:  p.precio_venta  || 0,
                    precio_costo:  p.precio_costo  || 0
                }))
            })
        });
        const data = await res.json();
        if (res.ok) {
            _toast(`\u2705 D\u00eda cerrado \u2014 Ventas: $${tVentas.toFixed(2)} | G.Neta: $${tGneta.toFixed(2)}`, 'success');
            _vend_items   = [];
            _vend_conteos = {};
            _vend_cargar();
        } else {
            _toast(data.error || 'Error al cerrar d\u00eda', 'danger');
        }
    } catch(e) { _toast('Error de conexi\u00f3n', 'danger'); }
}

// ══════════════════════════════════════════════════════════════
//  HISTORIAL DE CIERRES — Vendedor
// ══════════════════════════════════════════════════════════════
async function _vend_mostrarHistorial() {
    const panel = document.getElementById('vend-historial-panel');
    const body  = document.getElementById('vend-historial-body');
    if (!panel || !body) return;

    panel.classList.remove('d-none');
    body.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Cargando...';

    try {
        const uid = AUTH.usuario.usuario_id;
        const res  = await fetch(`/api/inventario/diario/historial/${uid}`, { credentials: 'same-origin' });
        const data = await res.json();
        const hist = data.historial || [];

        if (!hist.length) {
            body.innerHTML = '<p class="text-muted text-center py-3"><i class="bi bi-inbox me-2"></i>Sin cierres registrados.</p>';
            return;
        }

        const totalV = hist.reduce((s,c)=>s+(c.total_ventas||0),0);
        const totalC = hist.reduce((s,c)=>s+(c.total_costo||0),0);
        const totalG = totalV - totalC;
        body.innerHTML = `
        <div class="table-responsive">
          <table class="table table-sm table-hover align-middle text-center" style="font-size:.85rem">
            <thead class="table-dark">
              <tr>
                <th>Fecha</th>
                <th class="text-end">Ventas</th>
                <th class="text-end">Costo</th>
                <th class="text-end" style="color:#86efac">G.Neta</th>
                <th>Productos</th>
              </tr>
            </thead>
            <tbody>
              ${hist.map(c => {
                  const items = (() => { try { return JSON.parse(c.items_json||'[]'); } catch(e){ return []; } })();
                  const gn = (c.total_ventas||0) - (c.total_costo||0);
                  return `<tr>
                    <td class="fw-semibold">${c.fecha}</td>
                    <td class="text-end text-primary">$${(c.total_ventas||0).toFixed(2)}</td>
                    <td class="text-end text-secondary">$${(c.total_costo||0).toFixed(2)}</td>
                    <td class="text-end fw-bold ${gn>=0?'text-success':'text-danger'}">$${gn.toFixed(2)}</td>
                    <td class="text-muted">${items.length} prod.</td>
                  </tr>`;
              }).join('')}
            </tbody>
            <tfoot class="fw-bold" style="background:#1e293b;color:#f1f5f9">
              <tr>
                <td class="text-end">TOTAL (${hist.length} días)</td>
                <td class="text-end">$${totalV.toFixed(2)}</td>
                <td class="text-end">$${totalC.toFixed(2)}</td>
                <td class="text-end ${totalG>=0?'text-success':'text-danger'}">$${totalG.toFixed(2)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>`;
    } catch(e) {
        body.innerHTML = `<div class="alert alert-danger py-2">Error: ${e.message}</div>`;
    }
}


// ══════════════════════════════════════════════════════════════
//  INVENTARIO ADMIN — Almacén General + Vista vendedores
// ══════════════════════════════════════════════════════════════
function _setup_admin_inventario() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane || document.getElementById('inv-admin-btns')) return;

    const btns = document.createElement('div');
    btns.id = 'inv-admin-btns';
    btns.className = 'd-flex gap-2 mb-3 flex-wrap align-items-center';
    btns.innerHTML = `
        <button class="btn btn-primary btn-sm" id="inv-btn-almacen"
                onclick="_admin_invVista('almacen')">
            <i class="bi bi-building-fill-gear me-1"></i>Almacén General
        </button>
        <button class="btn btn-outline-success btn-sm" id="inv-btn-vendedores"
                onclick="_admin_invVista('vendedores')">
            <i class="bi bi-people-fill me-1"></i>Vendedores Hoy
        </button>
        <button class="btn btn-outline-warning btn-sm" id="inv-btn-gastos"
                onclick="_admin_invVista('gastos')">
            <i class="bi bi-cash-stack me-1"></i>Gastos / Inversión
        </button>`;
    pane.insertBefore(btns, pane.firstChild);
}

/** Supervisor: solo ve la vista de Vendedores Hoy (sin Almacén ni Gastos) */
function _setup_supervisor_inventario() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane) return;
    const tabBtn = document.getElementById('inv-inventario-tab');
    if (tabBtn) { const s = tabBtn.querySelector('span'); if(s) s.textContent = 'Inventario Vendedores'; }
    // Insertar botones de supervisor si no existen
    if (!document.getElementById('inv-sup-btns')) {
        const btns = document.createElement('div');
        btns.id = 'inv-sup-btns';
        btns.className = 'd-flex gap-2 mb-3 flex-wrap align-items-center';
        btns.innerHTML = `
            <button class="btn btn-success btn-sm" id="inv-btn-vendedores"
                    onclick="_admin_invVista('vendedores')">
                <i class="bi bi-people-fill me-1"></i>Vendedores Hoy
            </button>`;
        pane.insertBefore(btns, pane.firstChild);
    }
    // Ocultar el contenido original del inventario (tabla del día)
    [...pane.querySelectorAll(':scope > *:not(#inv-sup-btns):not(#inv-admin-vendedores-wrap):not(#inv-admin-gastos-wrap)')]
        .forEach(el => el.style.display = 'none');
    // Cargar vista vendedores directamente
    _admin_cargarVendedores();
}

function _admin_invVista(v) {
    // Actualizar estilos de botones
    const btnMap = {
        almacen:    { id:'inv-btn-almacen',    on:'btn btn-primary btn-sm',  off:'btn btn-outline-primary btn-sm' },
        vendedores: { id:'inv-btn-vendedores', on:'btn btn-success btn-sm',  off:'btn btn-outline-success btn-sm' },
        gastos:     { id:'inv-btn-gastos',     on:'btn btn-warning btn-sm',  off:'btn btn-outline-warning btn-sm' },
    };
    Object.entries(btnMap).forEach(([k, cfg]) => {
        const el = document.getElementById(cfg.id);
        if (el) el.className = v === k ? cfg.on : cfg.off;
    });

    // Contenidos dinámicos
    const wrapVend   = document.getElementById('inv-admin-vendedores-wrap');
    const wrapGastos = document.getElementById('inv-admin-gastos-wrap');
    const orig = [...document.querySelectorAll(
        '#inv-inventario-tab-pane > *:not(#inv-admin-btns):not(#inv-admin-vendedores-wrap):not(#inv-admin-gastos-wrap)'
    )];

    // Ocultar todo primero
    if (wrapVend)   wrapVend.style.display   = 'none';
    if (wrapGastos) wrapGastos.style.display = 'none';
    orig.forEach(el => el.style.display = 'none');

    if (v === 'almacen') {
        orig.forEach(el => el.style.display = '');
    }
    else if (v === 'vendedores') _admin_cargarVendedores();
    else if (v === 'gastos')     _admin_cargarGastos();
}

/** Recarga el almacén general refrescando datos desde el servidor */
async function _admin_recargarAlmacen() {
    // Delegar en _admin_renderVendedores que ya construye correctamente todo el HTML
    const fEl = document.getElementById('inv-admin-fecha-vend');
    const hoy  = fEl?.value || new Date().toISOString().split('T')[0];
    await _admin_renderVendedores(hoy);
}

async function _admin_cargarVendedores() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane) return;

    let wrap = document.getElementById('inv-admin-vendedores-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.id = 'inv-admin-vendedores-wrap';
        wrap.className = 'mt-0';
        pane.appendChild(wrap);
    }
    wrap.style.display = '';

    // Header con filtro de fecha dinámico
    const hoy = new Date().toISOString().split('T')[0];
    // Conservar fecha seleccionada si el elemento ya existe
    const fechaExist = document.getElementById('inv-admin-fecha-vend');
    const fechaVer   = fechaExist?.value || hoy;

    wrap.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5 class="mb-0 fw-bold"><i class="bi bi-people-fill me-2 text-success"></i>Inventario Vendedores</h5>
      <div class="d-flex gap-2 align-items-center flex-wrap">
        <input type="date" id="inv-admin-fecha-vend" class="form-control form-control-sm"
               style="width:145px" value="${fechaVer}"
               onchange="document.getElementById('inv-vend-body').innerHTML='<div class=\'text-center py-4\'><div class=\'spinner-border text-success me-2\'></div>Cargando...</div>';_admin_renderVendedores(this.value)">
        <span id="inv-vend-ts" class="text-muted small"></span>
        <button class="btn btn-sm btn-outline-secondary" onclick="_admin_cargarVendedores()">
          <i class="bi bi-arrow-clockwise me-1"></i>
        </button>
      </div>
    </div>
    <div id="inv-vend-body"><div class="text-center py-4"><div class="spinner-border text-success me-2"></div>Cargando...</div></div>`;

    await _admin_renderVendedores(fechaVer);

    // Polling cada 20 segundos mientras la vista esté activa
    clearInterval(window._vendPolling);
    window._vendPolling = setInterval(() => {
        const bV = document.getElementById('inv-btn-vendedores');
        if (!bV || bV.className.indexOf('btn-success btn-sm') === -1) {
            clearInterval(window._vendPolling);
            return;
        }
        // Usar la fecha del selector si existe
        const fEl = document.getElementById('inv-admin-fecha-vend');
        _admin_renderVendedores(fEl?.value || hoy);
    }, 20000);
}

async function _admin_renderVendedores(hoy) {
    const body = document.getElementById('inv-vend-body');
    if (!body) return;
    try {
        const [resU, resG] = await Promise.all([
            fetch('/api/usuarios',          { credentials: 'same-origin' }),
            fetch('/api/inventario/general',{ credentials: 'same-origin' })
        ]);
        if (!resU.ok) {
            const txt = await resU.text();
            throw new Error(`HTTP ${resU.status} /api/usuarios — ${txt.slice(0,300)}`);
        }
        if (!resG.ok) {
            const txt = await resG.text();
            throw new Error(`HTTP ${resG.status} /api/inventario/general — ${txt.slice(0,300)}`);
        }
        const dataU   = await resU.json();
        const dataG   = await resG.json();
        const vends   = (dataU.usuarios || []).filter(u => u.rol === 'vendedor' && u.activo);
        const general = dataG.inventario || [];

        window._adminVends   = vends;
        window._adminGeneral = general;

        let html = '';

        // ── BARRA ACCIONES ──
        html += `<div class="d-flex gap-2 mb-3 flex-wrap align-items-center">
          <button class="btn btn-sm btn-outline-danger" onclick="_admin_limpiarInventariosUI()">
            <i class="bi bi-trash3-fill me-1"></i>Limpiar Inventarios
          </button>
          <label class="btn btn-sm btn-outline-success mb-0" title="Carga cantidades desde columna del XLSX directamente al stock del almacén">
            <i class="bi bi-file-earmark-spreadsheet me-1"></i>Cargar Stock XLSX
            <input type="file" accept=".xlsx" class="d-none" onchange="_admin_cargarStockXLSX(event)">
          </label>
          <span class="text-muted small ms-auto">
            <i class="bi bi-info-circle me-1"></i>
            Selecciona vendedor + cantidad → <i class="bi bi-send-fill"></i> para asignar
          </span>
        </div>`;

        // ── TABLA GENERAL INTERACTIVA ──
        if (general.length) {
            const optsVend = vends.map(v =>
                `<option value="${v.usuario_id}">${v.nombre}</option>`
            ).join('');
            html += `<div class="glass-card mb-4">
              <h6 class="fw-bold mb-3">
                <i class="bi bi-building-fill-gear me-1 text-primary"></i>Almacén General
                <span class="badge bg-primary ms-2">${general.length} productos</span>
              </h6>
              <div class="table-responsive">
              <table class="table table-sm table-hover mb-0 align-middle" style="font-size:.82rem">
                <thead class="table-primary">
                  <tr>
                    <th class="text-start">Producto</th><th>Categ.</th>
                    <th class="text-center">Stock</th>
                    <th class="text-center">P.Costo</th>
                    <th class="text-center">P.Venta</th>
                    <th style="min-width:130px">Vendedor</th>
                    <th style="min-width:90px" class="text-center">Cantidad</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${general.map(p => {
                      const stk = parseFloat(p.stock_actual) || 0;
                      const min = parseFloat(p.stock_minimo)  || 5;
                      const cls = stk <= 0 ? 'text-danger fw-bold' : stk <= min ? 'text-warning fw-bold' : 'text-success fw-bold';
                      const pid = p.producto_id;
                      return `<tr id="agn-row-${pid}">
                        <td class="text-start fw-semibold">${p.nombre}</td>
                        <td class="text-muted">${p.categoria||'-'}</td>
                        <td class="text-center ${cls}">${stk}</td>
                        <td class="text-center text-warning">$${parseFloat(p.precio_compra||0).toFixed(2)}</td>
                        <td class="text-center">$${parseFloat(p.precio_venta||0).toFixed(2)}</td>
                        <td>${vends.length
                          ? `<select class="form-select form-select-sm" id="agn-vend-${pid}" style="font-size:.78rem">${optsVend}</select>`
                          : '<span class="text-muted small">Sin vendedores</span>'}</td>
                        <td class="text-center">
                          <input type="number" id="agn-cant-${pid}"
                                 class="form-control form-control-sm text-center"
                                 min="0" max="${stk}" step="1" value=""
                                 placeholder="0" style="width:72px;font-size:.82rem"
                                 data-pid="${pid}"
                                 data-nombre="${p.nombre.replace(/"/g,'&quot;')}"
                                 data-pv="${p.precio_venta||0}"
                                 data-pc="${p.precio_compra||0}"
                                 data-stock="${stk}">
                        </td>
                        <td>
                          <button class="btn btn-sm btn-success px-2 py-1"
                                  onclick="_admin_asignarUno('${pid}')"
                                  title="Asignar">
                            <i class="bi bi-send-fill"></i>
                          </button>
                        </td>
                      </tr>`;
                  }).join('')}
                </tbody>
                <tfoot class="table-secondary fw-bold" style="font-size:.82rem">
                  <tr>
                    <td colspan="2" class="text-end">TOTALES</td>
                    <td class="text-center">${general.reduce((s,p)=>s+(parseFloat(p.stock_actual)||0),0).toFixed(0)}</td>
                    <td class="text-center text-warning">
                      $${(general.reduce((s,p)=>s+(parseFloat(p.precio_compra)||0),0)).toFixed(2)}
                    </td>
                    <td class="text-center">
                      $${(general.reduce((s,p)=>s+(parseFloat(p.precio_venta)||0),0)).toFixed(2)}
                    </td>
                    <td colspan="3"></td>
                  </tr>
                  <tr class="table-primary">
                    <td colspan="8" class="text-end small">
                      <span class="me-3">💰 <strong>Inversión total (costo×stock):</strong>
                        $${(general.reduce((s,p)=>s+(parseFloat(p.precio_compra)||0)*(parseFloat(p.stock_actual)||0),0)).toFixed(2)}
                      </span>
                      <span>📈 <strong>Valor total a precio venta:</strong>
                        $${(general.reduce((s,p)=>s+(parseFloat(p.precio_venta)||0)*(parseFloat(p.stock_actual)||0),0)).toFixed(2)}
                      </span>
                    </td>
                  </tr>
                </tfoot>
              </table></div>
            </div>`;
        } else {
            html += `<div class="alert alert-warning">
              <i class="bi bi-exclamation-triangle me-2"></i>
              Almacén general vacío. Registra entradas de productos primero.
            </div>`;
        }

        // ── TARJETAS POR VENDEDOR ──
        let gVentas = 0, gCosto = 0, gComision = 0, gGanancia = 0;
        if (!vends.length) {
            html += '<div class="alert alert-info">Sin vendedores activos.</div>';
        }
        for (const v of vends) {
            const resI  = await fetch(`/api/inventario/diario/${v.usuario_id}?fecha=${hoy}`, { credentials: 'same-origin' });
            if (!resI.ok) {
                const txt = await resI.text();
                throw new Error(`HTTP ${resI.status} inventario ${v.nombre} — ${txt.slice(0,150)}`);
            }
            const dataI = await resI.json();
            const items = dataI.inventario || [];
            const pct   = (tpvState.config?.globalProfitPercent || 0) / 100;
            const tV  = items.reduce((s,p)=>s+(p.cant_vendida||0)*(p.precio_venta||0),0);
            const tC  = items.reduce((s,p)=>s+(p.cant_vendida||0)*(p.precio_costo||0),0);
            const tCom= items.reduce((s,p)=>{
                const gb = (p.precio_venta||0)-(p.precio_costo||0);
                return s + (p.cant_vendida||0) * (gb > 0 ? gb * pct : 0);
            }, 0);
            const tG  = tV - tC - tCom;
            gVentas+=tV; gCosto+=tC; gComision+=tCom; gGanancia+=tG;
            html += `<div class="glass-card mb-3" id="vend-card-${v.usuario_id}">
              <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                <span class="fw-bold fs-6">
                  <i class="bi bi-person-badge-fill me-1 text-success"></i>${v.nombre}
                  <span class="text-muted fw-normal small">@${v.username}</span>
                </span>
                <div class="d-flex gap-1 flex-wrap align-items-center">
                  <span class="badge bg-primary">$${tV.toFixed(2)}</span>
                  <span class="badge bg-warning text-dark">C: $${tCom.toFixed(2)}</span>
                  <span class="badge ${tG>=0?'bg-success':'bg-danger'}">G: $${tG.toFixed(2)}</span>
                  <button class="btn btn-sm btn-outline-danger px-2 py-0"
                          onclick="_admin_limpiarVendedor('${v.usuario_id}','${v.nombre}')"
                          title="Limpiar inventario">
                    <i class="bi bi-x-circle-fill"></i>
                  </button>
                </div>
              </div>
              ${items.length ? `<div class="table-responsive">
              <table class="table table-sm table-hover mb-0 text-center align-middle" style="font-size:.82rem">
                <thead class="table-dark">
                  <tr><th class="text-start">Producto</th><th>U/M</th><th>Asig.</th>
                      <th>Vendido</th><th>Dispon.</th><th>I.Venta</th>
                      <th style="color:#fbbf24">Comisión</th>
                      <th style="color:#86efac">G.Neta</th></tr>
                </thead><tbody>
                  ${items.map(p=>{
                    const pct  = (tpvState.config?.globalProfitPercent || 0) / 100;
                    const d    = (p.cant_asignada||0)-(p.cant_vendida||0);
                    const cl   = d<=0?'text-danger':d<=3?'text-warning':'text-success';
                    const iv   = (p.cant_vendida||0)*(p.precio_venta||0);
                    const gb   = (p.precio_venta||0)-(p.precio_costo||0);
                    const com  = (p.cant_vendida||0) * (gb > 0 ? gb * pct : 0);
                    const gn   = (p.cant_vendida||0) * gb - com;
                    return `<tr><td class="text-start">${p.nombre}</td><td>${p.um||'Un'}</td>
                      <td>${p.cant_asignada}</td><td class="fw-bold">${p.cant_vendida}</td>
                      <td class="fw-bold ${cl}">${d}</td><td>$${iv.toFixed(2)}</td>
                      <td class="fw-bold text-warning">$${com.toFixed(2)}</td>
                      <td class="fw-bold ${gn>=0?'text-success':'text-danger'}">$${gn.toFixed(2)}</td></tr>`;
                  }).join('')}
                </tbody></table></div>`
              : `<p class="text-muted small py-2 mb-0">
                  <i class="bi bi-inbox me-1"></i>Sin productos asignados. Usa el almacén de arriba.
                </p>`}
            </div>`;
        }

        // ── RESUMEN GLOBAL ──
        html += `<div class="glass-card" style="border:2px solid #4f46e544;background:linear-gradient(135deg,#4f46e50d,#19875411)">
          <h6 class="fw-bold text-center mb-3"><i class="bi bi-graph-up-arrow me-1 text-primary"></i>Resumen Global del Día</h6>
          <div class="row text-center g-2 mb-2">
            <div class="col-6 col-sm-2"><div class="text-muted small">Ingresos</div><div class="fw-bold text-primary fs-6">$${gVentas.toFixed(2)}</div></div>
            <div class="col-6 col-sm-2"><div class="text-muted small">Costo Vendido</div><div class="fw-bold text-secondary fs-6">$${gCosto.toFixed(2)}</div></div>
            <div class="col-6 col-sm-2"><div class="text-muted small">Comisiones</div><div class="fw-bold text-warning fs-6">$${gComision.toFixed(2)}</div></div>
            <div class="col-6 col-sm-2"><div class="text-muted small">Gastos Operac.</div><div class="fw-bold text-danger fs-6" id="resumen-gastos-dia">$0.00</div></div>
            <div class="col-6 col-sm-2">
              <div class="text-muted small">Utilidad Bruta</div>
              <div class="fw-bold text-success fs-6">$${(gVentas - gCosto - gComision).toFixed(2)}</div>
            </div>
            <div class="col-6 col-sm-2">
              <div class="text-muted small fw-bold">Utilidad Real</div>
              <div class="fw-bold fs-5" id="resumen-utilidad-dia">$${gGanancia.toFixed(2)}</div>
            </div>
          </div>
          <div class="text-center"><small class="text-muted">Utilidad Real = Ingresos − Costo Vendido − Comisiones − Gastos Operativos</small></div>
        </div>`;

        body.innerHTML = html;

        try {
            const rG = await fetch(`/api/gastos?desde=${hoy}&hasta=${hoy}`, { credentials: 'same-origin' });
            const dG = await rG.json();
            const totalG   = (dG.gastos||[]).reduce((s,g)=>s+(g.monto||0),0);
            const utilReal = gGanancia - totalG;
            const elG = document.getElementById('resumen-gastos-dia');
            const elU = document.getElementById('resumen-utilidad-dia');
            if (elG) elG.textContent = '$'+totalG.toFixed(2);
            if (elU) { elU.textContent='$'+utilReal.toFixed(2); elU.className='fw-bold fs-6 '+(utilReal>=0?'text-success':'text-danger'); }
        } catch(e){}

        const ts = document.getElementById('inv-vend-ts');
        if (ts) ts.textContent = 'Actualizado: '+new Date().toLocaleTimeString();
    } catch(e) {
        if (body) body.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
    }
}

/** Asigna un producto del almacén a un vendedor directamente */
async function _admin_asignarUno(pid) {
    const vendEl = document.getElementById(`agn-vend-${pid}`);
    const cantEl = document.getElementById(`agn-cant-${pid}`);
    if (!vendEl || !cantEl) return;
    const vendedor_id = vendEl.value;
    const cantidad    = parseFloat(cantEl.value)||0;
    const stock       = parseFloat(cantEl.dataset.stock)||0;
    const nombre      = cantEl.dataset.nombre||pid;
    const pv          = parseFloat(cantEl.dataset.pv)||0;
    const pc          = parseFloat(cantEl.dataset.pc)||0;
    if (!vendedor_id) { tpvAlert('Selecciona un vendedor'); return; }
    if (cantidad<=0)  { tpvAlert('Ingresa una cantidad mayor a 0'); cantEl.focus(); return; }
    if (cantidad>stock){ tpvAlert(`Stock insuficiente. Disponible: ${stock}`); return; }
    const btn = document.querySelector(`#agn-row-${pid} button`);
    if (btn) { btn.disabled=true; btn.innerHTML='<span class="spinner-border spinner-border-sm"></span>'; }
    try {
        const comisionPct = parseFloat(tpvState.config?.globalProfitPercent || 0);
        const res = await fetch('/api/inventario/asignar-diario', {
            method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ vendedor_id, productos:[{
                producto_id: pid, nombre,
                cant_asignada: cantidad,
                precio_venta: pv,
                precio_costo: pc,
                comision_pct: comisionPct
            }]})
        });
        const data = await res.json();
        if (data.ok) {
            // Rebajar del DOM lo realmente asignado (puede ser menos si stock era parcial)
            const cantReal = data.asignados > 0 ? cantidad : 0;
            const stockCl = document.querySelector(`#agn-row-${pid} td:nth-child(3)`);
            if (stockCl) {
                const ns = Math.max(0, stock - cantReal);
                stockCl.textContent = ns;
                stockCl.className   = `text-center fw-bold ${ns<=0?'text-danger':ns<=5?'text-warning':'text-success'}`;
                cantEl.dataset.stock = ns; cantEl.max = ns;
            }
            cantEl.value = '';
            const hoy = document.getElementById('inv-admin-fecha-vend')?.value || new Date().toISOString().split('T')[0];
            _admin_actualizarTarjetaVendedor(vendedor_id, hoy);
            const msg = data.errores?.length
                ? `⚠️ ${cantReal} × ${nombre} asignado. ${data.errores[0]}`
                : `✅ ${cantReal} × ${nombre} → ${(window._adminVends||[]).find(v=>v.usuario_id===vendedor_id)?.nombre||vendedor_id}`;
            if (typeof showToast==='function') showToast(msg, data.errores?.length ? 'warning' : 'success');
        } else {
            const errMsg = data.errores?.[0] || data.mensaje || 'No se pudo asignar';
            if (typeof showToast==='function') showToast(`❌ ${errMsg}`, 'danger');
            else tpvAlert('Error: ' + errMsg);
        }
    } catch(e) {
        if (typeof showToast==='function') showToast(`❌ Error de red: ${e.message}`, 'danger');
        else tpvAlert('Error de red: '+e.message);
    }
    finally { if(btn){btn.disabled=false;btn.innerHTML='<i class="bi bi-send-fill"></i>';} }
}

/** Actualiza solo la tarjeta de un vendedor sin recargar todo */
async function _admin_actualizarTarjetaVendedor(vendedor_id, fecha) {
    const card = document.getElementById(`vend-card-${vendedor_id}`);
    if (!card) return;
    const vend = (window._adminVends||[]).find(v=>v.usuario_id===vendedor_id);
    if (!vend) return;
    try {
        const res   = await fetch(`/api/inventario/diario/${vendedor_id}?fecha=${fecha}`, {credentials:'same-origin'});
        const data  = await res.json();
        const items = data.inventario||[];
        const tV = items.reduce((s,p)=>s+(p.cant_vendida||0)*(p.precio_venta||0),0);
        const tG = tV - items.reduce((s,p)=>s+(p.cant_vendida||0)*(p.precio_costo||0),0);
        const badges = card.querySelector('.d-flex.gap-1');
        if (badges) badges.innerHTML = `
          <span class="badge bg-primary">$${tV.toFixed(2)}</span>
          <span class="badge ${tG>=0?'bg-success':'bg-danger'}">G: $${tG.toFixed(2)}</span>
          <button class="btn btn-sm btn-outline-danger px-2 py-0"
                  onclick="_admin_limpiarVendedor('${vendedor_id}','${vend.nombre}')"
                  title="Limpiar inventario"><i class="bi bi-x-circle-fill"></i></button>`;
        if (!items.length) return;
        const rows = items.map(p=>{
            const pct  = (tpvState.config?.globalProfitPercent || 0) / 100;
            const d    = (p.cant_asignada||0)-(p.cant_vendida||0);
            const cl   = d<=0?'text-danger':d<=3?'text-warning':'text-success';
            const iv   = (p.cant_vendida||0)*(p.precio_venta||0);
            const gb   = (p.precio_venta||0)-(p.precio_costo||0);
            const com  = (p.cant_vendida||0) * (gb > 0 ? gb * pct : 0);
            const gn   = (p.cant_vendida||0) * gb - com;
            return `<tr><td class="text-start">${p.nombre}</td><td>${p.um||'Un'}</td>
              <td>${p.cant_asignada}</td><td class="fw-bold">${p.cant_vendida}</td>
              <td class="fw-bold ${cl}">${d}</td><td>$${iv.toFixed(2)}</td>
              <td class="fw-bold text-warning">$${com.toFixed(2)}</td>
              <td class="fw-bold ${gn>=0?'text-success':'text-danger'}">$${gn.toFixed(2)}</td></tr>`;
        }).join('');
        const tbody = card.querySelector('tbody');
        if (tbody) { tbody.innerHTML=rows; return; }
        const pE = card.querySelector('p.text-muted');
        if (pE) pE.outerHTML=`<div class="table-responsive"><table class="table table-sm table-hover mb-0 text-center align-middle" style="font-size:.82rem">
          <thead class="table-dark"><tr><th class="text-start">Producto</th><th>U/M</th><th>Asig.</th>
          <th>Vendido</th><th>Dispon.</th><th>I.Venta</th>
          <th style="color:#fbbf24">Comisión</th>
          <th style="color:#86efac">G.Neta</th></tr></thead>
          <tbody>${rows}</tbody></table></div>`;
    } catch(e){}
}

/** Limpiar inventario de un vendedor */
async function _admin_limpiarVendedor(vendedor_id, nombre) {
    if (!(await tpvConfirm(`⚠️ ¿Eliminar todo el inventario diario de ${nombre}?\n\nEl almacén general NO se modifica.`))) return;
    try {
        const res  = await fetch('/api/inventario/diario/limpiar', {
            method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({vendedor_id})
        });
        const data = await res.json();
        if (data.ok) {
            if (typeof showToast==='function') showToast(`🗑️ Inventario de ${nombre} limpiado`,'warning');
            const hoy = document.getElementById('inv-admin-fecha-vend')?.value||new Date().toISOString().split('T')[0];
            _admin_renderVendedores(hoy);
        } else { tpvAlert('Error: '+data.mensaje); }
    } catch(e) { tpvAlert('Error: '+e.message); }
}

/** Carga stock masivo desde XLSX al almacén general */
async function _admin_cargarStockXLSX(event) {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;

    if (typeof XLSX === 'undefined') {
        showToast('❌ Librería XLSX no disponible', 'danger'); return;
    }

    showToast('📖 Leyendo archivo de stock...', 'info');
    try {
        const buf  = await new Promise((res, rej) => {
            const r = new FileReader();
            r.onload = e => res(e.target.result);
            r.onerror = () => rej(new Error('Error leyendo archivo'));
            r.readAsArrayBuffer(file);
        });
        const wb   = XLSX.read(new Uint8Array(buf), { type: 'array' });
        const ws   = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });

        if (!rows.length) { showToast('❌ Archivo vacío', 'danger'); return; }

        // Detectar columnas: busca encabezados Nombre y Cantidad/Stock
        const header = rows[0].map(c => String(c).toLowerCase().trim());
        let colNombre   = header.findIndex(h => /nombre|product|descripci/i.test(h));
        let colCantidad = header.findIndex(h => /cantidad|stock|cant|qty|existencia/i.test(h));
        let colCosto    = header.findIndex(h => /costo|cost|compra|precio.*costo/i.test(h));
        // Fallback posicional si no hay encabezados reconocibles
        if (colNombre   < 0) colNombre   = 0;
        if (colCantidad < 0) colCantidad = 3; // columna D por defecto

        const filaInicio = header.some(h => /nombre|product/i.test(h)) ? 1 : 0;

        // Construir mapa nombre→producto_id desde el almacén actual
        const general = window._adminGeneral || [];
        const mapaId  = {};
        general.forEach(p => { mapaId[p.nombre.toLowerCase().trim()] = p.producto_id; });

        const items = [];
        for (let i = filaInicio; i < rows.length; i++) {
            const fila = rows[i];
            const nom  = String(fila[colNombre] || '').trim();
            const cant = parseFloat(String(fila[colCantidad] || '0').replace(/[^0-9.]/g,'')) || 0;
            const pc   = colCosto >= 0 ? (parseFloat(String(fila[colCosto] || '0').replace(/[^0-9.]/g,'')) || 0) : 0;
            if (!nom || cant <= 0) continue;
            const pid = mapaId[nom.toLowerCase()];
            if (pid) items.push({ producto_id: pid, cantidad: cant, precio_compra: pc });
        }

        if (!items.length) {
            showToast('⚠️ No se encontraron filas con nombre coincidente y cantidad > 0.\nVerifica que los nombres del XLSX coincidan con el almacén.', 'warning');
            return;
        }

        showToast(`⚙️ Cargando stock de ${items.length} productos...`, 'info');
        const r = await fetch('/api/stock/masivo', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items })
        });
        const d = await r.json();
        if (d.ok) {
            showToast(`✅ ${d.mensaje}`, 'success');
            // Recargar vista del almacén
            const fEl = document.getElementById('inv-admin-fecha-vend');
            const hoy = new Date().toISOString().split('T')[0];
            await _admin_renderVendedores(fEl?.value || hoy);
        } else {
            showToast(`❌ ${d.mensaje || d.error}`, 'danger');
        }
    } catch(e) {
        showToast(`❌ Error: ${e.message}`, 'danger');
    }
}

/** Diálogo para limpiar inventarios globalmente */
async function _admin_limpiarInventariosUI() {
    const hoy = new Date().toISOString().split('T')[0];
    const opc = prompt(`🗑️ LIMPIAR INVENTARIOS DIARIOS\n\n1 — Solo inventarios de HOY (${hoy})\n2 — TODOS los inventarios\n\nEl almacén general NO se modifica.\nEscribe 1 o 2:`);
    if (!opc) return;
    let payload = {};
    if (opc.trim()==='1') payload={fecha:hoy};
    else if (opc.trim()==='2') payload={};
    else { tpvAlert('Opción inválida'); return; }
    const desc = opc.trim()==='1' ? `inventarios de HOY (${hoy})` : 'TODOS los inventarios';
    if (!(await tpvConfirm(`⛔ ¿Confirmar eliminación de ${desc}?\n\nLos vendedores quedarán sin stock asignado.`))) return;
    fetch('/api/inventario/diario/limpiar',{
        method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
    }).then(r=>r.json()).then(data=>{
        if (data.ok) {
            if (typeof showToast==='function') showToast(`✅ ${data.mensaje}`,'success');
            const fechaEl=document.getElementById('inv-admin-fecha-vend');
            _admin_renderVendedores(fechaEl?.value||hoy);
        } else { tpvAlert('Error: '+data.mensaje); }
    }).catch(e=>tpvAlert('Error: '+e.message));
}

// ══════════════════════════════════════════════
//  GASTOS / INVERSIÓN (Admin)
// ══════════════════════════════════════════════
let _gastos = [];

async function _admin_cargarGastos() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane) return;

    let wrap = document.getElementById('inv-admin-gastos-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.id = 'inv-admin-gastos-wrap';
        wrap.className = 'mt-0';
        pane.appendChild(wrap);
    }
    wrap.style.display = '';

    // Cargar gastos del servidor — filtrar por mes actual por defecto
    try {
        const hoy   = new Date().toISOString().split('T')[0];
        const mesInicio = hoy.slice(0,7) + '-01';          // primer día del mes
        const url   = `/api/gastos?desde=${mesInicio}&hasta=${hoy}`;
        const res   = await fetch(url, { credentials: 'same-origin' });
        const data  = await res.json();
        _gastos = data.gastos || [];
    } catch(e) { _gastos = []; }

    _admin_renderGastos();
}

function _admin_renderGastos() {
    const wrap = document.getElementById('inv-admin-gastos-wrap');
    if (!wrap) return;

    const totalGastos = _gastos.reduce((s,g) => s + parseFloat(g.monto||0), 0);

    wrap.innerHTML = `
    <div class="glass-card mb-3">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h5 class="fw-bold mb-0"><i class="bi bi-cash-stack me-2 text-warning"></i>Gastos e Inversión</h5>
        <span class="badge bg-secondary">${new Date().toLocaleDateString('es',{month:'long',year:'numeric'})}</span>
      </div>

      <!-- Formulario nuevo gasto -->
      <div class="card mb-4">
        <div class="card-body">
          <h6 class="fw-bold mb-3"><i class="bi bi-plus-circle me-1 text-success"></i>Registrar Gasto</h6>
          <div class="row g-2">
            <div class="col-12 col-md-4">
              <label class="form-label small fw-semibold">Descripción *</label>
              <input type="text" id="gasto-desc" class="form-control form-control-sm" placeholder="Ej: Compra de productos">
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label small fw-semibold">Monto *</label>
              <input type="number" id="gasto-monto" class="form-control form-control-sm" min="0" step="0.01" placeholder="0.00">
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label small fw-semibold">Categoría</label>
              <select id="gasto-cat" class="form-select form-select-sm">
                <option>Compras</option>
                <option>Transporte</option>
                <option>Servicios</option>
                <option>Salarios</option>
                <option>Mantenimiento</option>
                <option>Marketing</option>
                <option>Otros</option>
              </select>
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label small fw-semibold">Fecha</label>
              <input type="date" id="gasto-fecha" class="form-control form-control-sm"
                     value="${new Date().toISOString().split('T')[0]}">
            </div>
            <div class="col-6 col-md-2 d-flex align-items-end">
              <button class="btn btn-success btn-sm w-100" onclick="_admin_guardarGasto()">
                <i class="bi bi-floppy-fill me-1"></i>Guardar
              </button>
            </div>
          </div>
          <div class="mt-2">
            <label class="form-label small fw-semibold">Nota (opcional)</label>
            <input type="text" id="gasto-nota" class="form-control form-control-sm" placeholder="Detalles adicionales">
          </div>
        </div>
      </div>

      <!-- Resumen -->
      <div class="row g-3 mb-3">
        <div class="col-6 col-md-3">
          <div class="card text-center border-warning">
            <div class="card-body py-2">
              <div class="text-muted small">Total Gastos</div>
              <div class="fw-bold text-warning fs-5">$${totalGastos.toFixed(2)}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card text-center border-danger">
            <div class="card-body py-2">
              <div class="text-muted small">Gastos Operativos</div>
              <div class="fw-bold text-danger fs-5" id="inv-total-inversion">$${totalGastos.toFixed(2)}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card text-center border-info">
            <div class="card-body py-2">
              <div class="text-muted small">Registros</div>
              <div class="fw-bold text-info fs-5">${_gastos.length}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card text-center border-secondary">
            <div class="card-body py-2">
              <div class="text-muted small">Filtrar mes</div>
              <input type="month" id="gasto-filtro-mes" class="form-control form-control-sm"
                     value="${new Date().toISOString().slice(0,7)}"
                     onchange="_admin_renderGastosFiltrados()">
            </div>
          </div>
        </div>
      </div>

      <!-- Tabla gastos -->
      <div class="table-responsive">
        <table class="table table-sm table-hover align-middle" style="font-size:.85rem">
          <thead class="table-warning">
            <tr><th>#</th><th>Fecha</th><th>Descripción</th><th>Categoría</th>
                <th class="text-end">Monto</th><th>Nota</th><th></th></tr>
          </thead>
          <tbody id="gastos-tabla-body">
            ${_admin_gastosFilas(_gastos)}
          </tbody>
          <tfoot class="table-secondary fw-bold">
            <tr>
              <td colspan="4" class="text-end">TOTAL</td>
              <td class="text-end text-warning">$${totalGastos.toFixed(2)}</td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>`;
}

function _admin_gastosFilas(lista) {
    if (!lista.length) return '<tr><td colspan="7" class="text-center text-muted py-3">Sin gastos registrados.</td></tr>';
    return lista.map((g, i) => `<tr>
      <td>${i+1}</td>
      <td>${g.fecha}</td>
      <td class="fw-semibold">${g.descripcion}</td>
      <td><span class="badge bg-secondary">${g.categoria||'Otros'}</span></td>
      <td class="text-end fw-bold text-warning">$${parseFloat(g.monto||0).toFixed(2)}</td>
      <td class="text-muted small">${g.nota||''}</td>
      <td><button class="btn btn-sm btn-outline-danger py-0" onclick="_admin_eliminarGasto('${g.gasto_id}')">
            <i class="bi bi-trash"></i></button></td>
    </tr>`).join('');
}

async function _admin_renderGastosFiltrados() {
    const mes = document.getElementById('gasto-filtro-mes')?.value;
    if (mes) {
        // Recargar del servidor con el rango del mes seleccionado
        try {
            const inicio = mes + '-01';
            const fin    = new Date(mes.slice(0,4), parseInt(mes.slice(5,7)), 0)
                               .toISOString().split('T')[0]; // último día del mes
            const res  = await fetch(`/api/gastos?desde=${inicio}&hasta=${fin}`, { credentials:'same-origin' });
            const data = await res.json();
            _gastos = data.gastos || [];
        } catch(e) {}
    }
    const filtrados = mes ? _gastos.filter(g => g.fecha?.startsWith(mes)) : _gastos;
    const body = document.getElementById('gastos-tabla-body');
    if (body) body.innerHTML = _admin_gastosFilas(filtrados);
    const total = filtrados.reduce((s,g) => s + parseFloat(g.monto||0), 0);
    const inv = document.getElementById('inv-total-inversion');
    if (inv) inv.textContent = '$' + total.toFixed(2);
}

async function _admin_guardarGasto() {
    const desc  = document.getElementById('gasto-desc')?.value.trim();
    const monto = parseFloat(document.getElementById('gasto-monto')?.value) || 0;
    const cat   = document.getElementById('gasto-cat')?.value || 'Otros';
    const fecha = document.getElementById('gasto-fecha')?.value || new Date().toISOString().split('T')[0];
    const nota  = document.getElementById('gasto-nota')?.value.trim() || '';

    if (!desc)   return _toast('La descripción es obligatoria.', 'warning');
    if (monto<=0) return _toast('El monto debe ser mayor a 0.', 'warning');

    try {
        const res  = await fetch('/api/gastos', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({ descripcion:desc, monto, categoria:cat, fecha, nota })
        });
        const data = await res.json();
        if (res.ok) {
            _toast('✅ Gasto registrado', 'success');
            ['gasto-desc','gasto-monto','gasto-nota'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = '';
            });
            // Actualizar filtro de mes al mes del gasto guardado
            const mesSel = document.getElementById('gasto-filtro-mes');
            if (mesSel) mesSel.value = fecha.slice(0,7);
            await _admin_cargarGastos();
        } else {
            _toast(data.error || 'Error al guardar', 'danger');
        }
    } catch(e) { _toast('Error de conexión', 'danger'); }
}

async function _admin_eliminarGasto(gasto_id) {
    if (!(await tpvConfirm('¿Eliminar este gasto?'))) return;
    try {
        const res = await fetch(`/api/gastos/${gasto_id}`, { method:'DELETE', credentials:'same-origin' });
        if (res.ok) { _toast('Gasto eliminado', 'success'); await _admin_cargarGastos(); }
    } catch(e) {}
}


// ══════════════════════════════════════════════════════════════
//  CONFIGURACIÓN DE TIENDA (Admin / Desarrollador)
// ══════════════════════════════════════════════════════════════
let _cfg_tienda_id = null;

async function cfg_cargarTienda() {
    try {
        const res  = await fetch('/api/tiendas', { credentials: 'same-origin' });
        const data = await res.json();
        const uid  = AUTH.usuario?.usuario_id;
        const t    = (data.tiendas || []).find(x => x.admin_id === uid) || (data.tiendas || [])[0];
        if (!t) return;
        _cfg_tienda_id = t.tienda_id;
        const inp = document.getElementById('cfg-tienda-nombre');
        if (inp) inp.value = t.nombre || '';
        if (t.imagen) {
            const img  = document.getElementById('cfg-tienda-img-el');
            const wrap = document.getElementById('cfg-tienda-img-wrap');
            if (img && wrap) { img.src = t.imagen; wrap.classList.remove('d-none'); }
        }
    } catch(e) {}
}

function cfg_previewTienda(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        const img  = document.getElementById('cfg-tienda-img-el');
        const wrap = document.getElementById('cfg-tienda-img-wrap');
        if (img && wrap) { img.src = e.target.result; wrap.classList.remove('d-none'); }
    };
    reader.readAsDataURL(file);
}

function cfg_quitarImgTienda() {
    const img  = document.getElementById('cfg-tienda-img-el');
    const wrap = document.getElementById('cfg-tienda-img-wrap');
    if (img)  img.src = '';
    if (wrap) wrap.classList.add('d-none');
    const inp = document.getElementById('cfg-tienda-img-file');
    if (inp)  inp.value = '';
}

async function cfg_guardarTienda() {
    const rolActual = window.AUTH?.usuario?.rol;
    if (!rolActual || !['administrador','desarrollador'].includes(rolActual)) {
        if (typeof _toast === 'function') _toast('Solo el Administrador puede cambiar la tienda.','warning');
        return;
    }
    const nombre = document.getElementById('cfg-tienda-nombre')?.value?.trim();
    const imgEl  = document.getElementById('cfg-tienda-img-el');
    const imagen = imgEl?.src && !imgEl.src.startsWith(window.location.href) ? imgEl.src : null;

    if (!nombre) { _toast('Escribe el nombre de la tienda.', 'warning'); return; }
    try {
        const esNueva = !_cfg_tienda_id;
        const url     = esNueva ? '/api/tiendas' : `/api/tiendas/${_cfg_tienda_id}`;
        const method  = esNueva ? 'POST' : 'PATCH';
        const body    = { nombre };
        if (imagen) body.imagen = imagen;

        const res  = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok) {
            _toast('\u2705 Tienda guardada', 'success');
            _cfg_tienda_id = data.tienda_id || _cfg_tienda_id;
        } else {
            _toast(data.error || 'Error al guardar', 'danger');
        }
    } catch(e) { _toast('Error de conexi\u00f3n', 'danger'); }
}

// Preview imagen producto (modal gestión)
function g_previewImg(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        const img  = document.getElementById('g-img-el');
        const wrap = document.getElementById('g-img-wrap');
        if (img && wrap) { img.src = e.target.result; wrap.classList.remove('d-none'); }
    };
    reader.readAsDataURL(file);
}

function g_quitarImg() {
    const img  = document.getElementById('g-img-el');
    const wrap = document.getElementById('g-img-wrap');
    if (img)  img.src = '';
    if (wrap) wrap.classList.add('d-none');
    const inp = document.getElementById('gestion-producto-imagen-local');
    if (inp)  inp.value = '';
}

async function auth_logout() {
    var _ok = (typeof tpvConfirm === 'function')
        ? await tpvConfirm({ title: 'Cerrar sesión', message: '¿Seguro que deseas cerrar la sesión actual?', okText: 'Cerrar sesión', cancelText: 'Quedarme', danger: true })
        : confirm('¿Cerrar sesión?');
    if (!_ok) return;

    // Auto-backup y logout en segundo plano (no bloquear la salida).
    // Antes eran 'await' secuenciales y si el backup tardaba, el logout se
    // quedaba "validando". Ahora se disparan sin esperar, con timeout corto.
    try {
        var _ctl = new AbortController();
        setTimeout(function(){ try{_ctl.abort();}catch(e){} }, 2500);
        fetch('/api/auth/auto-backup', { method:'POST', credentials:'same-origin', signal:_ctl.signal }).catch(function(){});
    } catch(e) {}
    try {
        fetch('/api/auth/logout', { method:'POST', credentials:'same-origin' }).catch(function(){});
    } catch(e) {}

    // Cerrar SSE
    if (_sseConn) { try { _sseConn.close(); } catch(e){} _sseConn = null; }
    if (AUTH.pollingNotif) { clearInterval(AUTH.pollingNotif); AUTH.pollingNotif = null; }

    // Limpiar y OCULTAR el panel debug al cerrar sesión (no debe verse en login)
    if (typeof window._dbg_limpiar === 'function') window._dbg_limpiar();
    try {
        var _dbgPanel = document.getElementById('dbg-v2');
        if (_dbgPanel) _dbgPanel.remove();   // quitar del DOM
        if (window._DBG) { window._DBG.expanded = false; window._DBG.activo = false; }
    } catch(e) {}
    try { _tpv_limpiarEstadoUsuarioAnterior(); } catch(e){}
    AUTH.usuario = null;
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
                AUTH.pollingNotif = setInterval(_pollPedidos, 20000);
                _pollPedidos();
            }
        };

        // Primera carga inmediata
        _pollPedidos();
    } else {
        // Navegador sin SSE: polling clásico 8 s
        AUTH.pollingNotif = setInterval(_pollPedidos, 20000);
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
    if (!(await tpvConfirm(`¿Desactivar a "${nombre}"?\nNo podrá iniciar sesión.`))) return;
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
    if (!(await tpvConfirm(`¿Revocar licencia de "${nombre}"?`))) return;
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