// tpv_tienda_cliente.js — Tienda: clientes, pedidos, auth cliente, productos por tienda
//  MÓDULO TIENDA — Estado global y constantes
// ══════════════════════════════════════════════════════════════
const TIENDA = {
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
                TIENDA.rolSistema = data.usuario.rol;
                TIENDA.usuarioSistema = data.usuario;
            }
        }
    } catch(e) { /* offline, continuar */ }

    // Cargar cola offline
    TIENDA.colaPendiente = await tiendaDB.getAll('cola');
    tienda_mostrarBadgeOffline();

    // Intentar sincronizar cola si hay conexión
    if (navigator.onLine) tienda_sincronizarCola();

    // Renderizar vista según contexto
    if (['administrador','supervisor','desarrollador','vendedor'].includes(TIENDA.rolSistema)) {
        await tienda_renderVendedor();
    } else if (TIENDA.rolSistema === 'cliente') {
        // Cliente autenticado via sistema principal — mapear AUTH.usuario a TIENDA.clienteActual
        if (!TIENDA.clienteActual && window.AUTH?.usuario) {
            TIENDA.clienteActual = {
                id: window.AUTH.usuario.id,
                nombre: window.AUTH.usuario.nombre,
                email: window.AUTH.usuario.email || window.AUTH.usuario.username,
                rol: 'cliente'
            };
        }
        if (TIENDA.clienteActual) {
            await tienda_renderCliente();
        } else {
            tienda_renderBienvenida();
        }
    } else if (TIENDA.clienteActual) {
        await tienda_renderCliente();
    } else {
        tienda_renderBienvenida();
    }

    // Iniciar polling solo para roles con panel de gestión
    if (['vendedor','administrador','desarrollador'].includes(TIENDA.rolSistema)) {
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
    const c = TIENDA.clienteActual;
    const carritoCount = TIENDA.carrito.reduce((s, i) => s + i.cantidad, 0);
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
    const u = TIENDA.usuarioSistema;
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
            TIENDA.clienteActual = data.cliente;
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
            TIENDA.clienteActual = cliente;
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

    TIENDA.clienteActual = clienteObj;
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
    TIENDA.clienteActual = null;
    TIENDA.carrito = [];
    TIENDA.tiendaSeleccionada = null;
    try { localStorage.removeItem('tienda_cliente_actual'); } catch(e) {}
    tienda_renderBienvenida();
    showToast('Sesión cerrada', 'info');
}

// ══════════════════════════════════════════════════════════════
//  TIENDAS
// ══════════════════════════════════════════════════════════════

async function tienda_cargarListaTiendas(containerId, seleccionable) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '<div class="col-12 text-center text-muted py-3"><div class="spinner-border spinner-border-sm me-2"></div>Cargando tiendas...</div>';

    let tiendas = [];
    try {
        const resp = await fetch('/api/tiendas');
        if (resp.ok) {
            const data = await resp.json();
            tiendas = data.tiendas || [];
            // Actualizar cache local
            for (const t of tiendas) await tiendaDB.put('tiendas', t);
        }
    } catch(e) {
        tiendas = await tiendaDB.getAll('tiendas');
    }

    if (tiendas.length === 0) {
        container.innerHTML = `<div class="col-12 text-center text-muted py-4">
            <i class="bi bi-shop fs-2 d-block mb-2 opacity-50"></i>
            <p>No hay tiendas registradas aún.</p>
            ${seleccionable ? '' : '<p class="small">El administrador debe registrar su tienda primero.</p>'}
        </div>`;
        return;
    }

    container.innerHTML = tiendas.map(t => `
    <div class="col-6 col-md-4 col-lg-3">
        <div class="tienda-shop-card h-100" onclick="${seleccionable ? `tienda_seleccionarTienda('${t.id}')` : ''}">
            <div class="shop-emoji">${t.emoji || '🏪'}</div>
            <h6 class="fw-bold mb-1">${t.nombre}</h6>
            <p class="text-muted small mb-2">${t.descripcion || ''}</p>
            <span class="badge ${t.activo ? 'bg-success' : 'bg-secondary'}">${t.activo ? 'Abierto' : 'Cerrado'}</span>
        </div>
    </div>`).join('');
}

