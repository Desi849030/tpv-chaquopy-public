async function _dbgCrearTablaManual() {
    _dbgTab('supabase');
    const tabla = await _dbgPromptTabla('➕ Crear tabla en Supabase:', true);
    if (!tabla) return;
    _dbgLog(`⏳ Creando tabla "${tabla}" en Supabase...`, 'info');
    try {
        const res  = await fetch('/api/supabase/tabla/crear', {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ tabla })
        });
        const data = await res.json();
        if (data.ok) {
            _dbgLog(`✅ Tabla "${tabla}" creada/verificada en Supabase`, 'success');
        } else {
            _dbgLog(`❌ Error creando "${tabla}": ${data.mensaje || data.error}`, 'error');
        }
        await _dbgChequeoSupabase();
        _dbgRenderSupabase();
    } catch(e) {
        _dbgLog(`❌ Error: ${e.message}`, 'error');
    }
}

async function _dbgEditarTabla() {
    _dbgTab('supabase');
    const tabla = await _dbgPromptTabla('✏️ Recrear tabla (DROP + CREATE):', false);
    if (!tabla) return;
    const ok = await _dbgConfirmar(`¿Recrear tabla "${tabla}"?\nSe eliminarán TODOS sus datos.`);
    if (!ok) return;
    _dbgLog(`⏳ Recreando tabla "${tabla}"...`, 'info');
    try {
        const res  = await fetch('/api/supabase/tabla/recrear', {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ tabla })
        });
        const data = await res.json();
        if (data.ok) {
            _dbgLog(`✅ Tabla "${tabla}" recreada correctamente`, 'success');
        } else {
            _dbgLog(`❌ Error recreando "${tabla}": ${data.mensaje || data.error}`, 'error');
        }
        await _dbgChequeoSupabase();
        _dbgRenderSupabase();
    } catch(e) {
        _dbgLog(`❌ Error: ${e.message}`, 'error');
    }
}

async function _dbgEliminarTabla() {
    _dbgTab('supabase');
    const tabla = await _dbgPromptTabla('🗑️ Eliminar tabla de Supabase:', true);
    if (!tabla) return;
    const ok = await _dbgConfirmar(`⛔ ELIMINAR "${tabla}" de Supabase\nSe PERDERÁN todos sus datos.\n¿Estás seguro?`);
    if (!ok) return;
    _dbgLog(`⏳ Eliminando tabla "${tabla}" de Supabase...`, 'info');
    try {
        const res  = await fetch('/api/supabase/tabla/eliminar', {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ tabla })
        });
        const data = await res.json();
        if (data.ok) {
            _dbgLog(`✅ Tabla "${tabla}" eliminada de Supabase`, 'success');
        } else {
            _dbgLog(`❌ Error eliminando "${tabla}": ${data.mensaje || data.error}`, 'error');
        }
        await _dbgChequeoSupabase();
        _dbgRenderSupabase();
    } catch(e) {
        _dbgLog(`❌ Error: ${e.message}`, 'error');
    }
}


async function _dbgGuardarHistorialHoy() {
    _dbgLog('📅 Guardando snapshot del día...', 'info');
    try {
        const state = window.tpvState;
        if (!state) { _dbgLog('❌ tpvState no disponible', 'error'); return; }

        const hoy   = new Date().toISOString().split('T')[0];
        const ventas = state.ventasDiarias?.[hoy] || [];
        const inventario = state.inventarios?.[hoy] || [];

        const snapshot = {
            fecha:            hoy,
            total_ventas:     ventas.reduce((s, v) => s + (v.total || 0), 0),
            num_transacciones: ventas.length,
            productos_activos: state.productos?.length || 0,
            inventario_items:  inventario.length,
            ventas_data:       ventas,
            inventario_data:   inventario,
            config_snapshot:   state.config || {},
            ts_guardado:       new Date().toISOString()
        };

        const res  = await fetch('/api/historial/diario', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(snapshot)
        });
        const data = await res.json();

        if (data.ok) {
            _dbgLog(`✅ Snapshot guardado: ${hoy} — ${ventas.length} ventas, total: $${snapshot.total_ventas.toFixed(2)}`, 'success');
            if (window.showToast) showToast(`Snapshot del día guardado`, 'success');
        } else {
            _dbgLog(`❌ Error guardando snapshot: ${data.mensaje}`, 'error');
        }
    } catch(e) {
        _dbgLog(`❌ Snapshot: ${e.message}`, 'error');
    }
}

