#!/usr/bin/env python3
"""v24 Sprint 1: Toasts + Búsqueda + Recibo + Swipe-to-delete"""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(BASE, "app/src/main/assets/frontend")
STATIC = os.path.join(FE, "static")
JS_DIR = os.path.join(STATIC, "js")
CSS_DIR = os.path.join(STATIC, "css")

# ============================================================
# 1) NUEVO ARCHIVO: toast_system.js
# ============================================================
toast_js = r'''/* ========== v24: Toast System Autónomo ========== */
(function(){
  "use strict";
  var _container = null;
  var _icons = {
    success: '\u2705', danger: '\u274C', warning: '\u26A0\uFE0F', info: '\u2139\uFE0F'
  };
  var _colors = {
    success: '#10b981', danger: '#ef4444', warning: '#f59e0b', info: '#3b82f6'
  };

  function _getContainer(){
    if(_container) return _container;
    _container = document.createElement('div');
    _container.id = 'tpv-toast-container';
    _container.style.cssText = 'position:fixed;top:70px;right:12px;z-index:99999;display:flex;flex-direction:column;gap:8px;max-width:340px;width:90%;pointer-events:none;';
    document.body.appendChild(_container);
    return _container;
  }

  function _toast(msg, type){
    type = type || 'info';
    var c = _getContainer();
    var el = document.createElement('div');
    el.style.cssText = 'pointer-events:auto;display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:12px;background:' + _colors[type] + ';color:#fff;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.25);transform:translateX(120%);transition:transform 0.35s cubic-bezier(.4,0,.2,1),opacity 0.35s;opacity:0;';
    el.innerHTML = '<span style="font-size:18px;">' + (_icons[type]||'') + '</span><span style="flex:1;">' + msg + '</span>';
    c.appendChild(el);
    requestAnimationFrame(function(){
      el.style.transform = 'translateX(0)';
      el.style.opacity = '1';
    });
    setTimeout(function(){
      el.style.transform = 'translateX(120%)';
      el.style.opacity = '0';
      setTimeout(function(){ if(el.parentNode) el.parentNode.removeChild(el); }, 400);
    }, 3500);
    el.addEventListener('click', function(){
      el.style.transform = 'translateX(120%)';
      el.style.opacity = '0';
      setTimeout(function(){ if(el.parentNode) el.parentNode.removeChild(el); }, 400);
    });
  }

  /* Reemplazar alert() global */
  window._origAlert = window.alert;
  window.alert = function(msg){
    _toast(String(msg), 'warning');
  };

  /* Exponer _toast global para uso en otros scripts */
  window._toast = _toast;

  /* Exponer showToast como alias */
  window.showToast = function(msg, type){ _toast(msg, type); };

  /* Detectar cuando showToast ya existía y era usada */
  if(typeof window.__tpv_toast_init === 'undefined'){
    window.__tpv_toast_init = true;
    console.log('[v24] Toast system cargado');
  }
})();
'''
toast_path = os.path.join(JS_DIR, "toast_system.js")
with open(toast_path, 'w') as f:
    f.write(toast_js)
print(f"[OK] {toast_path} ({len(toast_js)} bytes)")

