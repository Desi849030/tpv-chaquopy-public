/* ========== v24: Catalog Search + Swipe + Receipt ========== */
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
          } else { // 'interactive' o 'complete'
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
        } else { // 'interactive' o 'complete'
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
/* ----- INIT ----- */
function tryInit(){
  initCatalogSearch();
  initSwipeActions();
  console.log('[v24] Catalog search + swipe + receipt listo');
}
if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', tryInit);
} else { // 'interactive' o 'complete' — DOM ya listo
  tryInit();
}
})();
