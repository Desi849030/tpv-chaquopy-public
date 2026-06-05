/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║  tpv_debugger.js — TPV ULTRA SMART  v6.0                   ║
 * ║  Sistema de Debug Inteligente + Monitor Supabase            ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * FUNCIONES:
 *  • Panel de errores con categorización y soluciones automáticas
 *  • Diagnóstico de salud del sistema en tiempo real
 *  • Monitor de sincronización con Supabase (tablas, estado)
 *  • Historial diario de snapshots de la aplicación
 *  • Solo visible para el rol "desarrollador"
 */

// ══════════════════════════════════════════════════════════════
//  ESTADO INTERNO DEL DEBUGGER
// ══════════════════════════════════════════════════════════════
window._DBG = {
    activo:     false,
    buffer:     [],          // Todos los mensajes
    errores:    0,
    advertencias: 0,
    supLogs:    [],          // Logs Supabase
    tablasOK:   {},          // Estado de tablas Supabase
    ultimoSync: null,
    intervalId: null,
    expanded:   false,
};

// ══════════════════════════════════════════════════════════════
//  CATEGORÍAS DE ERRORES Y SOLUCIONES AUTOMÁTICAS
// ══════════════════════════════════════════════════════════════
const _DBG_CATEGORIAS = [
    {
        patron: /Cannot set properties of null/i,
        cat: 'DOM_NULL',
        icono: '🔲',
        color: '#f87171',
        titulo: 'Elemento DOM nulo',
        fix: 'Agregar guard: if (el) antes de asignar .innerHTML o .value'
    },
    {
        patron: /Cannot read prop.*of null|Cannot read prop.*of undefined/i,
        cat: 'NULL_REF',
        icono: '⛔',
        color: '#fb923c',
        titulo: 'Referencia nula',
        fix: 'Usar optional chaining: objeto?.propiedad'
    },
    {
        patron: /updateUITranslations is not defined/i,
        cat: 'FN_ELIMINADA',
        icono: '🗑️',
        color: '#a78bfa',
        titulo: 'Función eliminada aún referenciada',
        fix: 'Reemplazar updateUITranslations() por conf_setLanguage()'
    },
    {
        patron: /is not a function/i,
        cat: 'FN_MISSING',
        icono: '🔧',
        color: '#f59e0b',
        titulo: 'Función no definida o no cargada',
        fix: 'Verificar que el archivo JS esté incluido y sin errores de sintaxis'
    },
    {
        patron: /Uncaught SyntaxError|SyntaxError:/i,
        cat: 'SYNTAX',
        icono: '📝',
        color: '#ef4444',
        titulo: 'Error de sintaxis JS',
        fix: 'Revisar el archivo JS señalado en la consola del navegador'
    },
    {
        patron: /Failed to fetch|NetworkError|net::/i,
        cat: 'RED',
        icono: '🌐',
        color: '#38bdf8',
        titulo: 'Error de red / API',
        fix: 'Verificar conexión y que el servidor Flask esté corriendo'
    },
    {
        patron: /401|403|No autenticado|Sin permisos/i,
        cat: 'AUTH',
        icono: '🔑',
        color: '#fb7185',
        titulo: 'Error de autenticación/autorización',
        fix: 'Verificar sesión activa y rol del usuario'
    },
    {
        patron: /Supabase|supabase/i,
        cat: 'SUPABASE',
        icono: '☁️',
        color: '#34d399',
        titulo: 'Error Supabase',
        fix: 'Verificar URL y anon_key en supabase_sync.py. Ejecutar /api/supabase/setup'
    },
    {
        patron: /IndexedDB|IDB|dbHelper/i,
        cat: 'IDB',
        icono: '💾',
        color: '#818cf8',
        titulo: 'Error IndexedDB',
        fix: 'Limpiar datos del sitio en el navegador si la BD está corrupta'
    },
    {
        patron: /XLSX|Excel/i,
        cat: 'EXCEL',
        icono: '📊',
        color: '#4ade80',
        titulo: 'Error Excel/XLSX',
        fix: 'Verificar que la librería XLSX esté cargada y el archivo sea válido'
    },
];

