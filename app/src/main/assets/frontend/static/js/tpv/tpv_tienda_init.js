// tpv_tienda_cliente.js — Tienda: clientes, pedidos, auth cliente, productos por tienda
//  MÓDULO TIENDA — Estado global y constantes
// ══════════════════════════════════════════════════════════════
const TPV_TIENDA = {
    // Usuario cliente autenticado en este dispositivo
    clienteActual: null,
    // Tienda seleccionada para comprar
    tiendaSeleccionada: null,
    // Carrito actual
    carrito: [],
    // Cola offline de pedidos pendientes de sincronizar
    colaPendiente: [],
    // Pedido activo en modal de detalle (vendedor)
    pedidoEnDetalle: null,
    // Polling interval id
    pollingId: null,
    // Rol detectado del sistema principal
    rolSistema: null
};

// DB keys (IndexedDB compartida con el estado TPV)
const TIENDA_STORE = {
    clientes:  'tienda_clientes',
    pedidos:   'tienda_pedidos',
    tiendas:   'tienda_tiendas',
    cola:      'tienda_cola_offline'
};

// ── IndexedDB helpers simples para tienda ────────────────────
const tiendaDB = {
    _db: null,
    async open() {
        if (this._db) return this._db;
        return new Promise((res, rej) => {
            const req = indexedDB.open('tiendaTPV', 1);
            req.onupgradeneeded = e => {
                const db = e.target.result;
                ['clientes','pedidos','tiendas','cola'].forEach(s => {
                    if (!db.objectStoreNames.contains(s))
                        db.createObjectStore(s, { keyPath: 'id' });
                });
            };
            req.onsuccess = e => { this._db = e.target.result; res(this._db); };
            req.onerror   = () => rej(req.error);
        });
    },
    async getAll(store) {
        const db = await this.open();
        return new Promise((res, rej) => {
            const tx  = db.transaction(store, 'readonly');
            const req = tx.objectStore(store).getAll();
            req.onsuccess = () => res(req.result || []);
            req.onerror   = () => rej(req.error);
        });
    },
    async get(store, id) {
        const db = await this.open();
        return new Promise((res, rej) => {
            const tx  = db.transaction(store, 'readonly');
            const req = tx.objectStore(store).get(id);
            req.onsuccess = () => res(req.result || null);
            req.onerror   = () => rej(req.error);
        });
    },
    async put(store, obj) {
        const db = await this.open();
        return new Promise((res, rej) => {
            const tx  = db.transaction(store, 'readwrite');
            const req = tx.objectStore(store).put(obj);
            req.onsuccess = () => res(req.result);
            req.onerror   = () => rej(req.error);
        });
    },
    async delete(store, id) {
        const db = await this.open();
        return new Promise((res, rej) => {
            const tx  = db.transaction(store, 'readwrite');
            const req = tx.objectStore(store).delete(id);
            req.onsuccess = () => res();
            req.onerror   = () => rej(req.error);
        });
    }
};

// ── Helpers de ID y formato ───────────────────────────────────
function tienda_uid() {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
}
function tienda_fmt(num) {
    return '$' + parseFloat(num || 0).toFixed(2);
}
function tienda_now() {
    return new Date().toISOString();
}

// ══════════════════════════════════════════════════════════════
//  INICIALIZACIÓN — se llama al activar la pestaña
// ══════════════════════════════════════════════════════════════
async function tienda_init() {
    // Detectar rol del sistema principal (si existe sesión)
    try {
        const resp = await fetch('/api/auth/me');
        if (resp.ok) {
            const data = await resp.json();
            if (data.autenticado) {
                TPV_TIENDA.rolSistema = data.usuario.rol;
                TPV_TIENDA.usuarioSistema = data.usuario;
            }
        }
    } catch(e) { /* offline, continuar */ }

    // Cargar cola offline
    TPV_TIENDA.colaPendiente = await tiendaDB.getAll('cola');
    tienda_mostrarBadgeOffline();

    // Intentar sincronizar cola si hay conexión
    if (navigator.onLine) tienda_sincronizarCola();

    // Renderizar vista según contexto
    if (['administrador','supervisor','desarrollador','vendedor'].includes(TPV_TIENDA.rolSistema)) {
        await tienda_renderVendedor();
    } else if (TPV_TIENDA.rolSistema === 'cliente') {
        // Cliente autenticado via sistema principal — mapear AUTH.usuario a TPV_TIENDA.clienteActual
        if (!TPV_TIENDA.clienteActual && window.AUTH?.usuario) {
            TPV_TIENDA.clienteActual = {
                id: window.AUTH.usuario.id,
                nombre: window.AUTH.usuario.nombre,
                email: window.AUTH.usuario.email || window.AUTH.usuario.username,
                rol: 'cliente'
            };
        }
        if (TPV_TIENDA.clienteActual) {
            await tienda_renderCliente();
        } else {
            tienda_renderBienvenida();
        }
    } else if (TPV_TIENDA.clienteActual) {
        await tienda_renderCliente();
    } else {
        tienda_renderBienvenida();
    }

    // Iniciar polling solo para roles con panel de gestión
    if (['vendedor','administrador','desarrollador'].includes(TPV_TIENDA.rolSistema)) {
        tienda_iniciarPolling();
    }

    // Escuchar cambios de conexión para sincronizar
    window.addEventListener('online', () => tienda_sincronizarCola());
}