async function _dbgVerHistorial() {
    if (!window._DBG.expanded) _dbgToggleExpand();
    _dbgTab('hist');
}

async function _dbgCargarHistorial() {
    const pane = document.getElementById('dbg-pane-hist');
    if (!pane) return;
    pane.innerHTML = '<p style="color:#94a3b8;padding:8px">⏳ Cargando historial...</p>';

    try {
        const res  = await fetch('/api/historial/diario?limite=30', { credentials: 'same-origin' });
        const data = await res.json();

        if (!data.ok || !data.historial?.length) {
            pane.innerHTML = `
            <div style="padding:8px;color:#64748b;text-align:center">
                <p>📭 Sin historial diario guardado aún</p>
                <button onclick="_dbgGuardarHistorialHoy()" style="${_dbgBtnStyle('#4c1d95')}">
                    📅 Guardar snapshot de hoy
                </button>
            </div>`;
            return;
        }

        let html = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="color:#c084fc;font-weight:700">📅 Historial Diario (${data.historial.length} días)</span>
            <button onclick="_dbgGuardarHistorialHoy()" style="${_dbgBtnStyle('#4c1d95')}">
                + Snapshot hoy
            </button>
        </div>
        <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse;font-size:10px">
            <thead>
            <tr style="background:#1e293b;color:#7dd3fc">
                <th style="padding:4px 6px;text-align:left">Fecha</th>
                <th style="padding:4px 6px;text-align:right">Ventas</th>
                <th style="padding:4px 6px;text-align:right">Total $</th>
                <th style="padding:4px 6px;text-align:right">Prods</th>
                <th style="padding:4px 6px;text-align:right">Inv Items</th>
                <th style="padding:4px 6px;text-align:left">Guardado</th>
            </tr>
            </thead>
            <tbody>`;

        let totalAcum = 0;
        for (const h of data.historial) {
            totalAcum += (h.total_ventas || 0);
            const fila_color = (h.num_transacciones || 0) > 0 ? '#f0fdf422' : '#1e293b';
            html += `
            <tr style="background:${fila_color};border-bottom:1px solid #1e293b">
                <td style="padding:3px 6px;color:#e2e8f0;font-weight:600">${h.fecha}</td>
                <td style="padding:3px 6px;text-align:right;color:#94a3b8">${h.num_transacciones || 0}</td>
                <td style="padding:3px 6px;text-align:right;color:#4ade80;font-weight:600">
                    $${Number(h.total_ventas || 0).toFixed(2)}
                </td>
                <td style="padding:3px 6px;text-align:right;color:#94a3b8">${h.productos_activos || 0}</td>
                <td style="padding:3px 6px;text-align:right;color:#94a3b8">${h.inventario_items || 0}</td>
                <td style="padding:3px 6px;color:#475569;font-size:9px">
                    ${h.ts_guardado ? new Date(h.ts_guardado).toLocaleString() : '—'}
                </td>
            </tr>`;
        }

        html += `
            <tr style="background:#1e3a5f;font-weight:700">
                <td style="padding:4px 6px;color:#7dd3fc">TOTAL ${data.historial.length} días</td>
                <td style="padding:4px 6px;text-align:right;color:#7dd3fc">
                    ${data.historial.reduce((s,h)=>s+(h.num_transacciones||0),0)}
                </td>
                <td style="padding:4px 6px;text-align:right;color:#4ade80">
                    $${totalAcum.toFixed(2)}
                </td>
                <td colspan="3"></td>
            </tr>
            </tbody></table></div>`;

        pane.innerHTML = html;
    } catch(e) {
        pane.innerHTML = `<p style="color:#f87171;padding:8px">❌ Error: ${_dbgEscapar(e.message)}</p>`;
    }
}

// ══════════════════════════════════════════════════════════════
//  SALUD — pestaña de health
// ══════════════════════════════════════════════════════════════
function _dbgRenderSalud() {
    const pane = document.getElementById('dbg-pane-health');
    if (!pane) return;
    pane.innerHTML = `
    <div style="padding:8px;text-align:center;color:#94a3b8">
        <p>Haz clic en <strong>🔍 Diagnóstico</strong> para verificar el estado completo del sistema.</p>
        <button onclick="_dbgDiagnosticar()" style="${_dbgBtnStyle('#1d4ed8')};padding:6px 16px;font-size:12px">
            🔍 Ejecutar Diagnóstico Completo
        </button>
    </div>`;
}

// ══════════════════════════════════════════════════════════════
//  CRUD — Operaciones directas sobre datos
// ══════════════════════════════════════════════════════════════
function _dbgRenderCRUD() {
    const pane = document.getElementById('dbg-pane-crud');
    if (!pane) return;
    pane.innerHTML = `
    <div style="padding:8px">
        <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px">
            <button onclick="_dbgCRUDList('productos')" style="${_dbgBtnStyle('#1d4ed8')}">📦 Productos</button>
            <button onclick="_dbgCRUDList('categorias')" style="${_dbgBtnStyle('#7c3aed')}">🏷️ Categorías</button>
            <button onclick="_dbgCRUDList('ventas')" style="${_dbgBtnStyle('#059669')}">🧾 Ventas Hoy</button>
            <button onclick="_dbgCRUDList('inventario')" style="${_dbgBtnStyle('#d97706')}">📋 Inventario</button>
            <button onclick="_dbgCRUDList('usuarios')" style="${_dbgBtnStyle('#dc2626')}">👥 Usuarios</button>
            <button onclick="_dbgCRUDList('gastos')" style="${_dbgBtnStyle('#0891b2')}">💰 Gastos</button>
        </div>
        <div id="dbg-crud-content" style="color:#94a3b8;font-size:11px">
            <p style="text-align:center;padding:16px">Selecciona una entidad para ver/editar sus datos</p>
        </div>
    </div>`;
}

async function _dbgCRUDList(tipo) {
    const content = document.getElementById('dbg-crud-content');
    if (!content) return;
    content.innerHTML = '<p style="text-align:center;color:#94a3b8">⏳ Cargando...</p>';
    try {
        let items = [];
        const state = window.tpvState;
        if (!state) { content.innerHTML = '<p style="color:#f87171">❌ tpvState no disponible</p>'; return; }
        const hoy = new Date().toISOString().split('T')[0];
        switch(tipo) {
            case 'productos': items = (state.productos||[]).map((p,i)=>({idx:i,id:p.id,nombre:p.nombre,precio:p.precio,categoria:p.categoria,stock:p.stock||0})); break;
            case 'categorias': items = (state.categorias||[]).map((c,i)=>({idx:i,id:c.id||c.nombre,nombre:c.nombre,color:c.color||'#0d6efd'})); break;
            case 'ventas': { const _v=state.ventasDiarias?.[hoy]; if(Array.isArray(_v)){ items=_v.map((v,i)=>({idx:i,id:v.id,producto:v.productoNombre,cantidad:v.cantidad,total:v.total,hora:v.hora||'--:--'})); }else if(_v!=null){ _dbgLog('\u26A0\uFE0F ventasDiarias['+hoy+'] no es array (tipo: '+typeof _v+')','warning'); } break; }
            case 'inventario': { const _inv=state.inventarios?.[hoy]; if(Array.isArray(_inv)){ items=_inv.map((inv,i)=>({idx:i,id:inv.productoId,nombre:inv.productoNombre||inv.nombre,stock:inv.stockActual||inv.cantidad||0})); }else if(_inv!=null){ _dbgLog('\u26A0\uFE0F inventarios['+hoy+'] no es array (tipo: '+typeof _inv+')','warning'); } break; }
            case 'usuarios':
                try { const r=await fetch('/api/usuarios',{credentials:'same-origin'}); const d=await r.json(); const _raw=d?.usuarios||(Array.isArray(d)?d:null)||[]; if(!Array.isArray(_raw)){ _dbgLog('\u26A0\uFE0F /api/usuarios formato inesperado: '+typeof _raw,'warning'); items=[]; }else{ items=_raw.map((u,i)=>({idx:i,id:u.id||u.usuario_id,nombre:u.nombre,username:u.username,rol:u.rol,activo:u.activo!==false})); } } catch(e){ _dbgLog('\u26A0\uFE0F Error cargando usuarios: '+e.message,'error'); items=[]; }
                break;
            case 'gastos': { const _g=state.gastosDiarios?.[hoy]; if(Array.isArray(_g)){ items=_g.map((g,i)=>({idx:i,id:g.id,concepto:g.concepto||g.descripcion,monto:g.monto,categoria:g.categoria||'General'})); }else if(_g!=null){ _dbgLog('\u26A0\uFE0F gastosDiarios['+hoy+'] no es array (tipo: '+typeof _g+')','warning'); } break; }
        }
        if (items.length === 0) { content.innerHTML = `<p style="text-align:center;color:#64748b;padding:16px">📭 Sin datos de ${tipo}</p>`; return; }
        let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="color:#7dd3fc;font-weight:700;font-size:11px">${tipo.toUpperCase()} (${items.length})</span><button onclick="_dbgCRUDAdd('${tipo}')" style="background:#059669;color:#fff;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:10px">+ Agregar</button></div>`;
        html += `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:9px">`;
        const cols = Object.keys(items[0]).filter(k => k !== 'idx');
        html += `<thead><tr style="background:#1e293b;color:#7dd3fc">`;
        cols.forEach(c => { html += `<th style="padding:3px 5px;text-align:left;white-space:nowrap">${c}</th>`; });
        html += `<th style="padding:3px 5px;text-align:center">ACCIONES</th></tr></thead><tbody>`;
        items.forEach((item) => {
            html += `<tr style="background:#0f172a;border-bottom:1px solid #1e293b">`;
            cols.forEach(c => { const val=item[c]; const isNum=typeof val==='number'; html += `<td style="padding:2px 5px;color:${isNum?'#4ade80':'#e2e8f0'};${isNum?'text-align:right':''};max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${val!==undefined?val:'—'}</td>`; });
            html += `<td style="padding:2px 3px;text-align:center;white-space:nowrap"><button onclick="_dbgCRUDEdit('${tipo}',${item.idx})" style="background:#2563eb;color:#fff;border:none;border-radius:3px;padding:1px 5px;cursor:pointer;font-size:9px;margin-right:2px">✏️</button><button onclick="_dbgCRUDDelete('${tipo}',${item.idx})" style="background:#dc2626;color:#fff;border:none;border-radius:3px;padding:1px 5px;cursor:pointer;font-size:9px">🗑️</button></td></tr>`;
        });
        html += `</tbody></table></div>`;
        content.innerHTML = html;
    } catch(e) { content.innerHTML = `<p style="color:#f87171">❌ Error: ${e.message}</p>`; }
}

