// tpv_admin_inventario.js — Admin: inventario, vendedores, gastos
function _setup_admin_inventario() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane || document.getElementById('inv-admin-btns')) return;
    const btns = document.createElement('div');
    btns.id = 'inv-admin-btns';
    btns.className = 'd-flex gap-2 mb-3 flex-wrap align-items-center';
    btns.innerHTML = `
        <button class="btn btn-primary btn-sm" id="inv-btn-almacen" onclick="_admin_invVista('almacen')">
            <i class="bi bi-building-fill-gear me-1"></i>Almacen General
        </button>
        <button class="btn btn-outline-success btn-sm" id="inv-btn-vendedores" onclick="_admin_invVista('vendedores')">
            <i class="bi bi-people-fill me-1"></i>Vendedores Hoy
        </button>
        <button class="btn btn-outline-warning btn-sm" id="inv-btn-gastos" onclick="_admin_invVista('gastos')">
            <i class="bi bi-cash-stack me-1"></i>Gastos / Inversion
        </button>`;
    pane.insertBefore(btns, pane.firstChild);
}

function _setup_supervisor_inventario() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane) return;
    const tabBtn = document.getElementById('inv-inventario-tab');
    if (tabBtn) { const s = tabBtn.querySelector('span'); if(s) s.textContent = 'Inventario Vendedores'; }
    if (!document.getElementById('inv-sup-btns')) {
        const btns = document.createElement('div');
        btns.id = 'inv-sup-btns';
        btns.className = 'd-flex gap-2 mb-3 flex-wrap align-items-center';
        btns.innerHTML = `
            <button class="btn btn-success btn-sm" id="inv-btn-vendedores" onclick="_admin_invVista('vendedores')">
                <i class="bi bi-people-fill me-1"></i>Vendedores Hoy
            </button>`;
        pane.insertBefore(btns, pane.firstChild);
    }
    [...pane.querySelectorAll(':scope > *:not(#inv-sup-btns):not(#inv-admin-vendedores-wrap):not(#inv-admin-gastos-wrap)')]
        .forEach(function(el) { el.style.display = 'none'; });
    _admin_cargarVendedores();
}

function _admin_invVista(v) {
    var ids = ['almacen', 'vendedores', 'gastos'];
    var wraps = {
        almacen: document.getElementById('inv-inventario-tab-pane'),
        vendedores: document.getElementById('inv-admin-vendedores-wrap'),
        gastos: document.getElementById('inv-admin-gastos-wrap')
    };
    ids.forEach(function(id) {
        var b = document.getElementById('inv-btn-' + id);
        if (!b) return;
        var estilo = (id === v) ? 'btn btn-' : 'btn btn-outline-';
        var color = id === 'almacen' ? 'primary' : id === 'vendedores' ? 'success' : 'warning';
        b.className = estilo + color + ' btn-sm';
    });
    if (wraps.vendedores) wraps.vendedores.style.display = (v === 'vendedores') ? '' : 'none';
    if (wraps.gastos) wraps.gastos.style.display = (v === 'gastos') ? '' : 'none';
    var origEls = document.querySelectorAll('#inv-inventario-tab-pane > *:not(#inv-admin-btns):not(#inv-admin-vendedores-wrap):not(#inv-admin-gastos-wrap):not(#inv-sup-btns)');
    origEls.forEach(function(el) { el.style.display = (v === 'almacen') ? '' : 'none'; });
    if (v === 'vendedores' && typeof _admin_cargarVendedores === 'function') _admin_cargarVendedores();
    if (v === 'gastos' && typeof _admin_cargarGastos === 'function') _admin_cargarGastos();
    if (v === 'almacen' && typeof _admin_recargarAlmacen === 'function') _admin_recargarAlmacen();
}
