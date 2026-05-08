// tpv_debugger.js — Panel de debug inteligente + monitor Supabase + diagnóstico

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
    <!-- BARRA SUPERIOR -->
    <div id="dbg-bar" style="display:flex;align-items:center;gap:5px;padding:4px 8px;
         background:#0f172a;border-bottom:1px solid #1e293b;cursor:pointer;flex-shrink:0;flex-wrap:wrap"
         onclick="_dbgToggleExpand()">

        <span style="color:#4ade80;font-weight:700;font-size:12px">🩺 TPV DEBUG</span>

        <!-- Contadores -->
        <span id="dbg-cnt-err"  style="background:#dc2626;color:#fff;border-radius:999px;
              padding:1px 6px;font-size:10px;display:none">0 errores</span>
        <span id="dbg-cnt-warn" style="background:#d97706;color:#fff;border-radius:999px;
              padding:1px 6px;font-size:10px;display:none">0 avisos</span>
        <span id="dbg-sup-status" style="background:#1e3a5f;color:#38bdf8;border-radius:999px;
              padding:1px 6px;font-size:10px">☁️ Supabase —</span>

        <!-- Menús agrupados -->
        <div style="margin-left:auto;display:flex;gap:4px;position:relative" onclick="event.stopPropagation()">

            <!-- ▸ Diagnóstico (acción directa) -->
            <button onclick="_dbgDiagnosticar()" title="Diagnóstico completo"
                style="${_dbgBtnStyle('#1d4ed8')}">🔍 Diag</button>

            <!-- ▸ Supabase ▾ -->
            <div style="position:relative">
                <button onclick="_dbgToggleMenu('dbg-menu-supa')"
                    style="${_dbgBtnStyle('#065f46')}">☁️ Supa ▾</button>
                <div id="dbg-menu-supa" style="display:none;position:absolute;bottom:28px;right:0;
                    background:#0f172a;border:1px solid #1e3a5f;border-radius:6px;
                    min-width:200px;z-index:1000000;box-shadow:0 -4px 16px rgba(0,0,0,.6)">
                    <div style="padding:4px 8px;color:#38bdf8;font-size:10px;font-weight:700;border-bottom:1px solid #1e293b">☁️ SUPABASE</div>
                    <button onclick="_dbgMenuAcc(()=>_dbgSetupSupabase())" style="${_dbgMenuItemStyle()}">⚡ Setup (crear tablas)</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgTab('supabase'))" style="${_dbgMenuItemStyle()}">📊 Ver estado tablas</button>
                    <div style="border-top:1px solid #1e293b;margin:2px 0"></div>
                    <button onclick="_dbgMenuAcc(()=>_dbgCrearTablaManual())" style="${_dbgMenuItemStyle()}">➕ Crear tabla manual</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgEditarTabla())" style="${_dbgMenuItemStyle()}">✏️ Recrear / editar tabla</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgEliminarTabla())" style="${_dbgMenuItemStyle('#7f1d1d')}">🗑️ Eliminar tabla</button>
                    <div style="border-top:1px solid #1e293b;margin:2px 0"></div>
                    <button onclick="_dbgMenuAcc(()=>_dbgCopiarSQL())" style="${_dbgMenuItemStyle()}">📋 Copiar SQL completo</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgChequeoSupabase().then(()=>_dbgTab('supabase')))" style="${_dbgMenuItemStyle()}">🔄 Refrescar estado</button>
                </div>
            </div>

            <!-- ▸ Historial ▾ -->
            <div style="position:relative">
                <button onclick="_dbgToggleMenu('dbg-menu-hist')"
                    style="${_dbgBtnStyle('#4c1d95')}">📅 Hist ▾</button>
                <div id="dbg-menu-hist" style="display:none;position:absolute;bottom:28px;right:0;
                    background:#0f172a;border:1px solid #4c1d95;border-radius:6px;
                    min-width:180px;z-index:1000000;box-shadow:0 -4px 16px rgba(0,0,0,.6)">
                    <div style="padding:4px 8px;color:#a78bfa;font-size:10px;font-weight:700;border-bottom:1px solid #1e293b">📅 HISTORIAL</div>
                    <button onclick="_dbgMenuAcc(()=>_dbgGuardarHistorialHoy())" style="${_dbgMenuItemStyle()}">💾 Snapshot de hoy</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgVerHistorial())"         style="${_dbgMenuItemStyle()}">📋 Ver historial</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgTab('hist'))"            style="${_dbgMenuItemStyle()}">📅 Ir a tab Historial</button>
                </div>
            </div>

            <!-- ▸ Log ▾ -->
            <div style="position:relative">
                <button onclick="_dbgToggleMenu('dbg-menu-log')"
                    style="${_dbgBtnStyle('#374151')}">📋 Log ▾</button>
                <div id="dbg-menu-log" style="display:none;position:absolute;bottom:28px;right:0;
                    background:#0f172a;border:1px solid #374151;border-radius:6px;
                    min-width:160px;z-index:1000000;box-shadow:0 -4px 16px rgba(0,0,0,.6)">
                    <div style="padding:4px 8px;color:#94a3b8;font-size:10px;font-weight:700;border-bottom:1px solid #1e293b">📋 LOG</div>
                    <button onclick="_dbgMenuAcc(()=>_dbgTab('log'))"    style="${_dbgMenuItemStyle()}">📋 Ver log</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgTab('health'))" style="${_dbgMenuItemStyle()}">❤️ Salud sistema</button>
                    <button onclick="_dbgMenuAcc(()=>_dbgLimpiar())"     style="${_dbgMenuItemStyle()}">🗑️ Limpiar log</button>
                </div>
            </div>

            <button onclick="_dbgCerrar()"
                style="${_dbgBtnStyle('#7f1d1d')}">✕</button>
        </div>
    </div>

    <!-- TABS -->
    <div id="dbg-tabs" style="display:flex;background:#0f172a;border-bottom:1px solid #1e293b;
         flex-shrink:0;${window._DBG.expanded ? '' : 'display:none!important'}">
        <button onclick="_dbgTab('log')"    id="dbg-tab-log"    style="${_dbgTabStyle(true)}" >📋 Log</button>
        <button onclick="_dbgTab('health')" id="dbg-tab-health" style="${_dbgTabStyle(false)}">❤️ Salud</button>
        <button onclick="_dbgTab('supabase')"id="dbg-tab-supabase"style="${_dbgTabStyle(false)}">☁️ Supabase</button>
        <button onclick="_dbgTab('hist')"   id="dbg-tab-hist"   style="${_dbgTabStyle(false)}">📅 Historial</button>
        <button onclick="_dbgTab('crud')"   id="dbg-tab-crud"   style="${_dbgTabStyle(false)}">⚡ CRUD</button>
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

        <!-- TAB: CRUD (operaciones directas) -->
        <div id="dbg-pane-crud" style="display:none"></div>
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
    return `background:${bg};color:#e2e8f0;border:none;padding:2px 7px;
            border-radius:4px;cursor:pointer;font-size:10px;font-family:monospace`;
}
function _dbgTabStyle(activa) {
    return `background:${activa ? '#1e3a5f' : 'transparent'};color:${activa ? '#7dd3fc' : '#64748b'};
            border:none;padding:4px 10px;cursor:pointer;font-size:10px;font-family:monospace;
            border-bottom:${activa ? '2px solid #3b82f6' : '2px solid transparent'}`;
}
function _dbgMenuItemStyle(bg) {
    return `display:block;width:100%;text-align:left;background:${bg||'transparent'};
            color:#e2e8f0;border:none;padding:5px 12px;cursor:pointer;font-size:10px;
            font-family:monospace;white-space:nowrap;
            transition:background .15s`;
}
// Abre/cierra un menú desplegable del debug bar
function _dbgToggleMenu(id) {
    const menus = ['dbg-menu-supa','dbg-menu-hist','dbg-menu-log'];
    menus.forEach(m => {
        const el = document.getElementById(m);
        if (el) el.style.display = (m === id && el.style.display === 'none') ? 'block' : 'none';
    });
}
// Ejecuta acción y cierra todos los menús
function _dbgMenuAcc(fn) {
    ['dbg-menu-supa','dbg-menu-hist','dbg-menu-log'].forEach(m => {
        const el = document.getElementById(m); if (el) el.style.display = 'none';
    });
    try { fn(); } catch(e) { _dbgLog('❌ ' + e.message, 'error'); }
}
// Cerrar menús al hacer click fuera
document.addEventListener('click', function(e) {
    if (!e.target.closest || !e.target.closest('#dbg-v2')) {
        ['dbg-menu-supa','dbg-menu-hist','dbg-menu-log'].forEach(m => {
            const el = document.getElementById(m); if (el) el.style.display = 'none';
        });
    }
});


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
    ['log','health','supabase','hist','crud'].forEach(t => {
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
    if (nombre === 'crud')     _dbgRenderCRUD();
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