async function _dbgCRUDAdd(tipo) {
    const state = window.tpvState;
    if (!state) { _dbgLog('❌ tpvState no disponible','error'); return; }
    const hoy = new Date().toISOString().split('T')[0];

    // Para usuarios, usar un form embebido en vez de prompt
    if (tipo === 'usuarios') {
        _dbgCRUDAddUsuario();
        return;
    }

    const concepto = prompt(`Nuevo registro de ${tipo} (JSON):\n\nEjemplo productos:\n{"nombre":"Nuevo Producto","precio":100,"stock":10,"categoria":"General"}\n\nEjemplo ventas:\n{"productoNombre":"Producto","cantidad":1,"total":100,"hora":"12:00"}\n\nEjemplo gastos:\n{"concepto":"Gasto","monto":50,"categoria":"General"}`);
    if (!concepto) return;
    try {
        const obj = JSON.parse(concepto);
        switch(tipo) {
            case 'productos':
                if(!obj.nombre){_dbgLog('❌ "nombre" requerido','error');return;}
                obj.id='p_'+Date.now();
                obj.precio=Number(obj.precio)||0;
                obj.stock=Number(obj.stock)||0;
                obj.categoria=obj.categoria||'General';
                state.productos.push(obj);
                break;
            case 'categorias':
                if(!obj.nombre){_dbgLog('❌ "nombre" requerido','error');return;}
                obj.id=obj.nombre;
                obj.color=obj.color||'#0d6efd';
                state.categorias.push(obj);
                break;
            case 'ventas':
                if(!state.ventasDiarias) state.ventasDiarias={};
                if(!state.ventasDiarias[hoy]) state.ventasDiarias[hoy]=[];
                obj.id='v_'+Date.now();
                obj.total=Number(obj.total)||0;
                obj.cantidad=Number(obj.cantidad)||1;
                obj.hora=obj.hora||new Date().toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'});
                state.ventasDiarias[hoy].push(obj);
                if(state.historialVentas) state.historialVentas.push({...obj,fecha:hoy});
                break;
            case 'inventario':
                if(!state.inventarios) state.inventarios={};
                if(!state.inventarios[hoy]) state.inventarios[hoy]=[];
                obj.id='inv_'+Date.now();
                obj.stockActual=Number(obj.stockActual||obj.cantidad||0);
                state.inventarios[hoy].push(obj);
                break;
            case 'gastos':
                if(!state.gastosDiarios) state.gastosDiarios={};
                if(!state.gastosDiarios[hoy]) state.gastosDiarios[hoy]=[];
                obj.id='g_'+Date.now();
                obj.monto=Number(obj.monto)||0;
                obj.concepto=obj.concepto||obj.descripcion||'Gasto';
                obj.categoria=obj.categoria||'General';
                state.gastosDiarios[hoy].push(obj);
                break;
            default:
                _dbgLog(`❌ Tipo ${tipo} no soportado para agregar`,'error');
                return;
        }
        if (typeof saveState === 'function') await saveState();
        _dbgLog(`✅ ${tipo} agregado: ${JSON.stringify(obj).substring(0,80)}`,'success');
        _dbgCRUDList(tipo);
        if (typeof initializeUI === 'function') try { initializeUI(); } catch(e) {}
    } catch(e) { _dbgLog(`❌ Error JSON: ${e.message}`,'error'); }
}