async function tienda_seleccionarTienda(tiendaId) {
    const tiendas = await tiendaDB.getAll('tiendas');
    const tienda  = tiendas.find(t => t.id === tiendaId);
    if (!tienda) return;

    TIENDA.tiendaSeleccionada = tienda;

    // Marcar visualmente
    document.querySelectorAll('.tienda-shop-card').forEach(c => c.classList.remove('selected'));
    event?.currentTarget?.classList.add('selected');

    document.getElementById('seccion-elegir-tienda').classList.add('d-none');
    document.getElementById('seccion-productos-tienda').classList.remove('d-none');
    document.getElementById('nombre-tienda-activa').textContent = `🛒 ${tienda.nombre}`;
    document.getElementById('desc-tienda-activa').textContent = tienda.descripcion || '';

    await tienda_cargarProductosTienda(tienda);
}

function tienda_deseleccionarTienda() {
    TIENDA.tiendaSeleccionada = null;
    document.getElementById('seccion-productos-tienda').classList.add('d-none');
    document.getElementById('seccion-mis-pedidos').classList.add('d-none');
    document.getElementById('seccion-elegir-tienda').classList.remove('d-none');
}

async function tienda_cargarProductosTienda(tienda) {
    const grid = document.getElementById('tienda-productos-grid');
    grid.innerHTML = '<div class="col-12 text-center text-muted py-3"><div class="spinner-border spinner-border-sm me-2"></div>Cargando productos...</div>';

    let productos = [];
    try {
        const resp = await fetch(`/api/tiendas/${tienda.id}/productos`);
        if (resp.ok) {
            const data = await resp.json();
            productos = data.productos || [];
        }
    } catch(e) {
        // Offline: usar productos del tpvState si es la tienda local
        if (typeof tpvState !== 'undefined') {
            productos = (tpvState.productos || []).map(p => ({
                id: p.id, nombre: p.nombre, precio: p.precio,
                categoria: p.categoria, imagen: p.imagen,
                enOferta: p.enOferta, unidadMedida: p.unidadMedida || 'C/U'
            }));
        }
    }

    TIENDA._productosActuales = productos;

    // Llenar categorías
    const cats = [...new Set(productos.map(p => p.categoria).filter(Boolean))];
    const sel = document.getElementById('tienda-filtro-cat');
    sel.innerHTML = '<option value="">Todas las categorías</option>' +
        cats.map(c => `<option value="${c}">${c}</option>`).join('');

    tienda_renderProductosGrid(productos);
}

function tienda_filtrarProductos() {
    const q   = (document.getElementById('tienda-buscador')?.value || '').toLowerCase();
    const cat = document.getElementById('tienda-filtro-cat')?.value || '';
    const ps  = (TIENDA._productosActuales || []).filter(p => {
        const matchQ   = !q   || p.nombre.toLowerCase().includes(q);
        const matchCat = !cat || p.categoria === cat;
        return matchQ && matchCat;
    });
    tienda_renderProductosGrid(ps);
}

