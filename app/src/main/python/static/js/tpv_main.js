
// ========== PATCH AUTO: DEBOUNCE PARA SAVESTATE ==========
(function patchDebounce() {
    if (typeof window.saveState === 'function') {
        const original = window.saveState;
        window.saveState = function() {
            if (window.saveState._timer) clearTimeout(window.saveState._timer);
            window.saveState._timer = setTimeout(() => {
                original();
                window.saveState._timer = null;
            }, 500);
        };
        window.saveState.flush = function() {
            if (window.saveState._timer) {
                clearTimeout(window.saveState._timer);
                window.saveState._timer = null;
            }
            original();
        };
        console.log('[PATCH] Debounce aplicado a saveState');
    } else {
        console.warn('[PATCH] saveState no encontrada en window - debounce NO aplicado');
    }
})();
// ========== FIN PATCH DEBOUNCE ==========

// ========== PATCH AUTO: RECONEXIÓN SSE CON BACKOFF ==========
(function patchSSE() {
    let retryDelay = 1000;
    let retryTimer = null;
    
    // Esperar a que _sseSource esté disponible
    const waitForSSE = setInterval(() => {
        if (typeof window._sseSource !== 'undefined' && window._sseSource) {
            clearInterval(waitForSSE);
            
            const originalError = window._sseSource.onerror;
            const originalOpen = window._sseSource.onopen;
            
            window._sseSource.onerror = function(e) {
                if (window._sseSource) {
                    window._sseSource.close();
                    window._sseSource = null;
                }
                
                if (retryTimer) clearTimeout(retryTimer);
                
                console.warn('[SSE PATCH] Reconectando en ' + (retryDelay/1000) + 's...');
                retryTimer = setTimeout(() => {
                    if (typeof _iniciarSSE === 'function') _iniciarSSE();
                    retryTimer = null;
                }, retryDelay);
                
                retryDelay = Math.min(retryDelay * 2, 30000);
                
                if (originalError) originalError.call(this, e);
            };
            
            window._sseSource.onopen = function(e) {
                retryDelay = 1000;
                console.log('[SSE PATCH] Conectado - delay reseteado');
                if (originalOpen) originalOpen.call(this, e);
            };
            
            console.log('[PATCH] Reconexión SSE aplicada');
        }
    }, 100);
    
    // Dejar de buscar después de 10 segundos
    setTimeout(() => clearInterval(waitForSSE), 10000);
})();
// ========== FIN PATCH SSE ==========

// ========== PATCH AUTO: DEBOUNCE PARA SAVESTATE ==========
(function patchDebounce() {
    if (typeof window.saveState === 'function') {
        const original = window.saveState;
        window.saveState = function() {
            if (window.saveState._timer) clearTimeout(window.saveState._timer);
            window.saveState._timer = setTimeout(() => {
                original();
                window.saveState._timer = null;
            }, 500);
        };
        window.saveState.flush = function() {
            if (window.saveState._timer) {
                clearTimeout(window.saveState._timer);
                window.saveState._timer = null;
            }
            original();
        };
        console.log('[PATCH] Debounce aplicado a saveState');
    }
})();
// ========== FIN PATCH DEBOUNCE ==========

// ========== PATCH AUTO: RECONEXIÓN SSE CON BACKOFF ==========
(function patchSSE() {
    let retryDelay = 1000;
    let retryTimer = null;
    
    const waitForSSE = setInterval(() => {
        if (typeof window._sseSource !== 'undefined' && window._sseSource) {
            clearInterval(waitForSSE);
            
            const originalError = window._sseSource.onerror;
            const originalOpen = window._sseSource.onopen;
            
            window._sseSource.onerror = function(e) {
                if (window._sseSource) {
                    window._sseSource.close();
                    window._sseSource = null;
                }
                if (retryTimer) clearTimeout(retryTimer);
                retryTimer = setTimeout(() => {
                    if (typeof _iniciarSSE === 'function') _iniciarSSE();
                    retryTimer = null;
                }, retryDelay);
                retryDelay = Math.min(retryDelay * 2, 30000);
                if (originalError) originalError.call(this, e);
            };
            
            window._sseSource.onopen = function(e) {
                retryDelay = 1000;
                if (originalOpen) originalOpen.call(this, e);
            };
        }
    }, 100);
    setTimeout(() => clearInterval(waitForSSE), 10000);
})();
// ========== FIN PATCH SSE ==========

// ========== PATCH: DEBOUNCE SAVESTATE ==========
(function patchDebounce() {
    if (typeof window.saveState === 'function') {
        const original = window.saveState;
        window.saveState = function() {
            if (window.saveState._timer) clearTimeout(window.saveState._timer);
            window.saveState._timer = setTimeout(() => { original(); window.saveState._timer = null; }, 500);
        };
        window.saveState.flush = function() {
            if (window.saveState._timer) { clearTimeout(window.saveState._timer); window.saveState._timer = null; }
            original();
        };
    }
})();

// ========== PATCH: SSE RECONEXION ==========
(function patchSSE() {
    let d=1000,t=null,w=setInterval(()=>{
        if(typeof window._sseSource!=='undefined'&&window._sseSource){
            clearInterval(w);
            let oe=window._sseSource.onerror,oo=window._sseSource.onopen;
            window._sseSource.onerror=function(e){
                if(window._sseSource){window._sseSource.close();window._sseSource=null;}
                if(t)clearTimeout(t);
                t=setTimeout(()=>{if(typeof _iniciarSSE==='function')_iniciarSSE();},d);
                d=Math.min(d*2,30000);
                if(oe)oe.call(this,e);
            };
            window._sseSource.onopen=function(e){d=1000;if(oo)oo.call(this,e);};
        }
    },100);
    setTimeout(()=>clearInterval(w),10000);
})();
