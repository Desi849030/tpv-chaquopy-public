/* ========== v25: Catálogo Cache IndexedDB + Sync Status ========== */
/* Migración de localStorage (5MB, síncrono) a IndexedDB (sin límite, asíncrono) */
(function(){
  "use strict";

  var DB_NAME    = 'tpv_cache_db';
  var DB_VERSION = 1;
  var STORE_NAME = 'catalog';
  var CACHE_KEY  = 'productos';
  var SYNC_KEY   = 'tpv_last_sync';
  var CACHE_TTL  = 30 * 60 * 1000; /* 30 minutos */

  var _db = null;

  /* ── Abrir / crear la base IndexedDB ── */
  function openDB(){
    return new Promise(function(resolve, reject){
      if(_db){ resolve(_db); return; }
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function(e){
        var db = e.target.result;
        if(!db.objectStoreNames.contains(STORE_NAME)){
          db.createObjectStore(STORE_NAME, { keyPath: 'key' });
        }
      };
      req.onsuccess = function(e){
        _db = e.target.result;
        resolve(_db);
      };
      req.onerror = function(e){
        reject(e.target.error);
      };
    });
  }

  /* ── Guardar en IndexedDB ── */
  function saveCache(data){
    openDB().then(function(db){
      var tx    = db.transaction(STORE_NAME, 'readwrite');
      var store = tx.objectStore(STORE_NAME);
      store.put({ key: CACHE_KEY, data: data, timestamp: Date.now() });
      try{ tpvStorage.setItem(SYNC_KEY, new Date().toLocaleTimeString()); }catch(e){}
      console.log('[v25] IndexedDB: catálogo guardado (' + data.length + ' productos)');
    }).catch(function(e){
      console.warn('[v25] IndexedDB save falló:', e);
    });
  }

  /* ── Leer de IndexedDB ── */
  function loadCache(){
    return openDB().then(function(db){
      return new Promise(function(resolve){
        var tx    = db.transaction(STORE_NAME, 'readonly');
        var store = tx.objectStore(STORE_NAME);
        var req   = store.get(CACHE_KEY);
        req.onsuccess = function(e){
          var rec = e.target.result;
          if(!rec){ resolve(null); return; }
          if(Date.now() - rec.timestamp > CACHE_TTL){ resolve(null); return; }
          resolve(rec.data);
        };
        req.onerror = function(){ resolve(null); };
      });
    }).catch(function(){ return null; });
  }

  /* ── Invalidar cache (llamar tras importación Excel) ── */
  window.tpv_invalidarCache = function(){
    openDB().then(function(db){
      var tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).delete(CACHE_KEY);
      console.log('[v25] Cache invalidado tras importación');
    }).catch(function(){});
  };

  /* ── Interceptar fetch para cachear y hacer fallback offline ── */
  var origFetch = window.fetch;
  window.fetch = function(url, opts){
    var isProductUrl = url && (
      url.indexOf('/api/productos')  !== -1 ||
      url.indexOf('/api/catalogo')   !== -1 ||
      url.indexOf('/api/inventario') !== -1
    );
    var isGET = !opts || !opts.method || opts.method === 'GET';

    return origFetch.apply(this, arguments).then(function(resp){
      if(isProductUrl && isGET){
        resp.clone().json().then(function(data){
          var lista = Array.isArray(data) ? data
                    : (data && data.productos) ? data.productos
                    : (data && data.data)      ? data.data
                    : null;
          if(lista) saveCache(lista);
        }).catch(function(){});
      }
      return resp;
    }).catch(function(err){
      /* ── FALLBACK OFFLINE REAL ── */
      if(isProductUrl && isGET){
        return loadCache().then(function(cached){
          if(cached){
            console.log('[v25] Offline: sirviendo', cached.length, 'productos desde IndexedDB');
            if(window._toast) window._toast('Sin conexión — datos locales', 'warning');
            return new Response(JSON.stringify(cached), {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            });
          }
          throw err;
        });
      }
      throw err;
    });
  };

  /* ── Estado de sync en el UI (con MutationObserver) ── */
  function showSyncStatus(){
    var existing = document.getElementById('sync-status');
    if(existing) return;
    var bar = document.getElementById('user-bar');
    if(!bar) return;
    var last = tpvStorage.getItem(SYNC_KEY) || 'Nunca';
    var span = document.createElement('span');
    span.id = 'sync-status';
    span.style.cssText = 'font-size:10px;color:#94a3b8;margin-left:6px;';
    span.textContent = '\uD83D\uDD04 ' + last;
    bar.appendChild(span);
    setInterval(function(){
      var l = tpvStorage.getItem(SYNC_KEY);
      if(l) span.textContent = '\uD83D\uDD04 ' + l;
    }, 60000);
  }

  /* Esperar a que user-bar exista */
  var _obs = new MutationObserver(function(){
    var bar = document.getElementById('user-bar');
    if(bar){ showSyncStatus(); _obs.disconnect(); }
  });
  _obs.observe(document.body || document.documentElement, { childList: true, subtree: true });

  /* Verificar soporte */
  if(!window.indexedDB){
    console.warn('[v25] IndexedDB no disponible — sin cache offline');
  } else {
    openDB().then(function(){
      console.log('[v25] IndexedDB lista — cache offline activo');
    });
  }

})();
