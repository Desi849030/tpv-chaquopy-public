async function _dbgDiagnosticar() {
    if (!window._DBG.expanded) _dbgToggleExpand();
    _dbgTab('health');
    _dbgLog('🔍 Iniciando diagnóstico completo...', 'info');

    const pane = document.getElementById('dbg-pane-health');
    if (!pane) return;
    pane.innerHTML = '<p style="color:#94a3b8;padding:8px">⏳ Ejecutando diagnóstico...</p>';

    const checks = [];

    // 1. Estado de tpvState
    checks.push(_dbgCheckEstado());

    // 2. Elementos DOM críticos
    checks.push(_dbgCheckDOM());

    // 3. Funciones críticas
    checks.push(_dbgCheckFunciones());

    // 4. API del servidor
    checks.push(_dbgCheckAPI());

    // 5. IndexedDB
    checks.push(_dbgCheckIDB());

    // 6. Supabase
    checks.push(_dbgCheckSupabaseAPI());

    const resultados = await Promise.allSettled(checks);
    _dbgRenderResultadosDiagnostico(resultados.map(r => r.value || r.reason));
}

async function _dbgCheckEstado() {
    const label = 'Estado (tpvState)';
    try {
        if (!window.tpvState) return { label, ok: false, msg: 'tpvState no definido' };
        const s = window.tpvState;
        const campos = ['productos','categorias','ordenActual','ventasDiarias','historialVentas','inventarios','config'];
        const faltantes = campos.filter(c => s[c] === undefined);
        if (faltantes.length > 0) return { label, ok: false, msg: `Campos faltantes: ${faltantes.join(', ')}` };
        return { label, ok: true, msg: `OK · ${s.productos?.length ?? 0} productos · ${s.historialVentas?.length ?? 0} ventas` };
    } catch(e) { return { label, ok: false, msg: e.message }; }
}

async function _dbgCheckDOM() {
    const label = 'Elementos DOM críticos';
    const ids = [
        'tpv-productos-container', 'tpv-category-filter',
        'tpv-order-items-container', 'ventas-hoy-tabla',
        'inv-tablaInventario', 'gestion-tabla-productos'
    ];
    const faltantes = ids.filter(id => !document.getElementById(id));
    if (faltantes.length === 0) return { label, ok: true, msg: `OK · ${ids.length} elementos verificados` };
    return { label, ok: false, msg: `Faltantes (normal si no visible): ${faltantes.join(', ')}`, warn: true };
}

async function _dbgCheckFunciones() {
    const label = 'Funciones críticas';
    const fns = [
        'tpv_renderizarProductos','conf_setLanguage','saveState','loadState',
        'refreshAllUI','inv_renderizarTabla','registros_renderizar',
        'gestion_guardarProducto','ventas_renderizarTablaHoy'
    ];
    const faltantes = fns.filter(fn => typeof window[fn] !== 'function');
    if (faltantes.length === 0) return { label, ok: true, msg: `OK · ${fns.length} funciones presentes` };
    return { label, ok: false, msg: `No definidas: ${faltantes.join(', ')}` };
}

async function _dbgCheckAPI() {
    const label = 'API servidor Flask';
    try {
        const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (res.status === 401) return { label, ok: true, msg: 'Servidor OK (sesión expirada — normal)' };
        if (res.ok) {
            const d = await res.json();
            return { label, ok: true, msg: `OK · usuario: ${d?.nombre || '?'} (${d?.rol || '?'})` };
        }
        return { label, ok: false, msg: `HTTP ${res.status}` };
    } catch(e) { return { label, ok: false, msg: `Sin respuesta: ${e.message}` }; }
}

async function _dbgCheckIDB() {
    const label = 'IndexedDB';
    return new Promise(resolve => {
        try {
            const req = indexedDB.open('tpvDataProfessionalDB', 1);
            req.onsuccess = () => {
                req.result.close();
                resolve({ label, ok: true, msg: 'BD local accesible' });
            };
            req.onerror = () => resolve({ label, ok: false, msg: 'Error abriendo IndexedDB' });
        } catch(e) { resolve({ label, ok: false, msg: e.message }); }
    });
}

async function _dbgCheckSupabaseAPI() {
    const label = 'Supabase';
    try {
        const res = await fetch('/api/supabase/estado', { credentials: 'same-origin' });
        if (!res.ok) return { label, ok: false, msg: `HTTP ${res.status}` };
        const d = await res.json();
        if (!d.configurado) return { label, ok: false, msg: 'No configurado — edita supabase_sync.py', warn: true };
        const tablasFail = Object.entries(d.tablas || {}).filter(([,v]) => !v).map(([k]) => k);
        if (tablasFail.length > 0) {
            return { label, ok: false, msg: `Tablas faltantes: ${tablasFail.join(', ')} — Ejecuta Setup Supabase`, warn: true };
        }
        window._DBG.tablasOK = d.tablas || {};
        return { label, ok: true, msg: `OK · ${Object.keys(d.tablas || {}).length} tablas activas` };
    } catch(e) { return { label, ok: false, msg: e.message }; }
}