function tienda_renderProductosGrid(productos) {
    const grid = document.getElementById('tienda-productos-grid');
    if (!grid) return;
    if (!productos.length) {
        grid.innerHTML = '<div class="col-12 text-center text-muted py-4"><i class="bi bi-search fs-2 d-block mb-2 opacity-50"></i>No hay productos</div>';
        return;
    }
    grid.innerHTML = productos.map(p => {
        const enCarrito = TIENDA.carrito.find(i => i.id === p.id);
        return `
        <div class="col">
            <div class="tienda-card h-100" onclick="tienda_abrirProducto('${p.id}')">
                <div class="card-img-top">
                    ${p.imagen ? `<img src="${p.imagen}" alt="${p.nombre}" style="width:100%;height:140px;object-fit:cover;">` : `<span style="font-size:3rem;">${tienda_emojiCategoria(p.categoria)}</span>`}
                </div>
                <div class="card-body p-2">
                    ${p.enOferta ? '<span class="badge bg-danger mb-1">Oferta</span>' : ''}
                    <h6 class="fw-bold mb-1 lh-sm" style="font-size:.85rem;">${p.nombre}</h6>
                    <div class="d-flex justify-content-between align-items-center mt-1">
                        <span class="fw-bold text-success">${tienda_fmt(p.precio)}</span>
                        <button class="btn btn-sm fw-bold ${enCarrito ? 'btn-success' : 'btn-outline-primary'}" 
                                style="border-radius:.6rem;font-size:.75rem;padding:.25rem .6rem;"
                                onclick="event.stopPropagation();tienda_toggleCarrito('${p.id}')">
                            ${enCarrito ? `<i class="bi bi-cart-check"></i> ${enCarrito.cantidad}` : '<i class="bi bi-cart-plus"></i>'}
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');
}

function tienda_emojiCategoria(cat) {
    const m = { 'Bebidas':'🥤','Alimentos':'🍎','Snacks':'🍿','Limpieza':'🧹',
                'Higiene Personal':'🧼','Panadería':'🍞','Lácteos':'🥛','Carnes':'🥩',
                'Frutas y Verduras':'🥦','General':'📦' };
    return m[cat] || '🛍️';
}

function tienda_abrirProducto(id) {
    const p = (TIENDA._productosActuales || []).find(x => x.id === id);
    if (!p) return;
    const enCarrito = TIENDA.carrito.find(i => i.id === id);
    showToast(`${p.nombre} — ${tienda_fmt(p.precio)}. ${enCarrito ? `En carrito: ${enCarrito.cantidad}` : 'Toca el ícono + para agregar.'}`, 'info');
}

// ══════════════════════════════════════════════════════════════
//  CARRITO
// ══════════════════════════════════════════════════════════════

function tienda_toggleCarrito(prodId) {
    if (!TIENDA.clienteActual) { tienda_abrirAuth(); return; }
    const p = (TIENDA._productosActuales || []).find(x => x.id === prodId);
    if (!p) return;

    const idx = TIENDA.carrito.findIndex(i => i.id === prodId);
    if (idx >= 0) {
        TIENDA.carrito[idx].cantidad++;
    } else {
        TIENDA.carrito.push({ ...p, cantidad: 1 });
    }
    tienda_actualizarBadgeCarrito();
    tienda_filtrarProductos(); // re-render para reflejar cambio
    showToast(`+1 ${p.nombre} al carrito`, 'success');
}

function tienda_actualizarBadgeCarrito() {
    const total = TIENDA.carrito.reduce((s, i) => s + i.cantidad, 0);
    const btn   = document.getElementById('carrito-count-btn');
    if (btn) btn.textContent = total || '';
    // Badge en el nav
    const navBadge = document.getElementById('tienda-pedidos-badge');
    if (navBadge) {
        navBadge.textContent = total;
        navBadge.classList.toggle('d-none', total === 0);
    }
}

function tienda_abrirCarrito() {
    tienda_renderCarrito();
    new bootstrap.Modal(document.getElementById('carritoModal')).show();
}

function tienda_renderCarrito() {
    const list  = document.getElementById('carrito-items-list');
    const total = document.getElementById('carrito-total');
    if (!list) return;

    if (!TIENDA.carrito.length) {
        list.innerHTML = '<p class="text-center text-muted py-3"><i class="bi bi-cart-x fs-2 d-block mb-2"></i>Carrito vacío</p>';
        if (total) total.textContent = '$0.00';
        return;
    }

    list.innerHTML = TIENDA.carrito.map((item, idx) => `
    <div class="carrito-item">
        <div class="flex-grow-1">
            <div class="fw-semibold">${item.nombre}</div>
            <div class="text-muted small">${tienda_fmt(item.precio)} × ${item.cantidad} = <strong>${tienda_fmt(item.precio * item.cantidad)}</strong></div>
        </div>
        <div class="d-flex align-items-center gap-2">
            <button class="carrito-qty-btn" onclick="tienda_cambiarCantidad(${idx}, -1)">−</button>
            <span class="fw-bold">${item.cantidad}</span>
            <button class="carrito-qty-btn" onclick="tienda_cambiarCantidad(${idx}, +1)">+</button>
            <button class="btn btn-sm text-danger p-1" onclick="tienda_quitarItem(${idx})"><i class="bi bi-trash"></i></button>
        </div>
    </div>`).join('');

    const sum = TIENDA.carrito.reduce((s, i) => s + i.precio * i.cantidad, 0);
    if (total) total.textContent = tienda_fmt(sum);
}

function tienda_cambiarCantidad(idx, delta) {
    TIENDA.carrito[idx].cantidad += delta;
    if (TIENDA.carrito[idx].cantidad <= 0) TIENDA.carrito.splice(idx, 1);
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

function tienda_quitarItem(idx) {
    TIENDA.carrito.splice(idx, 1);
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

function tienda_limpiarCarrito() {
    if (!confirm('¿Vaciar el carrito?')) return;
    TIENDA.carrito = [];
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

// ══════════════════════════════════════════════════════════════
//  PEDIDOS — CLIENTE ENVÍA
// ══════════════════════════════════════════════════════════════

async function tienda_enviarPedido() {
    if (!TIENDA.clienteActual)    return showToast('Debes iniciar sesión', 'warning');
    if (!TIENDA.tiendaSeleccionada) return showToast('Selecciona una tienda primero', 'warning');
    if (!TIENDA.carrito.length)   return showToast('El carrito está vacío', 'warning');

    const pedido = {
        id:         tienda_uid(),
        cliente_id: TIENDA.clienteActual.id,
        cliente_nombre: TIENDA.clienteActual.nombre,
        tienda_id:  TIENDA.tiendaSeleccionada.id,
        tienda_nombre: TIENDA.tiendaSeleccionada.nombre,
        items:      [...TIENDA.carrito],
        total:      TIENDA.carrito.reduce((s, i) => s + i.precio * i.cantidad, 0),
        estado:     'pendiente',
        fecha:      tienda_now(),
        sincronizado: false
    };

    // Guardar localmente siempre
    await tiendaDB.put('pedidos', pedido);

    // Intentar enviar al servidor
    let enviado = false;
    try {
        const resp = await fetch('/api/pedidos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pedido)
        });
        const data = await resp.json();
        if (data.ok) {
            pedido.sincronizado = true;
            await tiendaDB.put('pedidos', pedido);
            enviado = true;
        }
    } catch(e) {
        // Agregar a cola offline
        tienda_agregarCola({ tipo: 'pedido', datos: pedido });
        showToast('Sin conexión. El pedido se enviará al vendedor cuando haya WiFi.', 'warning');
    }

    // Vaciar carrito
    TIENDA.carrito = [];
    tienda_actualizarBadgeCarrito();
    bootstrap.Modal.getInstance(document.getElementById('carritoModal'))?.hide();

    if (enviado) {
        showToast('¡Pedido enviado! El vendedor lo revisará.', 'success');
    }
    tienda_renderCarrito();
}

// ══════════════════════════════════════════════════════════════
//  MIS PEDIDOS (cliente)
// ══════════════════════════════════════════════════════════════

async function tienda_verMisPedidos() {
    document.getElementById('seccion-elegir-tienda')?.classList.add('d-none');
    document.getElementById('seccion-productos-tienda')?.classList.add('d-none');
    document.getElementById('seccion-mis-pedidos')?.classList.remove('d-none');

    const lista = document.getElementById('mis-pedidos-lista');
    lista.innerHTML = '<div class="text-center text-muted py-3"><div class="spinner-border spinner-border-sm me-2"></div>Cargando...</div>';

    let pedidos = [];
    try {
        const resp = await fetch(`/api/pedidos?cliente_id=${TIENDA.clienteActual?.id}`);
        if (resp.ok) {
            const data = await resp.json();
            pedidos = data.pedidos || [];
        }
    } catch(e) {
        pedidos = (await tiendaDB.getAll('pedidos'))
            .filter(p => p.cliente_id === TIENDA.clienteActual?.id)
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
    }

    if (!pedidos.length) {
        lista.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No tienes pedidos aún</div>';
        return;
    }

    lista.innerHTML = pedidos.map(p => `
    <div class="pedido-row">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
                <div class="fw-bold mb-1"><i class="bi bi-shop me-1"></i>${p.tienda_nombre || 'Tienda'}</div>
                <div class="text-muted small">${new Date(p.fecha).toLocaleString()}</div>
                <div class="mt-1">${(p.items || []).map(i => `${i.nombre} ×${i.cantidad}`).join(' · ')}</div>
            </div>
            <div class="text-end">
                <div class="fw-bold text-success fs-5">${tienda_fmt(p.total)}</div>
                <span class="tienda-badge-estado tienda-badge-${p.estado || 'pendiente'}">${tienda_estadoLabel(p.estado)}</span>
                ${!p.sincronizado ? '<div class="text-muted small mt-1"><i class="bi bi-cloud-slash me-1"></i>Pendiente WiFi</div>' : ''}
            </div>
        </div>
    </div>`).join('');
}

function tienda_estadoLabel(estado) {
    return { pendiente:'⏳ Pendiente', aceptado:'✅ Aceptado', rechazado:'❌ Rechazado', entregado:'📦 Entregado' }[estado] || estado;
}

// ══════════════════════════════════════════════════════════════
//  PANEL VENDEDOR — Cargar y gestionar pedidos
// ══════════════════════════════════════════════════════════════

async function tienda_cargarPedidosVendedor() {
    const lista = document.getElementById('lista-pedidos-pendientes');
    const count = document.getElementById('count-pendientes');
    if (!lista) return;

    let pedidos = [];
    try {
        const resp = await fetch('/api/pedidos?estado=pendiente');
        if (resp.ok) {
            const data = await resp.json();
            pedidos = data.pedidos || [];
        }
    } catch(e) {
        pedidos = (await tiendaDB.getAll('pedidos')).filter(p => p.estado === 'pendiente');
    }

    if (count) count.textContent = pedidos.length;
    // Badge en el nav tab
    const navBadge = document.getElementById('tienda-pedidos-badge');
    if (navBadge) {
        navBadge.textContent = pedidos.length;
        navBadge.classList.toggle('d-none', pedidos.length === 0);
        navBadge.style.background = pedidos.length > 0 ? '#ef4444' : '#f59e0b';
    }

    if (!pedidos.length) {
        lista.innerHTML = '<div class="text-center text-muted py-4"><i class="bi bi-inbox fs-2 d-block mb-2"></i>Sin pedidos pendientes</div>';
        return;
    }

    lista.innerHTML = pedidos.map(p => `
    <div class="pedido-row d-flex justify-content-between align-items-start flex-wrap gap-2">
        <div>
            <div class="fw-bold"><i class="bi bi-person me-1 text-primary"></i>${p.cliente_nombre || 'Cliente'}</div>
            <div class="text-muted small">${new Date(p.fecha).toLocaleString()}</div>
            <div class="mt-1 small">${(p.items || []).map(i => `<span class="badge bg-light text-dark border me-1">${i.nombre} ×${i.cantidad}</span>`).join('')}</div>
        </div>
        <div class="text-end d-flex flex-column align-items-end gap-2">
            <span class="fw-bold text-success fs-5">${tienda_fmt(p.total)}</span>
            <div class="d-flex gap-1">
                <button class="btn btn-sm btn-outline-info fw-bold" onclick="tienda_abrirDetallePedido('${p.id}')">
                    <i class="bi bi-eye me-1"></i>Ver
                </button>
                <button class="btn btn-sm btn-success fw-bold" onclick="tienda_cambiarEstadoPedido('${p.id}','aceptado')">
                    <i class="bi bi-check"></i>
                </button>
                <button class="btn btn-sm btn-danger fw-bold" onclick="tienda_cambiarEstadoPedido('${p.id}','rechazado')">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        </div>
    </div>`).join('');
}

async function tienda_abrirDetallePedido(pedidoId) {
    let pedido = null;
    try {
        const resp = await fetch(`/api/pedidos/${pedidoId}`);
        if (resp.ok) pedido = (await resp.json()).pedido;
    } catch(e) {}
    if (!pedido) pedido = await tiendaDB.get('pedidos', pedidoId);
    if (!pedido) return showToast('Pedido no encontrado', 'warning');

    TIENDA.pedidoEnDetalle = pedido;
    const body = document.getElementById('pedidoDetalleBody');
    body.innerHTML = `
    <div class="mb-3 p-3 rounded" style="background:rgba(99,102,241,.05);border:1px solid rgba(99,102,241,.15);">
        <div class="row g-2 text-center">
            <div class="col-6"><div class="text-muted small">Cliente</div><strong>${pedido.cliente_nombre}</strong></div>
            <div class="col-6"><div class="text-muted small">Tienda</div><strong>${pedido.tienda_nombre || '—'}</strong></div>
            <div class="col-6"><div class="text-muted small">Fecha</div><strong>${new Date(pedido.fecha).toLocaleString()}</strong></div>
            <div class="col-6"><div class="text-muted small">Estado</div><span class="tienda-badge-estado tienda-badge-${pedido.estado}">${tienda_estadoLabel(pedido.estado)}</span></div>
        </div>
    </div>
    <h6 class="fw-bold mb-2">Productos:</h6>
    ${(pedido.items || []).map(i => `
    <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
        <span>${i.nombre} <span class="badge bg-secondary ms-1">×${i.cantidad}</span></span>
        <strong class="text-success">${tienda_fmt(i.precio * i.cantidad)}</strong>
    </div>`).join('')}
    <div class="d-flex justify-content-between fw-bold fs-5 mt-3">
        <span>Total:</span>
        <span class="text-success">${tienda_fmt(pedido.total)}</span>
    </div>`;

    const btnA = document.getElementById('btn-aceptar-pedido');
    const btnR = document.getElementById('btn-rechazar-pedido');
    if (btnA) btnA.classList.toggle('d-none', pedido.estado !== 'pendiente');
    if (btnR) btnR.classList.toggle('d-none', pedido.estado !== 'pendiente');

    new bootstrap.Modal(document.getElementById('pedidoDetalleModal')).show();
}

function tienda_aceptarPedido() {
    if (TIENDA.pedidoEnDetalle) {
        tienda_cambiarEstadoPedido(TIENDA.pedidoEnDetalle.id, 'aceptado');
        bootstrap.Modal.getInstance(document.getElementById('pedidoDetalleModal'))?.hide();
    }
}
function tienda_rechazarPedido() {
    if (TIENDA.pedidoEnDetalle) {
        tienda_cambiarEstadoPedido(TIENDA.pedidoEnDetalle.id, 'rechazado');
        bootstrap.Modal.getInstance(document.getElementById('pedidoDetalleModal'))?.hide();
    }
}

async function tienda_cambiarEstadoPedido(pedidoId, nuevoEstado) {
    // Actualizar local
    const pedido = await tiendaDB.get('pedidos', pedidoId);
    if (pedido) {
        pedido.estado = nuevoEstado;
        await tiendaDB.put('pedidos', pedido);
    }

    // Intentar sincronizar
    try {
        await fetch(`/api/pedidos/${pedidoId}/estado`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: nuevoEstado })
        });
    } catch(e) {
        tienda_agregarCola({ tipo: 'estado_pedido', datos: { pedidoId, estado: nuevoEstado } });
    }

    showToast(`Pedido ${nuevoEstado === 'aceptado' ? 'aceptado ✅' : 'rechazado ❌'}`, nuevoEstado === 'aceptado' ? 'success' : 'danger');
    tienda_cargarPedidosVendedor();
}

// ══════════════════════════════════════════════════════════════
//  PANEL ADMIN SECUNDARIO (Tiendas / Clientes / Todos pedidos)
// ══════════════════════════════════════════════════════════════

async function tienda_tabAdmin(seccion) {
    const panel = document.getElementById('panel-admin-secundario');
    const contenido = document.getElementById('panel-admin-contenido');
    panel.classList.remove('d-none');

    if (seccion === 'tiendas') {
        let tiendas = [];
        try {
            const r = await fetch('/api/tiendas');
            if (r.ok) tiendas = (await r.json()).tiendas || [];
        } catch(e) { tiendas = await tiendaDB.getAll('tiendas'); }

        contenido.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold mb-0"><i class="bi bi-shop me-2 text-warning"></i>Mis Tiendas</h5>
            <button class="btn btn-sm fw-bold" onclick="tienda_abrirFormTienda()" style="background:#f59e0b;color:white;border-radius:.6rem;">
                <i class="bi bi-plus me-1"></i>Nueva Tienda
            </button>
        </div>
        <div id="admin-lista-tiendas">
        ${tiendas.length ? tiendas.map(t => `
        <div class="pedido-row d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div class="d-flex align-items-center gap-3">
                <span style="font-size:2rem;">${t.emoji || '🏪'}</span>
                <div>
                    <div class="fw-bold">${t.nombre}</div>
                    <div class="text-muted small">${t.descripcion || ''}</div>
                </div>
            </div>
            <div class="d-flex gap-2 align-items-center">
                <span class="badge ${t.activo ? 'bg-success' : 'bg-secondary'}">${t.activo ? 'Activa' : 'Inactiva'}</span>
                <button class="btn btn-sm btn-outline-danger" onclick="tienda_eliminarTienda('${t.id}')"><i class="bi bi-trash"></i></button>
            </div>
        </div>`).join('') : '<p class="text-muted text-center py-3">No hay tiendas registradas</p>'}
        </div>
        <div id="form-nueva-tienda" class="d-none mt-3 p-3 rounded" style="border:1.5px dashed #f59e0b;background:rgba(245,158,11,.05);">
            <h6 class="fw-bold mb-3">Nueva Tienda</h6>
            <div class="row g-2">
                <div class="col-md-4"><label class="form-label small">Nombre *</label><input type="text" id="nt-nombre" class="form-control" placeholder="Mi Tienda"></div>
                <div class="col-md-4"><label class="form-label small">Descripción</label><input type="text" id="nt-desc" class="form-control" placeholder="Abierto lun-sáb"></div>
                <div class="col-md-2"><label class="form-label small">Emoji</label><input type="text" id="nt-emoji" class="form-control" placeholder="🏪" maxlength="2"></div>
                <div class="col-md-2 d-flex align-items-end"><button class="btn fw-bold w-100" onclick="tienda_crearTienda()" style="background:#f59e0b;color:white;border-radius:.6rem;">Crear</button></div>
            </div>
        </div>`;

    } else if (seccion === 'clientes') {
        let clientes = [];
        try {
            const r = await fetch('/api/clientes');
            if (r.ok) clientes = (await r.json()).clientes || [];
        } catch(e) { clientes = await tiendaDB.getAll('clientes'); }

        contenido.innerHTML = `
        <h5 class="fw-bold mb-3"><i class="bi bi-people me-2 text-warning"></i>Clientes Registrados <span class="badge bg-secondary">${clientes.length}</span></h5>
        <div class="table-responsive">
        <table class="table table-hover align-middle">
            <thead><tr><th>Nombre</th><th>Usuario</th><th>Email</th><th>Teléfono</th><th>Registrado</th><th>Estado</th></tr></thead>
            <tbody>${clientes.length ? clientes.map(c => `
            <tr>
                <td class="fw-semibold">${c.nombre}</td>
                <td><span class="badge bg-light text-dark border">@${c.username}</span></td>
                <td class="text-muted small">${c.email || '—'}</td>
                <td class="text-muted small">${c.telefono || '—'}</td>
                <td class="text-muted small">${new Date(c.creado).toLocaleDateString()}</td>
                <td><span class="badge ${c.activo !== false ? 'bg-success' : 'bg-secondary'}">${c.activo !== false ? 'Activo' : 'Inactivo'}</span></td>
            </tr>`).join('') : '<tr><td colspan="6" class="text-center text-muted py-3">No hay clientes</td></tr>'}
            </tbody>
        </table>
        </div>`;

    } else if (seccion === 'pedidos') {
        let pedidos = [];
        try {
            const r = await fetch('/api/pedidos');
            if (r.ok) pedidos = (await r.json()).pedidos || [];
        } catch(e) { pedidos = (await tiendaDB.getAll('pedidos')).sort((a, b) => new Date(b.fecha) - new Date(a.fecha)); }

        contenido.innerHTML = `
        <h5 class="fw-bold mb-3"><i class="bi bi-bag me-2 text-warning"></i>Todos los Pedidos <span class="badge bg-secondary">${pedidos.length}</span></h5>
        ${pedidos.map(p => `
        <div class="pedido-row d-flex justify-content-between flex-wrap gap-2">
            <div>
                <div class="fw-bold">${p.cliente_nombre} → ${p.tienda_nombre || '—'}</div>
                <div class="text-muted small">${new Date(p.fecha).toLocaleString()}</div>
                <div class="mt-1 small">${(p.items || []).map(i => `${i.nombre} ×${i.cantidad}`).join(' · ')}</div>
            </div>
            <div class="text-end d-flex flex-column align-items-end gap-1">
                <strong class="text-success">${tienda_fmt(p.total)}</strong>
                <span class="tienda-badge-estado tienda-badge-${p.estado}">${tienda_estadoLabel(p.estado)}</span>
                <button class="btn btn-xs btn-outline-secondary" style="font-size:.7rem;padding:.2rem .5rem;" onclick="tienda_abrirDetallePedido('${p.id}')"><i class="bi bi-eye me-1"></i>Ver</button>
            </div>
        </div>`).join('') || '<p class="text-muted text-center py-3">No hay pedidos</p>'}`;
    }
}

function tienda_abrirFormTienda() {
    document.getElementById('form-nueva-tienda')?.classList.toggle('d-none');
}

async function tienda_crearTienda() {
    const nombre = document.getElementById('nt-nombre')?.value.trim();
    const desc   = document.getElementById('nt-desc')?.value.trim();
    const emoji  = document.getElementById('nt-emoji')?.value.trim() || '🏪';
    if (!nombre) return showToast('El nombre es obligatorio', 'warning');

    const tienda = { id: tienda_uid(), nombre, descripcion: desc, emoji, activo: true, creado: tienda_now() };
    await tiendaDB.put('tiendas', tienda);

    try {
        await fetch('/api/tiendas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tienda)
        });
    } catch(e) {
        tienda_agregarCola({ tipo: 'crear_tienda', datos: tienda });
    }

    showToast(`Tienda "${nombre}" creada`, 'success');
    tienda_tabAdmin('tiendas');
}

