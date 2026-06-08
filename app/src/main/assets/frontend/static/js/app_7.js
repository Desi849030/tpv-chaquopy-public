// Usar window.* de forma consistente para que el destroy encuentre la
// instancia previa y no falle Chart.js con "Canvas is already in use".
window._dashChartVentas = window._dashChartVentas || null;
window._dashChartCat    = window._dashChartCat    || null;

// Only render charts if the dashboard tab is active
function isDashboardTabActive() {
    const tabPane = document.getElementById('dashboard-tab-pane');
    return tabPane && tabPane.classList.contains('active');
}

async function dashboard_cargar() {
    const hoy   = new Date().toISOString().split('T')[0];

    // Sincronizar ventas del SERVIDOR (BD) hacia tpvState para que el dashboard
    // refleje los datos reales y no solo lo que haya en memoria del navegador.
    try {
        const rv = await fetch('/api/ventas/hoy', { credentials: 'same-origin' });
        if (rv.ok) {
            const dv = await rv.json();
            if (dv && Array.isArray(dv.ventas)) {
                tpvState.ventasDiarias = tpvState.ventasDiarias || {};
                tpvState.ventasDiarias[hoy] = dv.ventas.map(v => ({
                    productoId: v.producto_id || v.productoId || v.id,
                    producto: v.producto || v.nombre,
                    nombre: v.nombre || v.producto,
                    cantidad: Number(v.cantidad) || 1,
                    total: Number(v.total) || 0,
                    fecha: v.fecha || hoy
                }));
            }
        }
    } catch (e) { /* offline: usar lo que haya en tpvState */ }

    const ventas = tpvState.ventasDiarias[hoy] || [];
    const hist   = tpvState.historialVentas   || [];

    // ── KPIs del día ──────────────────────────────────────
    const ingHoy  = ventas.reduce((s,v) => s + (v.total||0), 0);
    const costoHoy= ventas.reduce((s,v) => {
        const p = tpvState.productos.find(p=>p.id===v.productoId);
        const costo = (p && (p.costoUnitario != null ? p.costoUnitario : p.costo)) || 0;
        return s + (Number(costo) * (v.cantidad||1));
    }, 0);
    const gananHoy = ingHoy - costoHoy;
    const txHoy    = ventas.length;

    // Ventas últimos 7 días
    const dias7 = [], lbl7 = [];
    for (let i=6; i>=0; i--) {
        const d = new Date(); d.setDate(d.getDate()-i);
        const k = d.toISOString().split('T')[0];
        const sv = (tpvState.ventasDiarias[k]||[]).reduce((s,v)=>s+(v.total||0),0);
        dias7.push(parseFloat(sv.toFixed(2)));
        lbl7.push(d.toLocaleDateString('es',{weekday:'short'}));
    }

    // Ventas por categoría hoy
    const catMap = {};
    ventas.forEach(v => {
        const p = tpvState.productos.find(p=>p.id===v.productoId);
        const cat = p?.categoria || 'General';
        catMap[cat] = (catMap[cat]||0) + (v.total||0);
    });

    // Top 5 hoy
    const prodMap = {};
    ventas.forEach(v => {
        prodMap[v.productoId] = { nombre: v.nombre, cant: (prodMap[v.productoId]?.cant||0)+(v.cantidad||1), total:(prodMap[v.productoId]?.total||0)+(v.total||0) };
    });
    const top5 = Object.values(prodMap).sort((a,b)=>b.cant-a.cant).slice(0,5);

    // ── Stock crítico + total de productos (refleja la importación Excel) ──
    let stockCritico = [];
    let totalProductos = 0;
    try {
        const r = await fetch('/api/inventario/general',{credentials:'same-origin'});
        const d = await r.json();
        const inv = d.inventario || [];
        totalProductos = inv.length;
        stockCritico = inv.filter(p => parseFloat(p.stock_actual||0) <= parseFloat(p.stock_minimo||5));
    } catch(e){}

    // ── Vendedores hoy ─────────────────────────────────────
    let vendsHoy = [];
    try {
        const r = await fetch('/api/pedidos?estado=pendiente',{credentials:'same-origin'}).catch(()=>null);
    } catch(e){}

    // ── Render KPIs ────────────────────────────────────────
    const kpiDiv = document.getElementById('dash-kpis');
    if (kpiDiv) kpiDiv.innerHTML = `
        <div class="col-6 col-md-3">
            <div class="glass-card text-center py-3">
                <div style="font-size:2rem">💰</div>
                <div class="fw-bold fs-4 text-success">$${ingHoy.toFixed(2)}</div>
                <div class="text-muted small">Ingresos hoy</div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="glass-card text-center py-3">
                <div style="font-size:2rem">📈</div>
                <div class="fw-bold fs-4 text-primary">$${gananHoy.toFixed(2)}</div>
                <div class="text-muted small">Ganancia hoy</div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="glass-card text-center py-3">
                <div style="font-size:2rem">🛒</div>
                <div class="fw-bold fs-4">${txHoy}</div>
                <div class="text-muted small">Transacciones</div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="glass-card text-center py-3">
                <div style="font-size:2rem">⚠️</div>
                <div class="fw-bold fs-4 text-danger">${stockCritico.length}</div>
                <div class="text-muted small">Stock crítico</div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="glass-card text-center py-3">
                <div style="font-size:2rem">📦</div>
                <div class="fw-bold fs-4 text-info">${totalProductos}</div>
                <div class="text-muted small">Productos</div>
            </div>
        </div>`;

    // ── Gráfico barras ventas 7 días ───────────────────────
    // Destroy existing chart instances to prevent leaks
    if (window._dashChartVentas) window._dashChartVentas.destroy();
    if (window._dashChartCat) window._dashChartCat.destroy();

    if (isDashboardTabActive()) {
        const ctxV = document.getElementById('dash-chart-ventas');
        if (ctxV) {
            window._dashChartVentas = new Chart(ctxV, {
                type: 'bar',
                data: {
                    labels: lbl7,
                    datasets: [{ label:'Ventas $', data: dias7,
                        backgroundColor:'rgba(13,110,253,0.7)', borderRadius:6 }]
                },
                options: { responsive:true, plugins:{ legend:{ display:false } },
                    scales:{ y:{ beginAtZero:true } } }
            });
        }

        // ── Gráfico pie categorías ─────────────────────────────
        const ctxC = document.getElementById('dash-chart-cat');
        if (ctxC && Object.keys(catMap).length) {
            const COLORS = ['#0d6efd','#198754','#ffc107','#dc3545','#6f42c1','#20c997','#fd7e14'];
            window._dashChartCat = new Chart(ctxC, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(catMap),
                    datasets: [{ data: Object.values(catMap).map(v=>parseFloat(v.toFixed(2))),
                        backgroundColor: COLORS }]
                },
                options: { responsive:true, plugins:{ legend:{ position:'bottom' } } }
            });
        } else if (ctxC) {
            ctxC.parentElement.innerHTML = '<p class="text-muted text-center py-4">Sin ventas hoy para categorías</p>';
        }
    }

    // ── Top 5 productos ────────────────────────────────────
    const top5El = document.getElementById('dash-top5');
    if (top5El) {
        if (!top5.length) { top5El.innerHTML = '<p class="text-muted small text-center py-3 col-12">Sin ventas hoy</p>'; }
        else top5El.innerHTML = top5.map((p,i)=>`
            <div class="col-12 col-sm-6">
                <div class="d-flex align-items-center gap-2 p-2 rounded-3 bg-light">
                    <span class="fw-bold text-warning fs-5">#${i+1}</span>
                    <div class="flex-grow-1 overflow-hidden">
                        <div class="fw-semibold text-truncate">${p.nombre}</div>
                        <div class="text-muted small">${p.cant} uds · $${(Number(p.total)||0).toFixed(2)}</div>
                    </div>
                </div>
            </div>`).join('');
    }

    // ── Stock crítico ──────────────────────────────────────
    const scEl = document.getElementById('dash-stock-critico');
    if (scEl) {
        if (!stockCritico.length) { scEl.innerHTML = '<p class="text-success text-center py-3"><i class="bi bi-check-circle-fill me-1"></i>Todo el stock OK</p>'; }
        else scEl.innerHTML = `<table class="table table-sm mb-0">
            <thead class="table-dark"><tr><th>Producto</th><th class="text-center">Stock</th><th class="text-center">Mínimo</th></tr></thead>
            <tbody>${stockCritico.map(p=>`<tr>
                <td class="text-truncate" style="max-width:160px">${p.nombre}</td>
                <td class="text-center text-danger fw-bold">${parseFloat(p.stock_actual||0)}</td>
                <td class="text-center text-muted">${parseFloat(p.stock_minimo||5)}</td>
            </tr>`).join('')}</tbody></table>`;
    }
}

