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

    TPV_TIENDA.tiendaSeleccionada = tienda;

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
    TPV_TIENDA.tiendaSeleccionada = null;
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

    TPV_TIENDA._productosActuales = productos;

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
    const ps  = (TPV_TIENDA._productosActuales || []).filter(p => {
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
        const enCarrito = TPV_TIENDA.carrito.find(i => i.id === p.id);
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
    const p = (TPV_TIENDA._productosActuales || []).find(x => x.id === id);
    if (!p) return;
    const enCarrito = TPV_TIENDA.carrito.find(i => i.id === id);
    showToast(`${p.nombre} — ${tienda_fmt(p.precio)}. ${enCarrito ? `En carrito: ${enCarrito.cantidad}` : 'Toca el ícono + para agregar.'}`, 'info');
}

// ══════════════════════════════════════════════════════════════
//  CARRITO
// ══════════════════════════════════════════════════════════════

function tienda_toggleCarrito(prodId) {
    if (!TPV_TIENDA.clienteActual) { tienda_abrirAuth(); return; }
    const p = (TPV_TIENDA._productosActuales || []).find(x => x.id === prodId);
    if (!p) return;

    const idx = TPV_TIENDA.carrito.findIndex(i => i.id === prodId);
    if (idx >= 0) {
        TPV_TIENDA.carrito[idx].cantidad++;
    } else {
        TPV_TIENDA.carrito.push({ ...p, cantidad: 1 });
    }
    tienda_actualizarBadgeCarrito();
    tienda_filtrarProductos(); // re-render para reflejar cambio
    showToast(`+1 ${p.nombre} al carrito`, 'success');
}

function tienda_actualizarBadgeCarrito() {
    const total = TPV_TIENDA.carrito.reduce((s, i) => s + i.cantidad, 0);
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

    if (!TPV_TIENDA.carrito.length) {
        list.innerHTML = '<p class="text-center text-muted py-3"><i class="bi bi-cart-x fs-2 d-block mb-2"></i>Carrito vacío</p>';
        if (total) total.textContent = '$0.00';
        return;
    }

    list.innerHTML = TPV_TIENDA.carrito.map((item, idx) => `
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

    const sum = TPV_TIENDA.carrito.reduce((s, i) => s + i.precio * i.cantidad, 0);
    if (total) total.textContent = tienda_fmt(sum);
}

function tienda_cambiarCantidad(idx, delta) {
    TPV_TIENDA.carrito[idx].cantidad += delta;
    if (TPV_TIENDA.carrito[idx].cantidad <= 0) TPV_TIENDA.carrito.splice(idx, 1);
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

function tienda_quitarItem(idx) {
    TPV_TIENDA.carrito.splice(idx, 1);
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

function tienda_limpiarCarrito() {
    if (!confirm('¿Vaciar el carrito?')) return;
    TPV_TIENDA.carrito = [];
    tienda_actualizarBadgeCarrito();
    tienda_renderCarrito();
}

// ══════════════════════════════════════════════════════════════
//  PEDIDOS — CLIENTE ENVÍA
// ══════════════════════════════════════════════════════════════