# ============================================================
# 2) NUEVO CSS: catalog_search.css + swipe_actions.css
# ============================================================
extra_css = r'''/* ========== v24: Catalog Search ========== */
#catalog-search-wrap {
  padding: 10px 12px 6px;
}
#catalog-search {
  width: 100%;
  padding: 10px 14px 10px 38px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  font-size: 14px;
  background: #f8fafc url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2394a3b8' viewBox='0 0 16 16'%3E%3Cpath d='M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85zm-5.242.156a5 5 0 1 1 0-10 5 5 0 0 1 0 10z'/%3E%3C/svg%3E") 12px center no-repeat;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}
#catalog-search:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.2);
}
#catalog-search::placeholder { color: #94a3b8; }

.product-row-hidden { display: none !important; }

/* ========== v24: Swipe Actions on Order Items ========== */
.orden-item {
  position: relative;
  overflow: hidden;
  transition: transform 0.25s cubic-bezier(.4,0,.2,1);
  touch-action: pan-y;
}
.orden-item-bg {
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  font-size: 22px;
  border-radius: 0 12px 12px 0;
}
.orden-item.swiped { transform: translateX(-80px); }
.orden-qty-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.orden-qty-btn {
  width: 30px; height: 30px;
  border-radius: 8px;
  border: 2px solid #667eea;
  background: transparent;
  color: #667eea;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}
.orden-qty-btn:active {
  background: #667eea;
  color: #fff;
  transform: scale(0.9);
}

/* ========== v24: Print Receipt ========== */
@media print {
  body * { visibility: hidden !important; }
  #tpv-receipt-print, #tpv-receipt-print * {
    visibility: visible !important;
  }
  #tpv-receipt-print {
    position: absolute;
    left: 0; top: 0;
    width: 80mm;
    padding: 4mm;
    font-size: 12px;
    color: #000 !important;
    background: #fff !important;
  }
  #tpv-receipt-print .receipt-header {
    text-align: center;
    border-bottom: 1px dashed #000;
    padding-bottom: 6px;
    margin-bottom: 8px;
    font-size: 14px;
    font-weight: bold;
  }
  #tpv-receipt-print .receipt-row {
    display: flex;
    justify-content: space-between;
    padding: 2px 0;
  }
  #tpv-receipt-print .receipt-total {
    border-top: 1px dashed #000;
    margin-top: 6px;
    padding-top: 6px;
    font-weight: bold;
    font-size: 14px;
  }
  #tpv-receipt-print .receipt-footer {
    text-align: center;
    margin-top: 10px;
    font-size: 10px;
    color: #555 !important;
  }
}
.btn-print-receipt {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.btn-print-receipt:active {
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(99,102,241,0.4);
}
'''
css_path = os.path.join(CSS_DIR, "v24_extras.css")
with open(css_path, 'w') as f:
    f.write(extra_css)
print(f"[OK] {css_path} ({len(extra_css)} bytes)")