// ══════════════════════════════════════════════════════════════
//  INICIALIZACIÓN — solo para desarrollador
// ══════════════════════════════════════════════════════════════
function _dbgInit() {
    // Capturar errores JS globales
    const _origOnerror = window.onerror;
    window.onerror = function(msg, src, line, col, err) {
        _dbgLog(`❌ [JS] ${msg} — ${(src||'').split('/').pop()}:${line}`, 'error', msg);
        if (_origOnerror) _origOnerror(msg, src, line, col, err);
        return false;
    };

    // Capturar promesas rechazadas
    window.addEventListener('unhandledrejection', e => {
        const msg = e.reason?.message || String(e.reason || 'Promise rechazada');
        _dbgLog(`❌ [PROMISE] ${msg}`, 'error', msg);
    });

    // Capturar console.error
    const _origError = console.error;
    console.error = function(...args) {
        _dbgLog(`⚠️ [console.error] ${args.join(' ')}`, 'warning');
        _origError.apply(console, args);
    };

    // Capturar console.warn
    const _origWarn = console.warn;
    console.warn = function(...args) {
        _dbgLog(`🔔 [console.warn] ${args.join(' ')}`, 'info');
        _origWarn.apply(console, args);
    };

    // Monitorear fetch para errores de red/API
    const _origFetch = window.fetch;
    window.fetch = function(url, opts) {
        return _origFetch(url, opts).then(res => {
            if (!res.ok && res.status >= 400) {
                _dbgLog(`⚠️ [API] ${res.status} ${res.statusText} → ${url}`, 'warning');
            }
            return res;
        }).catch(err => {
            _dbgLog(`❌ [FETCH] ${err.message} → ${url}`, 'error', err.message);
            throw err;
        });
    };

    window._DBG.activo = true;
    _dbgLog('🚀 Debugger TPV activado — modo desarrollador', 'success');
}

// ══════════════════════════════════════════════════════════════
//  LOGGING CENTRAL
// ══════════════════════════════════════════════════════════════
function _dbgLog(mensaje, tipo = 'info', rawMsg = '') {
    const ts   = new Date().toLocaleTimeString('es', { hour12: false });
    const cat  = _dbgCategorizar(rawMsg || mensaje);
    const entry = { ts, mensaje, tipo, cat };

    window._DBG.buffer.push(entry);
    if (window._DBG.buffer.length > 500) window._DBG.buffer.shift();

    if (tipo === 'error')   window._DBG.errores++;
    if (tipo === 'warning') window._DBG.advertencias++;

    // Solo renderizar si el panel está visible
    if (document.getElementById('dbg-v2')) {
        _dbgRenderEntry(entry);
        _dbgActualizarContadores();
    }
}

function _dbgCategorizar(msg) {
    for (const c of _DBG_CATEGORIAS) {
        if (c.patron.test(msg)) return c;
    }
    return null;
}