async function _dbgCRUDAddUsuario() {
    const content = document.getElementById('dbg-crud-content');
    if (!content) return;
    content.innerHTML = `
    <div style="background:#1e293b;padding:12px;border-radius:8px;margin-bottom:8px">
        <div style="color:#7dd3fc;font-weight:700;font-size:12px;margin-bottom:8px">👤 Crear Nuevo Usuario</div>
        <div style="display:flex;flex-direction:column;gap:6px">
            <input id="dbg-new-user-nombre" placeholder="Nombre completo" style="padding:6px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px">
            <input id="dbg-new-user-username" placeholder="Nombre de usuario" style="padding:6px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px">
            <input id="dbg-new-user-password" type="password" placeholder="Contraseña" style="padding:6px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px">
            <select id="dbg-new-user-rol" style="padding:6px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px">
                <option value="vendedor">Vendedor</option>
                <option value="supervisor">Supervisor</option>
                <option value="administrador">Administrador</option>
            </select>
            <div style="display:flex;gap:6px;margin-top:4px">
                <button onclick="_dbgCrearUsuario()" style="flex:1;background:#059669;color:#fff;border:none;border-radius:6px;padding:8px;cursor:pointer;font-size:12px;font-weight:600">✅ Crear Usuario</button>
                <button onclick="_dbgCRUDList('usuarios')" style="flex:1;background:#475569;color:#fff;border:none;border-radius:6px;padding:8px;cursor:pointer;font-size:12px">← Volver</button>
            </div>
        </div>
    </div>`;
}