# ============================================================
# 3) NUEVO: catalog_and_order.js
# ============================================================
catalog_js = r'''/* ========== v24: Catalog Search + Swipe + Receipt ========== */
(function(){
  "use strict";

  /* ----- CATALOG SEARCH ----- */
  function initCatalogSearch(){
    var tabs = ['gestion-productos-tab','inv-inventario-tab','catalogo-tab','cliente-catalogo-tab'];
    tabs.forEach(function(tabId){
      var tab = document.getElementById(tabId);
      if(!tab) return;
      /* Insertar barra de búsqueda al inicio */
      var existing = document.getElementById('catalog-search');
      if(existing) return;
      var wrap = document.createElement('div');
      wrap.id = 'catalog-search-wrap';
      var input = document.createElement('input');
      input.type = 'text';
      input.id = 'catalog-search';
      input.placeholder = '\uD83D\uDD0D Buscar producto...';
      input.autocomplete = 'off';
      wrap.appendChild(input);
      tab.parentNode.insertBefore(wrap, tab);
      input.addEventListener('input', function(){
        var q = this.value.toLowerCase().trim();
        var rows = tab.querySelectorAll('tr, .producto-card, .card');
        rows.forEach(function(row){
          var text = (row.textContent || '').toLowerCase();
          if(q === '' || text.indexOf(q) !== -1){
            row.classList.remove('product-row-hidden');
          } else {
            row.classList.add('product-row-hidden');
          }
        });
      });
    });
  }

  /* ----- SWIPE TO DELETE + QTY BUTTONS ----- */
  function initSwipeActions(){
    var ordenTab = document.getElementById('orden-actual-tab');
    if(!ordenTab) return;
    /* Observar cambios en el tab para aplicar a nuevos items */
    var observer = new MutationObserver(function(){
      applySwipeToItems();
    });
    observer.observe(ordenTab, { childList: true, subtree: true });
    applySwipeToItems();
  }

  function applySwipeToItems(){
    var items = document.querySelectorAll('.orden-item');
    items.forEach(function(item){
      if(item.dataset.swipeInit === '1') return;
      item.dataset.swipeInit = '1';
      /* Crear fondo de swipe */
      var bg = document.createElement('div');
      bg.className = 'orden-item-bg';
      bg.innerHTML = '\uD83D\uDDD1\uFE0F';
      item.style.position = 'relative';
      item.insertBefore(bg, item.firstChild);
      var startX = 0, currentX = 0, swiping = false;
      item.addEventListener('touchstart', function(e){
        startX = e.touches[0].clientX;
        swiping = false;
      }, {passive: true});
      item.addEventListener('touchmove', function(e){
        currentX = e.touches[0].clientX;
        var diff = startX - currentX;
        if(diff > 10) swiping = true;
        if(swiping){
          var tx = Math.min(diff, 80);
          item.style.transform = 'translateX(-' + tx + 'px)';
        }
      }, {passive: true});
      item.addEventListener('touchend', function(){
        var diff = startX - currentX;
        if(diff > 50){
          item.classList.add('swiped');
        } else {
          item.style.transform = '';
          item.classList.remove('swiped');
        }
      });
      /* Tap en fondo rojo = eliminar */
      bg.addEventListener('click', function(){
        if(typeof window.eliminarProductoOrden === 'function'){
          var idx = Array.from(item.parentNode.children).indexOf(item);
          window.eliminarProductoOrden(idx);
        }
        item.style.transform = 'translateX(-120%)';
        item.style.opacity = '0';
        setTimeout(function(){ if(item.parentNode) item.parentNode.removeChild(item); }, 300);
      });
    });

    /* Agregar botones +/- si no existen */
    var qtyCells = document.querySelectorAll('.orden-qty');
    qtyCells.forEach(function(cell){
      if(cell.querySelector('.orden-qty-controls')) return;
      var val = parseInt(cell.textContent) || 1;
      var controls = document.createElement('div');
      controls.className = 'orden-qty-controls';
      var btnMinus = document.createElement('button');
      btnMinus.className = 'orden-qty-btn';
      btnMinus.textContent = '\u2212';
      var span = document.createElement('span');
      span.textContent = val;
      span.style.cssText = 'min-width:24px;text-align:center;font-weight:600;';
      var btnPlus = document.createElement('button');
      btnPlus.className = 'orden-qty-btn';
      btnPlus.textContent = '+';
      controls.appendChild(btnMinus);
      controls.appendChild(span);
      controls.appendChild(btnPlus);
      cell.innerHTML = '';
      cell.appendChild(controls);
      btnMinus.addEventListener('click', function(){
        var nv = parseInt(span.textContent) - 1;
        if(nv < 1) nv = 1;
        span.textContent = nv;
        if(typeof window.actualizarCantidadOrden === 'function') window.actualizarCantidadOrden();
      });
      btnPlus.addEventListener('click', function(){
        var nv = parseInt(span.textContent) + 1;
        span.textContent = nv;
        if(typeof window.actualizarCantidadOrden === 'function') window.actualizarCantidadOrden();
      });
    });
  }

  /* ----- PRINT RECEIPT ----- */
  window.imprimirRecibo = function(venta){
    var html = '<div id="tpv-receipt-print">';
    html += '<div class="receipt-header">' + (venta.tienda || 'TPV') + '</div>';
    html += '<div class="receipt-row"><span>Fecha:</span><span>' + (venta.fecha || new Date().toLocaleString()) + '</span></div>';
    html += '<div class="receipt-row"><span>Vendedor:</span><span>' + (venta.vendedor || 'Sistema') + '</span></div>';
    html += '<div class="receipt-row"><span>Cliente:</span><span>' + (venta.cliente || 'General') + '</span></div>';
    html += '<hr style="border-top:1px dashed #000;margin:6px 0;">';
    var items = venta.items || [];
    items.forEach(function(it){
      html += '<div class="receipt-row"><span>' + (it.nombre || it.producto || '') + ' x' + (it.cantidad || 1) + '</span><span>$' + (it.subtotal || it.precio * it.cantidad || 0).toFixed(2) + '</span></div>';
    });
    html += '<div class="receipt-total"><span>TOTAL:</span><span>$' + (venta.total || 0).toFixed(2) + '</span></div>';
    html += '<div class="receipt-footer">Gracias por su compra</div>';
    html += '</div>';
    var printDiv = document.createElement('div');
    printDiv.innerHTML = html;
    document.body.appendChild(printDiv);
    setTimeout(function(){
      window.print();
      setTimeout(function(){ document.body.removeChild(printDiv); }, 500);
    }, 200);
  };

  /* ----- INIT ----- */
  function init(){
    setTimeout(function(){
      initCatalogSearch();
      initSwipeActions();
      console.log('[v24] Catalog search + swipe + receipt listo');
    }, 800);
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
'''
catalog_path = os.path.join(JS_DIR, "catalog_and_order.js")
with open(catalog_path, 'w') as f:
    f.write(catalog_js)
