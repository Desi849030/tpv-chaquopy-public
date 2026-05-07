/* ========== v24: Catálogo Cache + Sync Status ========== */
(function(){
  "use strict";
  var CACHE_KEY = 'tpv_catalog_cache';
  var SYNC_KEY = 'tpv_last_sync';
  var CACHE_TTL = 30 * 60 * 1000; /* 30 minutos */

  function saveCache(data){
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        data: data,
        timestamp: Date.now()
      }));
      localStorage.setItem(SYNC_KEY, new Date().toLocaleTimeString());
      console.log('[v24] Catálogo cacheado:', data.length, 'productos');
    } catch(e){}
  }

  function loadCache(){
    try {
      var raw = localStorage.getItem(CACHE_KEY);
      if(!raw) return null;
      var parsed = JSON.parse(raw);
      if(Date.now() - parsed.timestamp > CACHE_TTL){
        return null; /* Expirado */
      }
      return parsed.data;
    } catch(e){ return null; }
  }

  /* Interceptar fetch de productos para cachear */
  var origFetch = window.fetch;
  window.fetch = function(url, opts){
    return origFetch.apply(this, arguments).then(function(resp){
      if(url && (url.indexOf('/api/productos') !== -1 || url.indexOf('/api/catalogo') !== -1 || url.indexOf('/api/inventario') !== -1)){
        resp.clone().json().then(function(data){
          if(Array.isArray(data)) saveCache(data);
          else if(data && data.productos) saveCache(data.productos);
          else if(data && data.data) saveCache(data.data);
        }).catch(function(){});
      }
      return resp;
    }).catch(function(err){
      /* Si falla, intentar usar caché local */
      if(url && (url.indexOf('/api/productos') !== -1 || url.indexOf('/api/catalogo') !== -1)){
        var cached = loadCache();
        if(cached){
          console.log('[v24] Usando catálogo cacheado offline');
          if(window._toast) window._toast('Sin conexión — mostrando datos locales', 'warning');
        }
      }
      throw err;
    });
  };

  /* Mostrar último sync en el UI */
  function showSyncStatus(){
    var bar = document.getElementById('user-bar');
    if(!bar) return;
    var last = localStorage.getItem(SYNC_KEY) || 'Nunca';
    var span = document.createElement('span');
    span.id = 'sync-status';
    span.style.cssText = 'font-size:10px;color:#94a3b8;margin-left:6px;';
    span.textContent = '\uD83D\uDD04 ' + last;
    bar.appendChild(span);
    /* Actualizar cada minuto */
    setInterval(function(){
      var l = localStorage.getItem(SYNC_KEY);
      if(l) span.textContent = '\uD83D\uDD04 ' + l;
    }, 60000);
  }

  setTimeout(function(){
    showSyncStatus();
    console.log('[v24] Catalog cache + sync status listo');
  }, 1500);
})();