function _dbgRenderResultadosDiagnostico(resultados) {
    const pane = document.getElementById('dbg-pane-health');
    if (!pane) return;

    const total = resultados.length;
    const ok    = resultados.filter(r => r?.ok).length;
    const color = ok === total ? '#4ade80' : ok >= total/2 ? '#fbbf24' : '#f87171';

    let html = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding:6px;
                background:#0f2a1f;border-radius:6px;border:1px solid ${color}33">
        <span style="font-size:18px">${ok === total ? '✅' : ok >= total/2 ? '⚠️' : '❌'}</span>
        <div>
            <div style="color:${color};font-weight:700">Diagnóstico: ${ok}/${total} verificaciones OK</div>
            <div style="color:#64748b;font-size:10px">${new Date().toLocaleString()}</div>
        </div>
        <button onclick="_dbgDiagnosticar()" style="${_dbgBtnStyle('#1e40af')};margin-left:auto">
            🔄 Re-ejecutar
        </button>
    </div>
    <div style="display:grid;gap:4px">`;

    for (const r of resultados) {
        if (!r) continue;
        const c = r.ok ? '#4ade80' : r.warn ? '#fbbf24' : '#f87171';
        const ic = r.ok ? '✅' : r.warn ? '⚠️' : '❌';
        html += `
        <div style="display:flex;align-items:flex-start;gap:6px;padding:4px 6px;
                    background:${c}11;border-left:3px solid ${c};border-radius:3px">
            <span>${ic}</span>
            <div>
                <span style="color:#e2e8f0;font-weight:600">${_dbgEscapar(r.label)}</span>
                <span style="color:#94a3b8;margin-left:8px;font-size:10px">${_dbgEscapar(r.msg || '')}</span>
            </div>
        </div>`;
        // Loguear fallos
        if (!r.ok) _dbgLog(`${ic} [Diagnóstico] ${r.label}: ${r.msg}`, r.warn ? 'warning' : 'error');
    }

    html += '</div>';
    pane.innerHTML = html;
}

// ══════════════════════════════════════════════════════════════
//  MONITOR SUPABASE
// ══════════════════════════════════════════════════════════════
async function _dbgChequeoSupabase() {
    const badge = document.getElementById('dbg-sup-status');
    try {
        const res = await fetch('/api/supabase/estado', { credentials: 'same-origin' });
        if (!res.ok) {
            if (badge) { badge.textContent = '☁️ Supabase ✗'; badge.style.background = '#7f1d1d'; }
            return;
        }
        const d = await res.json();
        window._DBG.ultimoSync = new Date();
        window._DBG.tablasOK   = d.tablas || {};
        const tablasFail = Object.entries(d.tablas || {}).filter(([,v]) => !v).length;
        if (!d.configurado) {
            if (badge) { badge.textContent = '☁️ Sin config'; badge.style.background = '#78350f'; }
        } else if (tablasFail > 0) {
            if (badge) { badge.textContent = `☁️ ${tablasFail} tabla(s) ✗`; badge.style.background = '#7c2d12'; }
            _dbgLog(`⚠️ Supabase: ${tablasFail} tabla(s) faltantes`, 'warning');
        } else {
            if (badge) { badge.textContent = '☁️ Supabase ✓'; badge.style.background = '#14532d'; badge.style.color = '#4ade80'; }
        }
    } catch(e) {
        if (badge) { badge.textContent = '☁️ Offline'; badge.style.background = '#374151'; }
    }
}

function _dbgRenderSupabase() {
    const pane = document.getElementById('dbg-pane-supabase');
    if (!pane) return;

    const tablas = window._DBG.tablasOK;
    const ts     = window._DBG.ultimoSync;

    let html = `
    <div style="margin-bottom:10px;padding:8px;background:#0f172a;border-radius:8px;border:1px solid #334155">
        <div style="color:#94a3b8;font-size:10px;margin-bottom:6px;font-weight:600">&#9881;&#65039; CONFIGURACI&#211;N SUPABASE</div>
        <input id="dbg-sb-url" placeholder="https://xxx.supabase.co"
            style="width:100%;padding:5px 8px;background:#1e293b;color:#f1f5f9;
                   border:1px solid #334155;border-radius:6px;font-size:11px;margin-bottom:4px;
                   box-sizing:border-box">
        <input id="dbg-sb-key" placeholder="eyJhbGci..." type="password"
            style="width:100%;padding:5px 8px;background:#1e293b;color:#f1f5f9;
                   border:1px solid #334155;border-radius:6px;font-size:11px;
                   box-sizing:border-box">
        <div style="display:flex;gap:4px;margin-top:6px">
            <button onclick="_dbgGuardarConfigSB()"
                style="flex:1;padding:5px;background:#1e40af;color:white;border:none;
                       border-radius:6px;font-size:11px;cursor:pointer;font-weight:600">
                &#128190; Guardar Config
            </button>
            <button onclick="_dbgCargarConfigSB()"
                style="padding:5px 10px;background:#334155;color:#e2e8f0;border:none;
                       border-radius:6px;font-size:11px;cursor:pointer">
                &#128260;
            </button>
        </div>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="color:#7dd3fc;font-weight:700">☁️ Estado de Tablas Supabase</span>
        <div style="display:flex;gap:4px">
            <button onclick="_dbgSetupSupabase()" style="${_dbgBtnStyle('#065f46')}">⚡ Crear tablas</button>
            <button onclick="_dbgChequeoSupabase().then(()=>_dbgRenderSupabase())" style="${_dbgBtnStyle('#1e3a5f')}">🔄 Refrescar</button>
        </div>
    </div>
    <div style="color:#475569;font-size:10px;margin-bottom:6px">
        Último chequeo: ${ts ? ts.toLocaleTimeString() : '—'}
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:4px">`;

    const tablasEsperadas = [
        'tpv_estado','tpv_usuarios','tpv_clientes',
        'tpv_ventas_dia','tpv_productos','tpv_stock',
        'tpv_gastos_dia','tpv_historial_diario',
        'tpv_tiendas','tpv_pedidos_tienda','tpv_items_pedido'
    ];

    for (const t of tablasEsperadas) {
        const ok = tablas[t];
        const c  = ok ? '#4ade80' : ok === false ? '#f87171' : '#64748b';
        const ic = ok ? '✅' : ok === false ? '❌' : '❓';
        html += `
        <div style="display:flex;align-items:center;gap:4px;padding:4px 6px;
                    background:#1e293b;border-radius:4px;border:1px solid ${c}44">
            <span>${ic}</span>
            <span style="color:${c};font-size:10px">${t}</span>
        </div>`;
    }

    html += `</div>
    <div style="margin-top:10px;padding:6px;background:#1e293b;border-radius:4px">
        <div style="color:#94a3b8;font-size:10px;margin-bottom:4px">SQL para crear tablas manualmente:</div>
        <button onclick="_dbgCopiarSQL()" style="${_dbgBtnStyle('#1e40af')}">📋 Copiar SQL al portapapeles</button>
    </div>`;

    pane.innerHTML = html;
}