print(f"[OK] {catalog_path} ({len(catalog_js)} bytes)")

# ============================================================
# 4) AGREGAR SCRIPTS A index.html
# ============================================================
index_path = os.path.join(FE, "templates", "index.html")
with open(index_path, 'r') as f:
    html = f.read()

# Agregar toast_system.js ANTES de todos los scripts (primero)
if 'toast_system.js' not in html:
    html = html.replace(
        '<script src="static/lib/',
        '<script src="static/js/toast_system.js"></script>\n    <script src="static/lib/'
    )
    print("[OK] toast_system.js agregado a index.html")

# Agregar v24_extras.css
if 'v24_extras.css' not in html:
    html = html.replace(
        '</head>',
        '  <link rel="stylesheet" href="static/css/v24_extras.css">\n</head>'
    )
    print("[OK] v24_extras.css agregado a index.html")

# Agregar catalog_and_order.js DESPUÉS de script_12
if 'catalog_and_order.js' not in html:
    html = html.replace(
        '<script src="static/js/script_12.js"></script>',
        '<script src="static/js/script_12.js"></script>\n    <script src="static/js/catalog_and_order.js"></script>'
    )
    print("[OK] catalog_and_order.js agregado a index.html")

with open(index_path, 'w') as f:
    f.write(html)

# ============================================================
# 5) REEMPLAZAR alert() EN script_8.js
# ============================================================
s8_path = os.path.join(JS_DIR, "script_8.js")
if os.path.exists(s8_path):
    with open(s8_path, 'r') as f:
        s8 = f.read()
    count = s8.count('alert(')
    # Reemplazar alert() con _toast() — solo los alert simples con string
    s8_new = re.sub(r"\balert\(['\"]([^'\"]*?)['\"]\)", r"_toast('\1','warning')", s8)
    replaced = count - s8_new.count('alert(')
    if replaced > 0:
        with open(s8_path, 'w') as f:
            f.write(s8_new)
        print(f"[OK] {replaced} alert() reemplazados con _toast() en script_8.js")
    else:
        print("[INFO] No se encontraron alert() simples para reemplazar")
else:
    print(f"[SKIP] script_8.js no encontrado")

# ============================================================
# RESUMEN
# ============================================================
print("\n=== v24 SPRINT 1 COMPLETADO ===")
print("Archivos creados:")
print(f"  - toast_system.js ({len(toast_js)} bytes)")
print(f"  - v24_extras.css ({len(extra_css)} bytes)")
print(f"  - catalog_and_order.js ({len(catalog_js)} bytes)")
print("Modificados:")
print("  - index.html (3 inserciones)")
print("  - script_8.js (alert→_toast)")
