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

