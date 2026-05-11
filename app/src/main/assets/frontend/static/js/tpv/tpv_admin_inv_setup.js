// tpv_admin_inventario.js — Admin: inventario, vendedores, gastos
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