// ══════════════════════════════════════════════════════════════
//  CONSTRUCCIÓN DEL PANEL UI
// ══════════════════════════════════════════════════════════════
function _dbgConstruirPanel() {
    // Si ya existe, no crear otro (prevenir duplicados en re-login)
    if (document.getElementById('dbg-v2')) {
        window._DBG.expanded = true;
        const p = document.getElementById('dbg-v2');
        if (p) p.style.height = '55vh';
        document.getElementById('dbg-content')?.style && (document.getElementById('dbg-content').style.display = '');
        document.getElementById('dbg-tabs')?.style && (document.getElementById('dbg-tabs').style.display = 'flex');
        return;
    }

    const panel = document.createElement('div');
    panel.id = 'dbg-v2';
    panel.style.cssText = `
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 999999;
        background: #0f172a; color: #94a3b8;
        font-family: 'Courier New', monospace; font-size: 11px;
        border-top: 2px solid #1e40af;
        box-shadow: 0 -4px 24px rgba(0,0,0,.7);
        transition: height .25s ease;
        display: flex; flex-direction: column;
        height: ${window._DBG.expanded ? '55vh' : '38px'};
        max-height: 60vh;
    `;

    panel.innerHTML = `
    <!-- BARRA SUPERIOR: compacta para móvil -->
    <div id="dbg-bar" style="display:flex;align-items:center;gap:4px;padding:3px 6px;
         background:#0f172a;border-bottom:1px solid #1e293b;cursor:pointer;flex-shrink:0;
         min-width:0;overflow:hidden"
         onclick="_dbgToggleExpand()">

        <span style="color:#4ade80;font-weight:700;font-size:10px;white-space:nowrap;flex-shrink:0">🩺 DEBUG</span>

        <!-- Contadores -->
        <span id="dbg-cnt-err"  style="background:#dc2626;color:#fff;border-radius:999px;
              padding:1px 5px;font-size:9px;display:none;white-space:nowrap;flex-shrink:0">0 err</span>
        <span id="dbg-cnt-warn" style="background:#d97706;color:#fff;border-radius:999px;
              padding:1px 5px;font-size:9px;display:none;white-space:nowrap;flex-shrink:0">0 av</span>
        <span id="dbg-sup-status" style="background:#1e3a5f;color:#38bdf8;border-radius:999px;
              padding:1px 5px;font-size:9px;white-space:nowrap;flex-shrink:0;
              max-width:90px;overflow:hidden;text-overflow:ellipsis">☁️ —</span>

        <!-- Solo 3 botones esenciales en la barra -->
        <div style="margin-left:auto;display:flex;gap:3px;flex-shrink:0">
            <button onclick="event.stopPropagation();_dbgDiagnosticar()"
                title="Diagnóstico completo"
                style="${_dbgBtnStyle('#1d4ed8')}">🔍</button>
            <button onclick="event.stopPropagation();_dbgLimpiar()"
                title="Limpiar log"
                style="${_dbgBtnStyle('#374151')}">🗑️</button>
            <button onclick="event.stopPropagation();_dbgCerrar()"
                title="Cerrar panel"
                style="${_dbgBtnStyle('#7f1d1d')}">✕</button>
        </div>
    </div>

    <!-- TABS + ACCIONES secundarias en segunda fila -->
    <div id="dbg-tabs" style="display:flex;flex-wrap:nowrap;background:#0f172a;
         border-bottom:1px solid #1e293b;flex-shrink:0;overflow-x:auto;
         ${window._DBG.expanded ? '' : 'display:none!important'}">
        <!-- Tabs de navegación -->
        <button onclick="_dbgTab('log')"     id="dbg-tab-log"     style="${_dbgTabStyle(true)}">📋 Log</button>
        <button onclick="_dbgTab('health')"  id="dbg-tab-health"  style="${_dbgTabStyle(false)}">❤️ Salud</button>
        <button onclick="_dbgTab('supabase')"id="dbg-tab-supabase"style="${_dbgTabStyle(false)}">☁️ Supa</button>
        <button onclick="_dbgTab('hist')"    id="dbg-tab-hist"    style="${_dbgTabStyle(false)}">📅 Hist</button>
        <!-- Divisor -->
        <span style="width:1px;background:#1e293b;margin:3px 2px;flex-shrink:0"></span>
        <!-- Acciones secundarias -->
        <button onclick="event.stopPropagation();_dbgSetupSupabase()"
            title="Setup Supabase"
            style="${_dbgBtnStyle('#065f46')};margin:2px 1px">☁️ Setup</button>
        <button onclick="event.stopPropagation();_dbgGuardarHistorialHoy()"
            title="Snapshot del día"
            style="${_dbgBtnStyle('#4c1d95')};margin:2px 1px">📅 Snap</button>
        <button onclick="event.stopPropagation();_dbgVerHistorial()"
            title="Ver historial"
            style="${_dbgBtnStyle('#7c3aed')};margin:2px 1px">📋 Hist</button>
    </div>

    <!-- CONTENIDO -->
    <div id="dbg-content" style="flex:1;overflow-y:auto;padding:4px 8px;
         ${window._DBG.expanded ? '' : 'display:none'}">

        <!-- TAB: LOG -->
        <div id="dbg-pane-log">
            <div id="dbg-log-entries" style="display:flex;flex-direction:column;gap:2px"></div>
        </div>

        <!-- TAB: SALUD (oculto inicialmente) -->
        <div id="dbg-pane-health" style="display:none"></div>

        <!-- TAB: SUPABASE -->
        <div id="dbg-pane-supabase" style="display:none"></div>

        <!-- TAB: HISTORIAL -->
        <div id="dbg-pane-hist" style="display:none"></div>
    </div>
    `;

    document.body.appendChild(panel);

    // Volcar buffer existente
    window._DBG.buffer.forEach(_dbgRenderEntry);
    _dbgActualizarContadores();

    // Iniciar monitoreo de Supabase cada 30s
    if (window._DBG.intervalId) clearInterval(window._DBG.intervalId);
    window._DBG.intervalId = setInterval(_dbgChequeoSupabase, 30000);
    _dbgChequeoSupabase();
}

