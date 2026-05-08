// tpv_admin.js
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
                      $${(general.reduce((s,p)=>s+(parseFloat(p.precio_compra)||0)*(parseFloat(p.stock_actual)||0),0)).toFixed(2)}
                    </td>
                    <td class="text-center">
                      $${(general.reduce((s,p)=>s+(parseFloat(p.precio_venta)||0)*(parseFloat(p.stock_actual)||0),0)).toFixed(2)}
                    </td>
                    <td colspan="3"></td>
                  </tr>
                  <tr class="table-primary">
                    <td colspan="8" class="text-end small">
                      <span class="me-3">💰 <strong>Inversión total en almacén:</strong>
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
        html += `<div class="glass-card" style="border:2px solid #0d6efd44;background:linear-gradient(135deg,#0d6efd0d,#19875411)">
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
    if (!vendedor_id) { _toast('Selecciona un vendedor','warning'); return; }
    if (cantidad<=0)  { _toast('Ingresa una cantidad mayor a 0','warning'); cantEl.focus(); return; }
    if (cantidad>stock){ alert(`Stock insuficiente. Disponible: ${stock}`); return; }
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
            else alert('Error: ' + errMsg);
        }
    } catch(e) {
        if (typeof showToast==='function') showToast(`❌ Error de red: ${e.message}`, 'danger');
        else alert('Error de red: '+e.message);
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
    if (!confirm(`⚠️ ¿Eliminar todo el inventario diario de ${nombre}?\n\nEl almacén general NO se modifica.`)) return;
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
        } else { alert('Error: '+data.mensaje); }
    } catch(e) { alert('Error: '+e.message); }
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
function _admin_limpiarInventariosUI() {
    const hoy = new Date().toISOString().split('T')[0];
    const opc = prompt(`🗑️ LIMPIAR INVENTARIOS DIARIOS\n\n1 — Solo inventarios de HOY (${hoy})\n2 — TODOS los inventarios\n\nEl almacén general NO se modifica.\nEscribe 1 o 2:`);
    if (!opc) return;
    let payload = {};
    if (opc.trim()==='1') payload={fecha:hoy};
    else if (opc.trim()==='2') payload={};
    else { _toast('Opción inválida','warning'); return; }
    const desc = opc.trim()==='1' ? `inventarios de HOY (${hoy})` : 'TODOS los inventarios';
    if (!confirm(`⛔ ¿Confirmar eliminación de ${desc}?\n\nLos vendedores quedarán sin stock asignado.`)) return;
    fetch('/api/inventario/diario/limpiar',{
        method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
    }).then(r=>r.json()).then(data=>{
        if (data.ok) {
            if (typeof showToast==='function') showToast(`✅ ${data.mensaje}`,'success');
            const fechaEl=document.getElementById('inv-admin-fecha-vend');
            _admin_renderVendedores(fechaEl?.value||hoy);
        } else { alert('Error: '+data.mensaje); }
    }).catch(e=>alert('Error: '+e.message));
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
    if (!confirm('¿Eliminar este gasto?')) return;
    try {
        const res = await fetch(`/api/gastos/${gasto_id}`, { method:'DELETE', credentials:'same-origin' });
        if (res.ok) { _toast('Gasto eliminado', 'success'); await _admin_cargarGastos(); }
    } catch(e) {}
}


// ══════════════════════════════════════════════════════════════
//  CONFIGURACIÓN DE TIENDA (Admin / Desarrollador)
// ══════════════════════════════════════════════════════════════
let _cfg_tienda_id = null;

