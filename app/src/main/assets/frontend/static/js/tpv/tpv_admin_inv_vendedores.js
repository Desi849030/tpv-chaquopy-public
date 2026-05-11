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
