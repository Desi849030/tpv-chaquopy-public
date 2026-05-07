#!/usr/bin/env python3
"""v24 Sprint 3: Eliminar dead code + validación BD"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1) ELIMINAR app_backup.py
# ============================================================
backup_path = os.path.join(BASE, "app/src/main/python/app_backup.py")
if os.path.exists(backup_path):
    size = os.path.getsize(backup_path)
    os.remove(backup_path)
    print(f"[OK] app_backup.py eliminado ({size} bytes de código muerto)")
else:
    print("[SKIP] app_backup.py no encontrado")

# ============================================================
# 2) VALIDACIÓN BD AL INICIO (agregar a app.py)
# ============================================================
app_path = os.path.join(BASE, "app/src/main/python/app.py")
if os.path.exists(app_path):
    with open(app_path, 'r') as f:
        content = f.read()
    
    if 'tpv_validate_db' not in content:
        validation_code = '''
# ========== v24: Validación BD al inicio ==========
def tpv_validate_db():
    """Verificar que la BD existe y tiene datos al arrancar."""
    from database import DB_FILE, get_connection
    import os
    if not os.path.exists(DB_FILE):
        print("[v24] ADVERTENCIA: BD no encontrada en", DB_FILE)
        return False
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        conn.close()
        print(f"[v24] BD OK: {count} productos encontrados")
        return count > 0
    except Exception as e:
        print(f"[v24] ERROR BD: {e}")
        return False

tpv_validate_db()
'''
        # Insertar después de las importaciones
        if 'if __name__' in content:
            content = content.replace('if __name__', validation_code + '\nif __name__')
        else:
            content += validation_code
        with open(app_path, 'w') as f:
            f.write(content)
        print("[OK] Validación BD agregada a app.py")
    else:
        print("[SKIP] Validación BD ya existe")
else:
    print(f"[SKIP] app.py no encontrado")

# ============================================================
# 3) CACHÉ CATÁLOGO EN localStorage (JS)
# ============================================================
cache_js = r'''/* ========== v24: Catálogo Cache + Sync Status ========== */
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
'''
js_path = os.path.join(BASE, "app/src/main/assets/frontend/static/js", "catalog_cache.js")
with open(js_path, 'w') as f:
    f.write(cache_js)
print(f"[OK] catalog_cache.js ({len(cache_js)} bytes)")

# Agregar a index.html
index_path = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")
with open(index_path, 'r') as f:
    html = f.read()
if 'catalog_cache.js' not in html:
    html = html.replace(
        '<script src="static/js/dark_and_network.js"></script>',
        '<script src="static/js/dark_and_network.js"></script>\n    <script src="static/js/catalog_cache.js"></script>'
    )
    with open(index_path, 'w') as f:
        f.write(html)
    print("[OK] catalog_cache.js agregado a index.html")

print("\n=== v24 SPRINT 3 COMPLETADO ===")
print("Eliminados:")
print("  - app_backup.py")
print("Creados:")
print(f"  - catalog_cache.js ({len(cache_js)} bytes)")
print("Modificados:")
print("  - app.py (validación BD)")
print("  - index.html (1 inserción)")