function _dbgBtnStyle(bg) {
    return `background:${bg};color:#e2e8f0;border:none;padding:2px 6px;
            border-radius:4px;cursor:pointer;font-size:10px;font-family:monospace;
            white-space:nowrap;flex-shrink:0`;
}
function _dbgTabStyle(activa) {
    return `background:${activa ? '#1e3a5f' : 'transparent'};color:${activa ? '#7dd3fc' : '#64748b'};
            border:none;padding:4px 8px;cursor:pointer;font-size:11px;font-family:monospace;
            border-bottom:${activa ? '2px solid #3b82f6' : '2px solid transparent'};
            white-space:nowrap;flex-shrink:0`;
}

// ══════════════════════════════════════════════════════════════
//  RENDER DE ENTRADAS
// ══════════════════════════════════════════════════════════════
function _dbgRenderEntry(entry) {
    const container = document.getElementById('dbg-log-entries');
    if (!container) return;

    const colors = { error: '#fca5a5', warning: '#fde68a', success: '#86efac', info: '#94f3a8' };
    const color  = colors[entry.tipo] || colors.info;

    const div = document.createElement('div');
    div.style.cssText = `color:${color};border-bottom:1px solid #1e293b;padding:2px 0;
                         word-break:break-all;line-height:1.4`;

    let html = `<span style="color:#475569">[${entry.ts}]</span> ${_dbgEscapar(entry.mensaje)}`;

    // Si tiene categoría, mostrar badge con fix
    if (entry.cat) {
        html += ` <span style="background:${entry.cat.color}22;color:${entry.cat.color};
                  border:1px solid ${entry.cat.color}44;border-radius:3px;padding:0 4px;font-size:9px"
                  title="${_dbgEscapar(entry.cat.fix)}">${entry.cat.icono} ${entry.cat.titulo}</span>`;
    }

    div.innerHTML = html;
    container.appendChild(div);

    // Mantener máximo 200 entradas visibles
    while (container.children.length > 200) container.removeChild(container.firstChild);

    // Scroll automático
    const content = document.getElementById('dbg-content');
    if (content) content.scrollTop = content.scrollHeight;
}