async function tienda_eliminarTienda(tiendaId) {
    if (!confirm('¿Eliminar esta tienda?')) return;
    await tiendaDB.delete('tiendas', tiendaId);
    try { await fetch(`/api/tiendas/${tiendaId}`, { method: 'DELETE' }); } catch(e) {}
    showToast('Tienda eliminada', 'info');
    tienda_tabAdmin('tiendas');
}

// ══════════════════════════════════════════════════════════════
//  COLA OFFLINE — sincronización automática
// ══════════════════════════════════════════════════════════════

async function tienda_agregarCola(accion) {
    const item = { id: tienda_uid(), ...accion, timestamp: tienda_now() };
    await tiendaDB.put('cola', item);
    TIENDA.colaPendiente.push(item);
    tienda_mostrarBadgeOffline();
}

function tienda_mostrarBadgeOffline() {
    let badge = document.getElementById('tienda-offline-queue');
    const n   = TIENDA.colaPendiente.length;

    if (!badge && n > 0) {
        badge = document.createElement('div');
        badge.id = 'tienda-offline-queue';
        badge.className = 'offline-queue-badge';
        document.body.appendChild(badge);
    }
    if (badge) {
        badge.textContent = `⏳ ${n} acción${n !== 1 ? 'es' : ''} pendiente${n !== 1 ? 's' : ''} de sincronizar`;
        badge.style.display = n > 0 ? 'block' : 'none';
    }
}