async function _dbgSetupSupabase() {
    _dbgLog('⏳ Creando tablas en Supabase...', 'info');
    const badge = document.getElementById('dbg-sup-status');
    if (badge) badge.textContent = '☁️ Configurando...';
    try {
        const res  = await fetch('/api/supabase/setup', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.ok) {
            _dbgLog(`✅ Supabase: ${data.mensaje || 'Tablas creadas/verificadas'}`, 'success');
            if (data.tablas_creadas?.length) {
                _dbgLog(`   Nuevas: ${data.tablas_creadas.join(', ')}`, 'success');
            }
            if (data.tablas_existentes?.length) {
                _dbgLog(`   Ya existentes: ${data.tablas_existentes.join(', ')}`, 'info');
            }
        } else {
            _dbgLog(`❌ Supabase Setup: ${data.mensaje || data.error}`, 'error');
        }
        await _dbgChequeoSupabase();
        if (document.getElementById('dbg-pane-supabase')?.style.display !== 'none') {
            _dbgRenderSupabase();
        }
    } catch(e) {
        _dbgLog(`❌ Setup Supabase: ${e.message}`, 'error');
    }
}

async function _dbgCopiarSQL() {
    try {
        const res  = await fetch('/api/supabase/sql', { credentials: 'same-origin' });
        const data = await res.json();
        await navigator.clipboard.writeText(data.sql || '');
        _dbgLog('📋 SQL copiado al portapapeles', 'success');
        if (window.showToast) showToast('SQL copiado al portapapeles', 'success');
    } catch(e) {
        _dbgLog(`❌ Error copiando SQL: ${e.message}`, 'error');
    }
}

// ══════════════════════════════════════════════════════════════
//  SUPABASE CRUD DE TABLAS
// ══════════════════════════════════════════════════════════════
const _DBG_TABLAS = [
    'tpv_estado','tpv_usuarios','tpv_clientes',
    'tpv_ventas_dia','tpv_productos','tpv_stock',
    'tpv_gastos_dia','tpv_historial_diario'
];