// ══════════════════════════════════════════════════════════
//  DESCUENTOS — gestión desde herramientas
// ══════════════════════════════════════════════════════════
async function descuentos_cargarLista() {
    try {
        const r = await fetch('/api/descuentos',{credentials:'same-origin'});
        const d = await r.json();
        const el = document.getElementById('desc-lista');
        if (!el) return;
        const lista = d.descuentos || [];
        if (!lista.length) { el.innerHTML = '<p class="text-muted small text-center py-2">Sin descuentos configurados</p>'; return; }
        el.innerHTML = lista.map(d=>`
            <div class="list-group-item d-flex justify-content-between align-items-center py-1 px-2">
                <span class="fw-semibold">${d.nombre}</span>
                <div class="d-flex gap-2 align-items-center">
                    <span class="badge bg-warning text-dark">${d.tipo==='porcentaje'?d.valor+'%':'$'+d.valor}</span>
                    <button class="btn btn-sm btn-outline-danger py-0 px-1" onclick="descuentos_eliminar(${d.id})"><i class="bi bi-trash-fill"></i></button>
                </div>
            </div>`).join('');
    } catch(e) {}
}

async function descuentos_crear() {
    const nombre = document.getElementById('desc-nombre')?.value?.trim();
    const tipo   = document.getElementById('desc-tipo')?.value;
    const valor  = parseFloat(document.getElementById('desc-valor')?.value);
    if (!nombre || isNaN(valor) || valor <= 0) { showToast('Completa todos los campos del descuento', 'warning'); return; }
    try {
        const r = await fetch('/api/descuentos', { method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({nombre, tipo, valor}) });
        const d = await r.json();
        if (d.ok) {
            document.getElementById('desc-nombre').value = '';
            document.getElementById('desc-valor').value  = '';
            descuentos_cargarLista();
            showToast('✅ Descuento creado','success');
        }
    } catch(e) {}
}