async function _dbgCrearUsuario() {
    const nombre = document.getElementById('dbg-new-user-nombre')?.value?.trim();
    const username = document.getElementById('dbg-new-user-username')?.value?.trim();
    const password = document.getElementById('dbg-new-user-password')?.value;
    const rol = document.getElementById('dbg-new-user-rol')?.value;
    if (!nombre || !username || !password) { _dbgLog('❌ Todos los campos son requeridos','error'); return; }
    try {
        const res = await fetch('/api/usuarios/crear', {
            method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({nombre, username, password, rol})
        });
        if (res.ok) {
            _dbgLog(`✅ Usuario "${username}" creado con rol ${rol}`,'success');
            _dbgCRUDList('usuarios');
        } else {
            const err = await res.json().catch(()=>({}));
            _dbgLog(`❌ Error al crear usuario: ${err.error || err.mensaje || res.status}`,'error');
        }
    } catch(e) { _dbgLog(`❌ Error: ${e.message}`,'error'); }
}

async function _dbgCRUDEdit(tipo, idx) {
    const state = window.tpvState;
    if (!state) return;
    const hoy = new Date().toISOString().split('T')[0];
    let items;
    switch(tipo) {
        case 'productos': items=state.productos; break;
        case 'categorias': items=state.categorias; break;
        case 'ventas': items=state.ventasDiarias?.[hoy]; break;
        case 'inventario': items=state.inventarios?.[hoy]; break;
        case 'gastos': items=state.gastosDiarios?.[hoy]; break;
        default: _dbgLog(`❌ Tipo ${tipo} no editable`,'error'); return;
    }
    if (!Array.isArray(items)) { _dbgLog('❌ Datos de '+tipo+' no son un array (tipo: '+(typeof items)+')','error'); return; }
    if (!items[idx]) { _dbgLog('❌ Ítem no encontrado','error'); return; }
    const current = JSON.stringify(items[idx], null, 2);
    const edited = prompt(`Editar ${tipo}[${idx}] (JSON):`, current);
    if (!edited) return;
    try {
        items[idx] = JSON.parse(edited);
        if (typeof saveState === 'function') await saveState();
        _dbgLog(`✅ ${tipo}[${idx}] editado`,'success');
        _dbgCRUDList(tipo);
        if (typeof initializeUI === 'function') try { initializeUI(); } catch(e) {}
    } catch(e) { _dbgLog(`❌ Error JSON: ${e.message}`,'error'); }
}