function _dbgEscapar(str) {
    return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function _dbgActualizarContadores() {
    const cntErr  = document.getElementById('dbg-cnt-err');
    const cntWarn = document.getElementById('dbg-cnt-warn');
    if (!cntErr || !cntWarn) return;
    const e = window._DBG.errores, w = window._DBG.advertencias;
    cntErr.style.display  = e > 0 ? '' : 'none';
    cntErr.textContent    = `${e} error${e !== 1 ? 'es' : ''}`;
    cntWarn.style.display = w > 0 ? '' : 'none';
    cntWarn.textContent   = `${w} aviso${w !== 1 ? 's' : ''}`;
}

// ══════════════════════════════════════════════════════════════
//  CONTROL DE PANEL
// ══════════════════════════════════════════════════════════════
function _dbgToggleExpand() {
    window._DBG.expanded = !window._DBG.expanded;
    const panel   = document.getElementById('dbg-v2');
    const content = document.getElementById('dbg-content');
    const tabs    = document.getElementById('dbg-tabs');
    if (!panel) return;
    panel.style.height = window._DBG.expanded ? '55vh' : '38px';
    if (content) content.style.display = window._DBG.expanded ? '' : 'none';
    if (tabs)    tabs.style.display    = window._DBG.expanded ? 'flex' : 'none';
    // Padding para no tapar contenido de la app
    const app = document.getElementById('tpv-app');
    if (app) app.style.paddingBottom = window._DBG.expanded ? '58vh' : '42px';
}

function _dbgCerrar() {
    const p = document.getElementById('dbg-v2');
    if (p) p.remove();
    if (window._DBG.intervalId) clearInterval(window._DBG.intervalId);
}

function _dbgLimpiar() {
    window._DBG.buffer = [];
    window._DBG.errores = 0;
    window._DBG.advertencias = 0;
    const c = document.getElementById('dbg-log-entries');
    if (c) c.innerHTML = '';
    _dbgActualizarContadores();
    _dbgLog('🧹 Log limpiado', 'info');
}

function _dbgTab(nombre) {
    ['log','health','supabase','hist'].forEach(t => {
        const pane = document.getElementById(`dbg-pane-${t}`);
        const tab  = document.getElementById(`dbg-tab-${t}`);
        if (pane) pane.style.display = t === nombre ? '' : 'none';
        if (tab)  {
            tab.style.background    = t === nombre ? '#1e3a5f' : 'transparent';
            tab.style.color         = t === nombre ? '#7dd3fc' : '#64748b';
            tab.style.borderBottom  = t === nombre ? '2px solid #3b82f6' : '2px solid transparent';
        }
    });
    if (nombre === 'health')   _dbgRenderSalud();
    if (nombre === 'supabase') _dbgRenderSupabase();
    if (nombre === 'hist')     _dbgCargarHistorial();
}

// ══════════════════════════════════════════════════════════════
//  DIAGNÓSTICO COMPLETO DEL SISTEMA
// ══════════════════════════════════════════════════════════════
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
            // Abrir SIN forzar versión para no crear una BD vacía sin el store
            // que usa la app (tpvStateStore). Solo comprobamos accesibilidad.
            const req = indexedDB.open('tpvDataProfessionalDB');
            req.onupgradeneeded = e => {
                // Si la BD no existía, crear el store que espera la app para
                // evitar 'object store not found' en saveState.
                const db = e.target.result;
                if (!db.objectStoreNames.contains('tpvStateStore')) {
                    db.createObjectStore('tpvStateStore');
                }
            };
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
        'tpv_gastos_dia','tpv_historial_diario'
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
//  HISTORIAL DIARIO
// ══════════════════════════════════════════════════════════════
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
//  PUNTO DE ENTRADA PÚBLICO — llamar tras login exitoso
// ══════════════════════════════════════════════════════════════
window.tpvDebugger = {
    /**
     * activar() — idempotente:
     *  • Primera llamada: inicializa capturadores + construye panel + diagnóstico automático
     *  • Llamadas siguientes: muestra/oculta el panel (toggle)
     *  • El botón "Debug" de la barra siempre hace toggle
     */
    activar() {
        const panelExiste = !!document.getElementById('dbg-v2');

        if (panelExiste) {
            // Si está colapsado: expandir. Si ya expandido: solo asegurarse de que se ve.
            if (!window._DBG.expanded) {
                _dbgToggleExpand(); // abre
            } else {
                // Ya está abierto, simplemente aseguramos visibilidad
                const p = document.getElementById('dbg-v2');
                if (p) p.style.height = '55vh';
            }
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

    /** Añadir mensaje al log desde cualquier parte de la app */
    log:    _dbgLog,
    error:  (msg) => _dbgLog(msg, 'error', msg),
    warn:   (msg) => _dbgLog(msg, 'warning'),
    info:   (msg) => _dbgLog(msg, 'info'),
    ok:     (msg) => _dbgLog(msg, 'success'),

    /** API pública para guardar snapshot desde botón Cerrar Día */
    guardarSnapshot: _dbgGuardarHistorialHoy,
};

// Compatibilidad con el sistema dbg() existente en index.html
window.dbg = function(msg, tipo) {
    const t = msg.startsWith('❌') ? 'error' : msg.startsWith('⚠') ? 'warning'
            : msg.startsWith('✅') ? 'success' : 'info';
    _dbgLog(msg, tipo || t, msg);
};