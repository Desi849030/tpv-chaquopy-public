// tpv_estado_shim.js — Declaración inicial de tpvState (shim global)
    var tpvState = window.tpvState || {
        config:{lang:'es',theme:'light',globalProfitPercent:20},
        productos:[],categorias:[],ordenActual:[],
        ventasDiarias:{},historialVentas:[],inventarios:{},
        cierresCaja:[],licencia:{activada:false,diasPrueba:15,clienteId:''},
        nomencladores:{USD:[100,50,20,10,5,1],EUR:[100,50,20,10,5],CUP:[1000,500,200,100,50,20,10,5,1]},
        nomencladorCantidades:{}
    };
    window.tpvState = tpvState;
    var _dbg_buffer = [];
    function dbg(msg,tipo){
        tipo=tipo||'info';
        var t=new Date().toLocaleTimeString('es',{hour12:false});
        _dbg_buffer.push({t:t,msg:msg,tipo:tipo});
        if(_dbg_buffer.length>300)_dbg_buffer.shift();
        // Rutear al nuevo panel si existe
        if(window.tpvDebugger&&typeof window.tpvDebugger.log==='function'){
            window.tpvDebugger.log(msg,tipo);
        }
    }
    window.dbg = dbg;
    // Shim _dbg_mostrar para compatibilidad
    window._dbg_mostrar = function(){
        if(window.tpvDebugger&&typeof window.tpvDebugger.activar==='function'){
            window.tpvDebugger.activar();
        }
    };
    window._dbg_toggle = window._dbg_mostrar;
    window._dbg_limpiar = function(){
        _dbg_buffer=[];
        if(window.tpvDebugger&&typeof window.tpvDebugger.log==='function'){
            // limpiar log interno
        }
    };
    window.onerror = function(msg,src,line,col,err){
        dbg('❌ [JS] '+msg+' — '+(src||'').split('/').pop()+':'+line,'error');
        return false;
    };
    window.addEventListener('unhandledrejection',function(e){
        dbg('❌ [PROMISE] '+(e.reason?.message||String(e.reason||'')),'error');
    });

// === conf_setLanguage — Cambiar idioma de la interfaz ===
// FIX: Restaurada automáticamente por fix_frontend_real.sh
function conf_setLanguage(lang) {
    try {
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('tpv_lang', lang);
        }
        if (typeof tpv_i18n_apply === 'function') {
            tpv_i18n_apply(lang);
        }
        if (typeof refreshAllUI === 'function') {
            refreshAllUI();
        }
        console.log('[TPV] Idioma cambiado a: ' + lang);
    } catch(e) {
        console.warn('[TPV] Error en conf_setLanguage:', e);
    }
}

// === loadState — Cargar estado desde localStorage ===
// FIX: Restaurada automáticamente por fix_frontend_real.sh
function loadState() {
    try {
        var saved = null;
        if (typeof localStorage !== 'undefined') {
            saved = localStorage.getItem('tpv_state');
        }
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch(e) {
                console.warn('[TPV] Error parseando estado guardado:', e);
            }
        }
        // Estado por defecto
        if (typeof getDefaultState === 'function') {
            return getDefaultState();
        }
        return {
            tab: 'tpv-caja-tab',
            lang: 'es',
            darkMode: false,
            fontSize: 'normal'
        };
    } catch(e) {
        console.warn('[TPV] Error en loadState:', e);
        return {};
    }
}

// === refreshAllUI — Refrescar toda la interfaz según el estado actual ===
// FIX: Restaurada automáticamente por fix_frontend_real.sh
function refreshAllUI() {
    try {
        var state = (typeof loadState === 'function') ? loadState() : {};
        // Refrescar idioma
        var lang = state.lang || 'es';
        if (typeof conf_setLanguage === 'function') {
            conf_setLanguage(lang);
        }
        // Refrescar tema oscuro
        if (typeof applyDarkMode === 'function' && state.darkMode) {
            applyDarkMode(state.darkMode);
        }
        // Refrescar tabs activos
        var activeTab = state.tab;
        if (activeTab) {
            var tabEl = document.getElementById(activeTab);
            if (tabEl && typeof bootstrap !== 'undefined') {
                var tab = new bootstrap.Tab(tabEl);
                tab.show();
            }
        }
        // Refrescar organizeSubmenus si existe
        if (typeof organizeSubmenus === 'function') {
            organizeSubmenus();
        }
        console.log('[TPV] UI refrescada');
    } catch(e) {
        console.warn('[TPV] Error en refreshAllUI:', e);
    }
}


// === FIX: Exportar funciones críticas al scope global ===
// (agregado automáticamente por fix_frontend_real.sh)
try {
  if (typeof conf_setLanguage === 'function' && !window.conf_setLanguage) window.conf_setLanguage = conf_setLanguage;
  if (typeof loadState === 'function' && !window.loadState) window.loadState = loadState;
  if (typeof refreshAllUI === 'function' && !window.refreshAllUI) window.refreshAllUI = refreshAllUI;
  if (typeof initializeUI === 'function' && !window.initializeUI) window.initializeUI = initializeUI;
  if (typeof showToast === 'function' && !window.showToast) window.showToast = showToast;
  if (typeof saveState === 'function' && !window.saveState) window.saveState = saveState;
  if (typeof getDefaultState === 'function' && !window.getDefaultState) window.getDefaultState = getDefaultState;
} catch(e) { console.warn('[FIX] Error exportando funciones:', e); }
