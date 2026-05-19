// tpv_autenticacion.js — Login, roles, tabs, biometría
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

const ROL_INFO = {
    desarrollador: { color:'#7c3aed', icono:'bi-code-slash',    label:'Desarrollador' },
    administrador: { color:'#0d6efd', icono:'bi-shield-fill',   label:'Administrador' },
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
    'seguridad-tab':          ['desarrollador'],
};

// ══════════════════════════════════════════════════════════════
//  CSS
// ══════════════════════════════════════════════════════════════
const _css = document.createElement('style');
_css.textContent = `
#login-screen {
    position:fixed;inset:0;z-index:9999;
    background:linear-gradient(135deg,#0d1b2a 0%,#1a3a5c 55%,#0d6efd 100%);
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
    background:linear-gradient(135deg,#0d6efd,#0a58ca);
    color:white;font-size:2rem;
    display:flex;align-items:center;justify-content:center;
    margin:0 auto 1rem;box-shadow:0 8px 20px rgba(13,110,253,.35);
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
.login-input:focus{border-color:#0d6efd;box-shadow:0 0 0 3px rgba(13,110,253,.12)}
.pw-eye{
    position:absolute;right:.75rem;top:50%;transform:translateY(-50%);
    background:none;border:none;cursor:pointer;color:#94a3b8;
    padding:.3rem;font-size:1rem;line-height:1;transition:color .15s;
}
.pw-eye:hover{color:#0d6efd}
.login-btn{
    width:100%;padding:.85rem;border:none;border-radius:.75rem;
    background:linear-gradient(135deg,#0d6efd,#0a58ca);color:white;
    font-size:1rem;font-weight:700;cursor:pointer;margin-top:.25rem;
    transition:transform .15s,box-shadow .15s;
    box-shadow:0 4px 14px rgba(13,110,253,.35);
}
.login-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 6px 20px rgba(13,110,253,.45)}
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
        <h2 class="login-title">Sistema TPV</h2>
        <div style="display:flex;background:#f1f5f9;border-radius:.75rem;padding:4px;margin-bottom:1.2rem">
            <button id="modo-staff-btn" onclick="auth_setModo('staff')"
                style="flex:1;padding:.5rem;border:none;border-radius:.6rem;font-weight:600;font-size:.88rem;cursor:pointer;background:#0d6efd;color:white">
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
            <strong>Flask no responde.</strong> Abre TPV y ejecuta:<br>
            <code>python app.py</code>
        </div>
        <div id="panel-staff" style="display:none">
            <p class="login-sub" style="margin-bottom:1rem">Acceso para empleados</p>
            <div class="login-field">
                <label><i class="bi bi-person me-1"></i>Usuario</label>
                <input id="login-username" class="login-input" type="text" placeholder="ej: usuario" autocomplete="username">
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
            <button id="bio-btn" class="login-btn" style="background:#00b894;margin-top:8px;display:none" onclick="auth_biometric()"><i class="bi bi-fingerprint"></i> Huella digital</button>
            <div class="login-footer"><i class="bi bi-shield-lock me-1"></i>Acceso restringido al personal</div>
        </div>
        <div id="panel-cliente" style="display:none">
            <div style="display:flex;border-bottom:2px solid #e2e8f0;margin-bottom:1rem">
                <button id="cli-tab-login" onclick="auth_cliTab('login')"
                    style="flex:1;padding:.55rem;border:none;background:none;font-weight:700;font-size:.88rem;cursor:pointer;color:#0d6efd;border-bottom:2px solid #0d6efd;margin-bottom:-2px">
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
                    Sin cuenta: <a href="#" onclick="auth_cliTab('registro');return false" style="color:#0d6efd;font-weight:600">Registrate gratis</a>
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
                    Ya tienes cuenta: <a href="#" onclick="auth_cliTab('login');return false" style="color:#0d6efd;font-weight:600">Inicia sesion</a>
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
                <i class="bi bi-key-fill me-1"></i><span>Licencias</span>
            </button>
            <button id="btn-usuarios" class="ub-btn d-none" onclick="auth_abrirUsuarios()">
                <i class="bi bi-people-fill me-1"></i><span>Usuarios</span>
            </button>
            <button id="btn-debug-toggle" class="ub-btn d-none"
                    onclick="if(window.tpvDebugger)tpvDebugger.activar();else window._dbg_mostrar()"
                    style="background:rgba(34,197,94,.15);border-color:rgba(34,197,94,.4)"
                    title="Mostrar/Ocultar panel de debug">
                <i class="bi bi-bug-fill me-1"></i><span id="btn-debug-label">Debug</span>
            </button>
            <button class="ub-btn out" onclick="auth_logout()">
                <i class="bi bi-box-arrow-right me-1"></i><span>Salir</span>
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
               style="background:linear-gradient(135deg,#0d6efd,#0a58ca)">
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
