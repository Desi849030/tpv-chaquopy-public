// tpv_debugger.js — Panel de debug inteligente + monitor Supabase + diagnóstico

// ══════════════════════════════════════════════════════════════
//  ESTADO INTERNO DEL DEBUGGER
// ══════════════════════════════════════════════════════════════
// Acceso directo a métricas del sistema
window._DBG_METRICAS = function(){ window.open('/dev/metricas','_blank'); };

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