async function _dbgCRUDDelete(tipo, idx) {
    if (!confirm(`¿Eliminar ${tipo}[${idx}]?`)) return;
    const state = window.tpvState;
    if (!state) return;
    const hoy = new Date().toISOString().split('T')[0];
    switch(tipo) {
        case 'productos': state.productos.splice(idx,1); break;
        case 'categorias': state.categorias.splice(idx,1); break;
        case 'ventas': if(Array.isArray(state.ventasDiarias?.[hoy])) state.ventasDiarias[hoy].splice(idx,1); else _dbgLog('⚠️ ventasDiarias no es array','warning'); break;
        case 'inventario': if(Array.isArray(state.inventarios?.[hoy])) state.inventarios[hoy].splice(idx,1); else _dbgLog('⚠️ inventarios no es array','warning'); break;
        case 'gastos': if(Array.isArray(state.gastosDiarios?.[hoy])) state.gastosDiarios[hoy].splice(idx,1); else _dbgLog('⚠️ gastosDiarios no es array','warning'); break;
        default: _dbgLog(`❌ Tipo ${tipo} no eliminable`,'error'); return;
    }
    if (typeof saveState === 'function') await saveState();
    _dbgLog(`🗑️ ${tipo}[${idx}] eliminado`,'warning');
    _dbgCRUDList(tipo);
    if (typeof initializeUI === 'function') try { initializeUI(); } catch(e) {}
}


// ══════════════════════════════════════════════════════════════
//  PUNTO DE ENTRADA PÚBLICO — llamar tras login exitoso
// ══════════════════════════════════════════════════════════════
window.tpvDebugger = {
    activar() {
        const panelExiste = !!document.getElementById('dbg-v2');

        if (panelExiste) {
            // Toggle: mostrar u ocultar
            _dbgToggleExpand();
            return;
        }

        // Primera vez: inicializar todo
        if (!window._DBG.activo) _dbgInit();
        _dbgConstruirPanel();

        // Expandir automáticamente al abrir por primera vez
        if (!window._DBG.expanded) {
            window._DBG.expanded = true;
            const panel   = document.getElementById('dbg-v2');
            const content = document.getElementById('dbg-content');
            const tabs    = document.getElementById('dbg-tabs');
            if (panel)   panel.style.height   = '55vh';
            if (content) content.style.display = '';
            if (tabs)    tabs.style.display    = 'flex';
        }

        // Diagnóstico automático 1.5s después
        setTimeout(_dbgDiagnosticar, 1500);

        // Aviso si hay ventas del día sin snapshot
        setTimeout(() => {
            const hoy    = new Date().toISOString().split('T')[0];
            const ventas = window.tpvState?.ventasDiarias?.[hoy] || [];
            if (ventas.length > 0) {
                _dbgLog(`ℹ️ ${ventas.length} ventas hoy sin snapshot — usa "📅 Snapshot" para guardar`, 'info');
            }
        }, 2000);
    },

    log:    _dbgLog,
    error:  (msg) => _dbgLog(msg, 'error', msg),
    warn:   (msg) => _dbgLog(msg, 'warning'),
    info:   (msg) => _dbgLog(msg, 'info'),
    ok:     (msg) => _dbgLog(msg, 'success'),

    guardarSnapshot: _dbgGuardarHistorialHoy,
};