async function tienda_sincronizarCola() {
    const cola = await tiendaDB.getAll('cola');
    if (!cola.length) return;

    let sincronizados = 0;
    for (const accion of cola) {
        try {
            let ok = false;
            if (accion.tipo === 'pedido') {
                const r = await fetch('/api/pedidos', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(accion.datos) });
                ok = r.ok;
            } else if (accion.tipo === 'registrar_cliente') {
                const r = await fetch('/api/clientes/registrar', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(accion.datos) });
                ok = r.ok;
            } else if (accion.tipo === 'estado_pedido') {
                const r = await fetch(`/api/pedidos/${accion.datos.pedidoId}/estado`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ estado: accion.datos.estado }) });
                ok = r.ok;
            } else if (accion.tipo === 'crear_tienda') {
                const r = await fetch('/api/tiendas', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(accion.datos) });
                ok = r.ok;
            }
            if (ok) {
                await tiendaDB.delete('cola', accion.id);
                sincronizados++;
            }
        } catch(e) { /* mantener en cola */ }
    }

    TIENDA.colaPendiente = await tiendaDB.getAll('cola');
    tienda_mostrarBadgeOffline();
    if (sincronizados > 0) showToast(`✅ ${sincronizados} acción${sincronizados > 1 ? 'es' : ''} sincronizada${sincronizados > 1 ? 's' : ''}`, 'success');
}