async function descuentos_eliminar(id) {
    try {
        await fetch(`/api/descuentos/${id}`, { method:'DELETE', credentials:'same-origin' });
        descuentos_cargarLista();
        showToast('Descuento eliminado','info');
    } catch(e) {}
}

// ══════════════════════════════════════════════════════════
//  SUPABASE SYNC COMPLETO
// ══════════════════════════════════════════════════════════
// Cargar la configuración actual de Supabase en los campos del formulario
async function supabase_cargarConfig() {
    try {
        const r = await fetch('/api/supabase/config', { credentials: 'same-origin' });
        if (!r.ok) return;
        const d = await r.json();
        const u = document.getElementById('sb-cfg-url');
        const k = document.getElementById('sb-cfg-key');
        if (u && d.url) u.value = d.url;
        if (k && d.anon_key) k.value = d.anon_key;
    } catch (e) { /* sin conexión */ }
}

// Mostrar las tablas que deben existir en el proyecto Supabase
async function supabase_verTablas() {
    const el = document.getElementById('sb-tablas');
    if (!el) return;
    el.innerHTML = '<div class="spinner-border spinner-border-sm me-1"></div>Consultando...';
    try {
        const r = await fetch('/api/supabase/estado', { credentials: 'same-origin' });
        const d = await r.json();
        const tablas = d.tablas || [];
        if (!tablas.length) { el.innerHTML = '<span class="text-muted">Sin tablas definidas.</span>'; return; }
        el.innerHTML = '<div class="border rounded p-2 mt-1">' +
            '<strong>Crea estas ' + tablas.length + ' tablas en tu Supabase:</strong><br>' +
            tablas.map(function(t){ return '<code>' + t + '</code>'; }).join(' · ') +
            '<br><span class="text-muted">Estado: ' + (d.configurado ? '✅ configurado' : '⚠️ sin configurar') + '</span></div>';
    } catch (e) {
        el.innerHTML = '<span class="text-danger">No se pudo consultar.</span>';
    }
}