// ══════════════════════════════════════════════════════════════
//  CONFIG SUPABASE — guardar/cargar URL y key desde la app
// ══════════════════════════════════════════════════════════════
async function _dbgGuardarConfigSB() {
    var url = document.getElementById('dbg-sb-url');
    var key = document.getElementById('dbg-sb-key');
    if (!url || !key) { _dbgLog('Error: elementos no encontrados', 'error'); return; }
    var urlVal = url.value ? url.value.trim() : '';
    var keyVal = key.value ? key.value.trim() : '';
    if (!urlVal || !keyVal) { _dbgLog('URL y Key son requeridos', 'error'); return; }
    if (!urlVal.startsWith('https://')) { _dbgLog('URL debe empezar con https://', 'error'); return; }
    if (keyVal.length < 20) { _dbgLog('Key demasiado corta (min 20 chars)', 'error'); return; }
    _dbgLog('Guardando configuracion Supabase...', 'info');
    try {
        var res = await fetch('/api/supabase/config', {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: urlVal, anon_key: keyVal})
        });
        var d = await res.json();
        if (d.ok) {
            _dbgLog('Config guardada. Ejecuta Setup para crear tablas.', 'success');
            await _dbgChequeoSupabase();
            _dbgRenderSupabase();
        } else {
            _dbgLog('Error: ' + (d.error || d.mensaje || JSON.stringify(d)), 'error');
        }
    } catch(e) {
        _dbgLog('Error de red: ' + e.message, 'error');
    }
}

async function _dbgCargarConfigSB() {
    _dbgLog('Cargando config actual...', 'info');
    try {
        var res = await fetch('/api/supabase/config', {
            method: 'GET', credentials: 'same-origin'
        });
        var d = await res.json();
        if (d.ok) {
            var urlInput = document.getElementById('dbg-sb-url');
            var keyInput = document.getElementById('dbg-sb-key');
            if (urlInput && d.url) urlInput.value = d.url;
            if (keyInput && d.anon_key_preview) keyInput.placeholder = 'Actual: ' + d.anon_key_preview;
            _dbgLog('Config cargada: ' + (d.url || 'sin config'), 'info');
        } else {
            _dbgLog('No hay config guardada', 'warning');
        }
    } catch(e) {
        _dbgLog('Error: ' + e.message, 'error');
    }
}

// Compatibilidad con el sistema dbg() existente en index.html
window.dbg = function(msg, tipo) {
    const t = msg.startsWith('❌') ? 'error' : msg.startsWith('⚠') ? 'warning'
            : msg.startsWith('✅') ? 'success' : 'info';
    _dbgLog(msg, tipo || t, msg);
};