// ══════════════════════════════════════════════════════════════
//  POLLING — notificaciones en tiempo real (polling cada 8s)
// ══════════════════════════════════════════════════════════════

function tienda_iniciarPolling() {
    if (TIENDA.pollingId) return;
    TIENDA.pollingId = setInterval(async () => {
        if (document.visibilityState !== 'visible') return;
        const tabActivo = document.getElementById('tienda-tab-pane')?.classList.contains('show');
        // Siempre actualizar el badge aunque no esté en la pestaña
        try {
            const r = await fetch('/api/pedidos?estado=pendiente');
            if (r.ok) {
                const data = await r.json();
                const n = (data.pedidos || []).length;
                const badge = document.getElementById('tienda-pedidos-badge');
                if (badge) {
                    badge.textContent = n;
                    badge.classList.toggle('d-none', n === 0);
                    badge.style.background = n > 0 ? '#ef4444' : '#f59e0b';
                }
                if (tabActivo && n > 0) tienda_cargarPedidosVendedor();
            }
        } catch(e) { /* offline, silencioso */ }
    }, 8000);
}

// ══════════════════════════════════════════════════════════════
//  ARRANQUE AUTOMÁTICO
// ══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    // Restaurar cliente de sesión previa
    const clienteGuardado = tienda_cargarClienteLocal();
    if (clienteGuardado) TIENDA.clienteActual = clienteGuardado;

    // Sincronizar cuando vuelva la conexión
    window.addEventListener('online', () => {
        tienda_sincronizarCola();
        showToast('Conexión restaurada — sincronizando pedidos...', 'info');
    });
});
