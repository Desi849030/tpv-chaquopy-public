/**
 * tpv_vendedor.js — TPV ULTRA SMART v5.0
 * Inventario Diario vendedor: conteos, cierre, historial
 * Extraido de script_8.js
 */

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
    if (!confirm(`\u00bfCerrar el d\u00eda ${hoy}?\n\nEsto registrar\u00e1 el resumen de ventas.\nAseg\u00farate de haber anotado todos los conteos finales.`)) return;

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
function admin_inventario
function _setup_admin_inventario() {
    const pane = document.getElementById('inv-inventario-tab-pane');
    if (!pane || document.getElementById('inv-admin-btns')) return;

    const btns = document.createElement('div');
    btns.id = 'inv-admin-btns';
    btns.className = 'd-flex gap-2 mb-3 flex-wrap align-items-center';
