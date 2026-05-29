async function tienda_enviarPedido() {
    if (!TPV_TIENDA.clienteActual)    return showToast('Debes iniciar sesión', 'warning');
    if (!TPV_TIENDA.tiendaSeleccionada) return showToast('Selecciona una tienda primero', 'warning');
    if (!TPV_TIENDA.carrito.length)   return showToast('El carrito está vacío', 'warning');

    const pedido = {
        id:         tienda_uid(),
        cliente_id: TPV_TIENDA.clienteActual.id,
        cliente_nombre: TPV_TIENDA.clienteActual.nombre,
        tienda_id:  TPV_TIENDA.tiendaSeleccionada.id,
        tienda_nombre: TPV_TIENDA.tiendaSeleccionada.nombre,
        items:      [...TPV_TIENDA.carrito],
        total:      TPV_TIENDA.carrito.reduce((s, i) => s + i.precio * i.cantidad, 0),
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
    TPV_TIENDA.carrito = [];
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
        const resp = await fetch(`/api/pedidos?cliente_id=${TPV_TIENDA.clienteActual?.id}`);
        if (resp.ok) {
            const data = await resp.json();
            pedidos = data.pedidos || [];
        }
    } catch(e) {
        pedidos = (await tiendaDB.getAll('pedidos'))
            .filter(p => p.cliente_id === TPV_TIENDA.clienteActual?.id)
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

    TPV_TIENDA.pedidoEnDetalle = pedido;
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
    if (TPV_TIENDA.pedidoEnDetalle) {
        tienda_cambiarEstadoPedido(TPV_TIENDA.pedidoEnDetalle.id, 'aceptado');
        bootstrap.Modal.getInstance(document.getElementById('pedidoDetalleModal'))?.hide();
    }
}
function tienda_rechazarPedido() {
    if (TPV_TIENDA.pedidoEnDetalle) {
        tienda_cambiarEstadoPedido(TPV_TIENDA.pedidoEnDetalle.id, 'rechazado');
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
    TPV_TIENDA.colaPendiente.push(item);
    tienda_mostrarBadgeOffline();
}

function tienda_mostrarBadgeOffline() {
    let badge = document.getElementById('tienda-offline-queue');
    const n   = TPV_TIENDA.colaPendiente.length;

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

    TPV_TIENDA.colaPendiente = await tiendaDB.getAll('cola');
    tienda_mostrarBadgeOffline();
    if (sincronizados > 0) showToast(`✅ ${sincronizados} acción${sincronizados > 1 ? 'es' : ''} sincronizada${sincronizados > 1 ? 's' : ''}`, 'success');
}

// ══════════════════════════════════════════════════════════════
//  POLLING — notificaciones en tiempo real (polling cada 8s)
// ══════════════════════════════════════════════════════════════

function tienda_iniciarPolling() {
    if (TPV_TIENDA.pollingId) return;
    TPV_TIENDA.pollingId = setInterval(async () => {
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
    if (clienteGuardado) TPV_TIENDA.clienteActual = clienteGuardado;

    // Sincronizar cuando vuelva la conexión
    window.addEventListener('online', () => {
        tienda_sincronizarCola();
        showToast('Conexión restaurada — sincronizando pedidos...', 'info');
    });
});