// Guardar URL + API key de Supabase
async function supabase_guardarConfig() {
    const u = document.getElementById('sb-cfg-url');
    const k = document.getElementById('sb-cfg-key');
    const st = document.getElementById('sb-cfg-status');
    const url = (u && u.value || '').trim();
    const key = (k && k.value || '').trim();
    if (!url || !key) {
        if (st) st.innerHTML = '<span class="text-warning">Completa URL y API Key.</span>';
        return;
    }
    if (st) st.innerHTML = '<div class="spinner-border spinner-border-sm me-1"></div>Guardando...';
    try {
        const r = await fetch('/api/supabase/config', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, anon_key: key })
        });
        const d = await r.json();
        if (r.ok && d.ok) {
            if (st) st.innerHTML = d.configurado
                ? '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Supabase configurado correctamente.</span>'
                : '<span class="text-warning">Guardado, pero verifica la URL/clave.</span>';
        } else {
            if (st) st.innerHTML = '<span class="text-danger">Error: ' + (d.error || '') + '</span>';
        }
    } catch (e) {
        if (st) st.innerHTML = '<span class="text-danger">Sin conexión con el servidor.</span>';
    }
}
// Cargar config al abrir la pestaña de configuración
document.addEventListener('shown.bs.tab', function (e) {
    if (e.target && e.target.getAttribute('data-bs-target') === '#conf-config-tab-pane') {
        supabase_cargarConfig();
    }
});

async function supabase_syncFull() {
    const el = document.getElementById('sb-sync-status');
    if (el) el.innerHTML = '<div class="spinner-border spinner-border-sm me-1"></div>Sincronizando...';
    try {
        const r = await fetch('/api/supabase/sync-full', { method:'POST', credentials:'same-origin' });
        const d = await r.json();
        if (d.ok) {
            if (el) el.innerHTML = `✅ Ventas:${d.ventas} Productos:${d.productos} Stock:${d.stock} Gastos:${d.gastos}`;
            showToast('☁️ Sync completo a Supabase','success');
        } else {
            if (el) el.innerHTML = '❌ ' + (d.mensaje||d.error||'Error');
            showToast(d.mensaje||'Error de sincronización','danger');
        }
    } catch(e) {
        if (el) el.innerHTML = '❌ Sin conexión';
        showToast('Sin conexión a Supabase','warning');
    }
}

async function supabase_syncUsuarios() {
    const el = document.getElementById('sb-sync-status');
    if (el) el.innerHTML = '<div class="spinner-border spinner-border-sm me-1"></div>Sincronizando usuarios...';
    try {
        const r = await fetch('/api/supabase/sync', { method:'POST', credentials:'same-origin' });
        const d = await r.json();
        if (el) el.innerHTML = d.ok ? '✅ Usuarios sincronizados' : '❌ ' + (d.mensaje||'Error');
        showToast(d.ok ? '☁️ Usuarios sync OK' : 'Error sync usuarios', d.ok?'success':'danger');
    } catch(e) { if (el) el.innerHTML = '❌ Sin conexión'; }
}