// ══════════════════════════════════════════════════════════════
//  VISTAS
// ══════════════════════════════════════════════════════════════

// ── Pantalla de bienvenida (usuario no identificado) ─────────
function tienda_renderBienvenida() {
    document.getElementById('tienda-root').innerHTML = `
    <div class="tienda-hero">
        <div class="position-relative">
            <h2 class="fw-bold mb-1"><i class="bi bi-shop me-2"></i>Tienda en Línea</h2>
            <p class="opacity-75 mb-3">Elige tu tienda y compra desde tu dispositivo. Todo funciona en tu red WiFi local.</p>
            <div class="d-flex flex-wrap gap-2">
                <button class="btn fw-bold px-4 py-2" onclick="tienda_abrirAuth()" style="background:white;color:#6366f1;border-radius:.8rem;">
                    <i class="bi bi-person-circle me-2"></i>Entrar como Cliente
                </button>
            </div>
        </div>
    </div>
    <div class="glass-card">
        <h5 class="fw-bold mb-4"><i class="bi bi-grid-3x3-gap me-2 text-primary"></i>Tiendas disponibles</h5>
        <div id="tienda-lista-publico" class="row g-3"></div>
    </div>`;
    tienda_cargarListaTiendas('tienda-lista-publico', false);
}

// ── Vista del cliente autenticado ────────────────────────────
async function tienda_renderCliente() {
    const c = TPV_TIENDA.clienteActual;
    const carritoCount = TPV_TIENDA.carrito.reduce((s, i) => s + i.cantidad, 0);
    document.getElementById('tienda-root').innerHTML = `
    <div class="tienda-hero">
        <div class="position-relative d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div class="d-flex align-items-center gap-3">
                ${c.foto ? `<img src="${c.foto}" alt="perfil"
                    style="width:52px;height:52px;border-radius:50%;object-fit:cover;
                           border:2.5px solid rgba(255,255,255,.7);box-shadow:0 2px 8px #0004">` : 
                  `<div style="width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,.2);
                               display:flex;align-items:center;justify-content:center;font-size:1.5rem;">
                    <i class="bi bi-person-fill"></i></div>`}
                <div>
                    <h3 class="fw-bold mb-0">¡Hola, ${c.nombre}! 👋</h3>
                    <p class="opacity-75 mb-0 small">${c.email || ''}</p>
                </div>
            </div>
            <div class="d-flex gap-2">
                <button class="btn fw-bold" onclick="tienda_abrirCarrito()" style="background:white;color:#3b82f6;border-radius:.8rem;">
                    <i class="bi bi-cart3 me-1"></i>Carrito
                    <span class="badge bg-danger ms-1" id="carrito-count-btn">${carritoCount || ''}</span>
                </button>
                <button class="btn fw-bold" onclick="tienda_verMisPedidos()" style="background:rgba(255,255,255,.15);color:white;border:1.5px solid rgba(255,255,255,.5);border-radius:.8rem;">
                    <i class="bi bi-clock-history me-1"></i>Mis Pedidos
                </button>
                <button class="btn btn-sm" onclick="tienda_logoutCliente()" style="background:rgba(255,255,255,.1);color:white;border-radius:.6rem;" title="Cerrar sesión cliente">
                    <i class="bi bi-box-arrow-right"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- Sección: elegir tienda -->
    <div class="glass-card mb-3" id="seccion-elegir-tienda">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold mb-0"><i class="bi bi-geo-alt me-2 text-primary"></i>Elige una tienda</h5>
        </div>
        <div id="tienda-lista-cliente" class="row g-3 mb-3"></div>
    </div>

    <!-- Sección: productos de la tienda seleccionada -->
    <div id="seccion-productos-tienda" class="d-none">
        <div class="glass-card">
            <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                <div>
                    <h5 class="fw-bold mb-0" id="nombre-tienda-activa">Productos</h5>
                    <small class="text-muted" id="desc-tienda-activa"></small>
                </div>
                <div class="d-flex gap-2">
                    <input type="text" class="form-control form-control-sm" id="tienda-buscador" placeholder="Buscar producto..." oninput="tienda_filtrarProductos()" style="max-width:180px;">
                    <select class="form-select form-select-sm" id="tienda-filtro-cat" onchange="tienda_filtrarProductos()" style="max-width:140px;">
                        <option value="">Todas las categorías</option>
                    </select>
                    <button class="btn btn-sm btn-outline-secondary" onclick="tienda_deseleccionarTienda()">
                        <i class="bi bi-arrow-left me-1"></i>Cambiar
                    </button>
                </div>
            </div>
            <div class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-3" id="tienda-productos-grid"></div>
        </div>
    </div>

    <!-- Sección: mis pedidos -->
    <div id="seccion-mis-pedidos" class="d-none">
        <div class="glass-card">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h5 class="fw-bold mb-0"><i class="bi bi-clock-history me-2"></i>Mis Pedidos</h5>
                <button class="btn btn-sm btn-outline-primary" onclick="tienda_renderCliente()"><i class="bi bi-arrow-left me-1"></i>Volver</button>
            </div>
            <div id="mis-pedidos-lista"></div>
        </div>
    </div>`;

    tienda_cargarListaTiendas('tienda-lista-cliente', true);
}

// ── Vista del vendedor / admin ────────────────────────────────
async function tienda_renderVendedor() {
    const u = TPV_TIENDA.usuarioSistema;
    document.getElementById('tienda-root').innerHTML = `
    <div class="tienda-hero" style="background:linear-gradient(135deg,#f59e0b,#d97706);">
        <div class="position-relative d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
                <h3 class="fw-bold mb-1"><i class="bi bi-bell me-2"></i>Panel de Pedidos</h3>
                <p class="opacity-75 mb-0">Gestiona los pedidos de los clientes en tiempo real.</p>
            </div>
            <div class="d-flex gap-2 flex-wrap">
                ${u?.rol === 'administrador' || u?.rol === 'desarrollador' ? `
                <button class="btn fw-bold" onclick="tienda_tabAdmin('tiendas')" style="background:white;color:#d97706;border-radius:.8rem;">
                    <i class="bi bi-shop me-1"></i>Mis Tiendas
                </button>
                <button class="btn fw-bold" onclick="tienda_tabAdmin('clientes')" style="background:rgba(255,255,255,.15);color:white;border:1.5px solid rgba(255,255,255,.5);border-radius:.8rem;">
                    <i class="bi bi-people me-1"></i>Clientes
                </button>` : ''}
                <button class="btn fw-bold" onclick="tienda_tabAdmin('pedidos')" style="background:rgba(255,255,255,.15);color:white;border:1.5px solid rgba(255,255,255,.5);border-radius:.8rem;">
                    <i class="bi bi-bag me-1"></i>Todos los Pedidos
                </button>
            </div>
        </div>
    </div>

    <!-- Pedidos pendientes (alerta) -->
    <div id="panel-pedidos-pendientes" class="glass-card mb-3">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold mb-0">
                <i class="bi bi-hourglass-split me-2 text-warning"></i>Pedidos Pendientes
                <span id="count-pendientes" class="badge bg-warning text-dark ms-2">0</span>
            </h5>
            <button class="btn btn-sm btn-outline-secondary" onclick="tienda_cargarPedidosVendedor()">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
        </div>
        <div id="lista-pedidos-pendientes">
            <div class="text-center text-muted py-4"><i class="bi bi-inbox fs-2 d-block mb-2"></i>Sin pedidos pendientes</div>
        </div>
    </div>

    <!-- Panel secundario (Tiendas / Clientes / Todos los pedidos) -->
    <div id="panel-admin-secundario" class="d-none glass-card">
        <div id="panel-admin-contenido"></div>
    </div>`;

    await tienda_cargarPedidosVendedor();
}

// ══════════════════════════════════════════════════════════════
//  AUTENTICACIÓN DE CLIENTES
// ══════════════════════════════════════════════════════════════

function tienda_abrirAuth() {
    tienda_switchAuthTab('login');
    new bootstrap.Modal(document.getElementById('clienteAuthModal')).show();
}

function tienda_switchAuthTab(tab) {
    document.getElementById('clienteLoginForm').classList.toggle('d-none', tab !== 'login');
    document.getElementById('clienteRegistroForm').classList.toggle('d-none', tab !== 'registro');
    document.getElementById('btn-tab-login').style.background = tab === 'login' ? '#6366f1' : '#e2e8f0';
    document.getElementById('btn-tab-login').style.color = tab === 'login' ? 'white' : '#475569';
    document.getElementById('btn-tab-registro').style.background = tab === 'registro' ? '#6366f1' : '#e2e8f0';
    document.getElementById('btn-tab-registro').style.color = tab === 'registro' ? 'white' : '#475569';
}

async function tienda_loginCliente() {
    const username = document.getElementById('cli-login-user').value.trim();
    const password = document.getElementById('cli-login-pass').value;
    if (!username || !password) return showToast('Completa los campos', 'warning');

    try {
        // Intentar contra el servidor
        const resp = await fetch('/api/clientes/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (data.ok) {
            TPV_TIENDA.clienteActual = data.cliente;
            tienda_guardarClienteLocal(data.cliente);
            bootstrap.Modal.getInstance(document.getElementById('clienteAuthModal'))?.hide();
            showToast(`¡Bienvenido, ${data.cliente.nombre}!`, 'success');
            await tienda_renderCliente();
            return;
        }
        showToast(data.error || 'Credenciales incorrectas', 'danger');
    } catch(e) {
        // Offline: verificar contra IndexedDB local
        const clientes = await tiendaDB.getAll('clientes');
        const cliente = clientes.find(c =>
            (c.username === username || c.email === username) &&
            c.password_plain === password   // Solo para modo demo offline
        );
        if (cliente) {
            TPV_TIENDA.clienteActual = cliente;
            bootstrap.Modal.getInstance(document.getElementById('clienteAuthModal'))?.hide();
            showToast(`¡Bienvenido (offline), ${cliente.nombre}!`, 'info');
            await tienda_renderCliente();
        } else {
            showToast('Sin conexión. Verifica tu WiFi o regístrate primero.', 'warning');
        }
    }
}

// ── helpers foto de perfil ──────────────────────────────────
function cli_previewFoto(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        const img  = document.getElementById('cli-foto-img');
        const wrap = document.getElementById('cli-foto-preview');
        if (img && wrap) { img.src = e.target.result; wrap.classList.remove('d-none'); }
    };
    reader.readAsDataURL(file);
}
function cli_quitarFoto() {
    const inp  = document.getElementById('cli-reg-foto');
    const img  = document.getElementById('cli-foto-img');
    const wrap = document.getElementById('cli-foto-preview');
    if (inp)  inp.value  = '';
    if (img)  img.src   = '';
    if (wrap) wrap.classList.add('d-none');
}

async function tienda_registrarCliente() {
    const nombre   = document.getElementById('cli-reg-nombre')?.value.trim();
    const email    = document.getElementById('cli-reg-email')?.value.trim();
    const password = document.getElementById('cli-reg-pass')?.value;
    const fotoEl   = document.getElementById('cli-foto-img');
    const foto     = (fotoEl?.src && fotoEl.src !== window.location.href) ? fotoEl.src : null;

    if (!nombre)   return showToast('El nombre es obligatorio.', 'warning');
    if (!email || !email.includes('@')) return showToast('Introduce un correo válido.', 'warning');
    if (!password || password.length < 4) return showToast('La contraseña debe tener al menos 4 caracteres.', 'warning');

    const clienteObj = {
        id:      tienda_uid(),
        nombre, username: email, email, foto,
        creado:  tienda_now(),
        activo:  true
    };

    try {
        const resp = await fetch('/api/clientes/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, username: email, email, password, foto })
        });
        const data = await resp.json();
        if (resp.ok && data.ok) {
            clienteObj.id = data.cliente_id || clienteObj.id;
        } else {
            return showToast(data.error || 'Error al registrar.', 'danger');
        }
    } catch(e) {
        tienda_agregarCola({ tipo: 'registrar_cliente', datos: { ...clienteObj, password_plain: password } });
        showToast('Sin conexión — se sincronizará luego.', 'info');
    }

    TPV_TIENDA.clienteActual = clienteObj;
    tienda_guardarClienteLocal(clienteObj);
    bootstrap.Modal.getInstance(document.getElementById('clienteAuthModal'))?.hide();
    showToast(`¡Bienvenido, ${nombre}!`, 'success');
    await tienda_renderCliente();
}

function tienda_guardarClienteLocal(cliente) {
    try { localStorage.setItem('tienda_cliente_actual', JSON.stringify(cliente)); } catch(e) {}
}
function tienda_cargarClienteLocal() {
    try {
        const c = localStorage.getItem('tienda_cliente_actual');
        return c ? JSON.parse(c) : null;
    } catch(e) { return null; }
}
function tienda_logoutCliente() {
    TPV_TIENDA.clienteActual = null;
    TPV_TIENDA.carrito = [];
    TPV_TIENDA.tiendaSeleccionada = null;
    try { localStorage.removeItem('tienda_cliente_actual'); } catch(e) {}
    tienda_renderBienvenida();
    showToast('Sesión cerrada', 'info');
}

// ══════════════════════════════════════════════════════════════
//  TIENDAS
// ══════════════════════════════════════════════════════════════