function _dbgPromptTabla(titulo, incluirCustom) {
    return new Promise(resolve => {
        const existente = document.getElementById('_dbg-modal-tabla');
        if (existente) existente.remove();
        const modal = document.createElement('div');
        modal.id = '_dbg-modal-tabla';
        modal.style.cssText = 'position:fixed;inset:0;z-index:9999999;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px';
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;min-width:260px;max-width:320px;max-height:80vh;overflow-y:auto';
        const tituloEl = document.createElement('div');
        tituloEl.style.cssText = 'color:#7dd3fc;font-weight:700;font-size:12px;margin-bottom:10px';
        tituloEl.textContent = titulo;
        wrapper.appendChild(tituloEl);
        _DBG_TABLAS.forEach(t => {
            const btn = document.createElement('button');
            btn.textContent = t;
            btn.style.cssText = 'display:block;width:100%;text-align:left;background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:6px 10px;margin-bottom:4px;cursor:pointer;font-size:12px;font-family:monospace';
            btn.addEventListener('click', () => { modal.remove(); resolve(t); });
            wrapper.appendChild(btn);
        });
        if (incluirCustom) {
            const sep = document.createElement('div');
            sep.style.cssText = 'margin-top:8px;border-top:1px solid #334155;padding-top:8px';
            const lbl = document.createElement('div');
            lbl.style.cssText = 'color:#94a3b8;font-size:10px;margin-bottom:4px';
            lbl.textContent = 'O escribe el nombre:';
            const row = document.createElement('div');
            row.style.cssText = 'display:flex;gap:4px';
            const inp = document.createElement('input');
            inp.id = '_dbg-tabla-custom';
            inp.placeholder = 'nombre_tabla';
            inp.style.cssText = 'flex:1;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:4px 8px;font-size:12px';
            const okBtn = document.createElement('button');
            okBtn.textContent = 'OK';
            okBtn.style.cssText = 'background:#1d4ed8;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:11px';
            okBtn.addEventListener('click', () => { const v=inp.value.trim(); if(v){modal.remove();resolve(v);} });
            row.appendChild(inp); row.appendChild(okBtn); sep.appendChild(lbl); sep.appendChild(row); wrapper.appendChild(sep);
        }
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancelar';
        cancelBtn.style.cssText = 'margin-top:6px;width:100%;background:#374151;color:#94a3b8;border:none;border-radius:4px;padding:5px;cursor:pointer;font-size:11px';
        cancelBtn.addEventListener('click', () => { modal.remove(); resolve(null); });
        wrapper.appendChild(cancelBtn);
        modal.appendChild(wrapper);
        modal.addEventListener('click', e => { if(e.target === modal){modal.remove(); resolve(null);} });
        document.body.appendChild(modal);
    });
}

function _dbgConfirmar(mensaje) {
    return new Promise(resolve => {
        const existente = document.getElementById('_dbg-modal-confirm');
        if (existente) existente.remove();
        const modal = document.createElement('div');
        modal.id = '_dbg-modal-confirm';
        modal.style.cssText = 'position:fixed;inset:0;z-index:9999999;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px';
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'background:#0f172a;border:1px solid #dc2626;border-radius:8px;padding:16px;max-width:300px;text-align:center';
        const icon = document.createElement('div'); icon.style.cssText = 'font-size:1.5rem;margin-bottom:8px'; icon.textContent = '\u26A0\uFE0F';
        const msgEl = document.createElement('div'); msgEl.style.cssText = 'color:#fca5a5;font-size:12px;margin-bottom:14px;font-family:monospace'; msgEl.textContent = mensaje;
        const btns = document.createElement('div'); btns.style.cssText = 'display:flex;gap:8px;justify-content:center';
        const okBtn = document.createElement('button'); okBtn.textContent = 'Confirmar'; okBtn.style.cssText = 'background:#dc2626;color:#fff;border:none;border-radius:4px;padding:6px 16px;cursor:pointer;font-size:12px;font-weight:700';
        okBtn.addEventListener('click', () => { modal.remove(); resolve(true); });
        const noBtn = document.createElement('button'); noBtn.textContent = 'Cancelar'; noBtn.style.cssText = 'background:#374151;color:#e2e8f0;border:none;border-radius:4px;padding:6px 16px;cursor:pointer;font-size:12px';
        noBtn.addEventListener('click', () => { modal.remove(); resolve(false); });
        btns.appendChild(okBtn); btns.appendChild(noBtn);
        wrapper.appendChild(icon); wrapper.appendChild(msgEl); wrapper.appendChild(btns);
        modal.appendChild(wrapper);
        modal.addEventListener('click', e => { if(e.target === modal){modal.remove(); resolve(false);} });
        document.body.appendChild(modal);
    });
}