// === MÉTRICAS DEL SISTEMA (v2.1.1) ===
window._DBG_METRICAS = function() {
    var ex = document.getElementById('dbg-metricas-modal');
    if (ex) ex.remove();
    var m = document.createElement('div');
    m.id = 'dbg-metricas-modal';
    m.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:99999;display:flex;align-items:center;justify-content:center;';
    var p = document.createElement('div');
    p.style.cssText = 'background:#1a1a2e;border-radius:12px;width:95%;max-width:900px;height:80vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.5);';
    var h = document.createElement('div');
    h.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:12px 20px;background:#16213e;border-radius:12px 12px 0 0;border-bottom:1px solid #0f3460;';
    h.innerHTML = '<h3 style="margin:0;color:#e94560;font-size:16px;">\uD83D\uDCCA M\u00e9tricas del Sistema</h3>';
    var cb = document.createElement('button');
    cb.textContent = '\u2715';
    cb.style.cssText = 'background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:4px 8px;';
    cb.onclick = function() { m.remove(); };
    h.appendChild(cb);
    var fr = document.createElement('div');
    fr.id = 'dbg-metrics-content';
    fr.style.cssText = 'flex:1;border:none;width:100%;border-radius:0 0 12px 12px;padding:20px;color:#e0e0e0;overflow-y:auto;text-align:center';
    fr.innerHTML = '<span style="color:#5a6a7a">Cargando métricas...</span>';
    p.appendChild(h); p.appendChild(fr); m.appendChild(p);
    
    // Cargar datos en tiempo real
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/dev/metrics', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            var d = JSON.parse(xhr.responseText);
            if (d.ok && d.ram && d.inventario) {
                fr.innerHTML = 
                    '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                    '<b>🧠 RAM</b><br>Proceso: ' + d.ram.proceso_mb + ' MB | Sistema: ' + d.ram.sistema_pct + '%<br>' +
                    'Total: ' + d.ram.sistema_total_mb + ' MB | Libre: ' + d.ram.sistema_libre_mb + ' MB</div>' +
                    '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                    '<b>💾 Almacenamiento</b><br>BD: ' + (d.storage?.db_size_kb||'--') + ' KB | Disco: ' + (d.storage?.disco_pct||'--') + '%</div>' +
                    '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                    '<b>📦 Inventario</b><br>Productos: ' + d.inventario.total_productos + ' | Unidades: ' + d.inventario.total_unidades + '<br>' +
                    'Valor venta: ' + (d.inventario.valor_venta_total||0).toFixed(2) + ' CUP | Ganancia: ' + (d.inventario.ganancia_potencial||0).toFixed(2) + ' CUP<br>' +
                    'Margen: ' + d.inventario.margen_bruto_pct + '% | Cobertura: ' + (d.inventario.formula_cobertura||'N/A') + '</div>';
            }
        }
    };
    xhr.send();
    
    // Actualizar cada 10 segundos
    var intervalId = setInterval(function() {
        var fr2 = document.getElementById('dbg-metrics-content');
        if (!fr2) { clearInterval(intervalId); return; }
        var xhr2 = new XMLHttpRequest();
        xhr2.open('GET', '/api/dev/metrics', true);
        xhr2.onload = function() {
            if (xhr2.status === 200 && fr2) {
                var d = JSON.parse(xhr2.responseText);
                if (d.ok && d.ram) {
                    fr2.innerHTML = 
                        '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                        '<b>🧠 RAM</b><br>Proceso: ' + d.ram.proceso_mb + ' MB | Sistema: ' + d.ram.sistema_pct + '%<br>' +
                        'Total: ' + d.ram.sistema_total_mb + ' MB | Libre: ' + d.ram.sistema_libre_mb + ' MB</div>' +
                        '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                        '<b>💾 Almacenamiento</b><br>BD: ' + (d.storage?.db_size_kb||'--') + ' KB | Disco: ' + (d.storage?.disco_pct||'--') + '%</div>' +
                        '<div style="background:#0f3460;border-radius:8px;padding:12px;margin-bottom:8px">' +
                        '<b>📦 Inventario</b><br>Productos: ' + d.inventario.total_productos + ' | Unidades: ' + d.inventario.total_unidades + '<br>' +
                        'Valor venta: ' + (d.inventario.valor_venta_total||0).toFixed(2) + ' CUP | Ganancia: ' + (d.inventario.ganancia_potencial||0).toFixed(2) + ' CUP<br>' +
                        'Margen: ' + d.inventario.margen_bruto_pct + '% | Cobertura: ' + (d.inventario.formula_cobertura||'N/A') + '</div>' +
                        '<div style="font-size:10px;color:#5a6a7a">Actualizado: ' + (d.timestamp||'') + '</div>';
                }
            }
        };
        xhr2.send();
    }, 10000);
    m.addEventListener('click', function(e) { if (e.target === m) m.remove(); });
    document.body.appendChild(m);
};

(function() {
    function tryBtn() {
        var db = document.getElementById('btn-debug-toggle');
        if (db && !document.getElementById('btn-metricas-toggle')) {
            var b = document.createElement('button');
            b.id = 'btn-metricas-toggle';
            b.className = 'ub-btn';
            b.style.cssText = 'background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.4);color:#60a5fa;margin-left:6px;';
            b.innerHTML = '<i class="bi bi-bar-chart-fill" style="margin-right:4px;"></i><span class="d-none d-sm-inline">M\u00e9tricas</span>';
            b.onclick = function(e) { e.preventDefault(); e.stopPropagation(); if (window._DBG_METRICAS) window._DBG_METRICAS(); };
            db.parentNode.insertBefore(b, db.nextSibling);
            return true;
        }
        var dp = document.getElementById('dbg-v2');
        if (dp) {
            var dc = dp.querySelector('.dbg-content,.dbg-body');
            if (dc && !document.getElementById('dbg-metricas-btn')) {
                var b2 = document.createElement('button');
                b2.id = 'dbg-metricas-btn';
                b2.className = 'btn btn-sm btn-outline-info mb-2';
                b2.innerHTML = '\uD83D\uDCCA M\u00e9tricas del Sistema';
                b2.style.cssText = 'width:100%;';
                b2.onclick = function() { if (window._DBG_METRICAS) window._DBG_METRICAS(); };
                dc.insertBefore(b2, dc.firstChild);
                return true;
            }
        }
        return false;
    }
    if (!tryBtn()) { var i = 0; var iv = setInterval(function() { if (tryBtn() || ++i > 10) clearInterval(iv); }, 500); }
})();
