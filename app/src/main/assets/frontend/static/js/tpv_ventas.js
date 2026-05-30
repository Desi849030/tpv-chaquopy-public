// Módulo de Ventas Rápidas
window.registrarVenta = async function() {
  var items = [];
  var total = 0;
  
  // Tomar productos del catálogo visible
  var cards = document.querySelectorAll('.product-card');
  if (!cards.length) { alert('No hay productos visibles'); return; }
  
  var html = '<div style="max-height:300px;overflow-y:auto">';
  cards.forEach(function(card, i) {
    var nombre = card.querySelector('.product-name')?.textContent || 'Producto ' + i;
    var precio = parseFloat(card.querySelector('.product-price')?.textContent?.replace('$','')) || 0;
    var stock = parseInt(card.querySelector('.product-stock')?.textContent?.replace('Stock: ','')) || 0;
    html += '<div style="display:flex;align-items:center;gap:8px;padding:8px;border-bottom:1px solid #334155">' +
      '<span style="flex:1;font-size:.8rem">'+nombre+' - $'+precio.toFixed(2)+' (Stock:'+stock+')</span>' +
      '<input type="number" id="qty-'+i+'" value="0" min="0" max="'+stock+'" style="width:60px;padding:4px;background:#0f172a;border:1px solid #334155;border-radius:4px;color:white;text-align:center;font-size:.8rem" onchange="actualizarTotalVenta()">' +
      '</div>';
  });
  html += '</div>';
  html += '<div style="display:flex;justify-content:space-between;padding:10px;font-weight:700;font-size:1rem;margin-top:10px"><span>Total:</span><span id="venta-total-preview">$0.00</span></div>';
  html += '<select id="metodo-pago" style="width:100%;padding:8px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-top:8px"><option value="efectivo">Efectivo</option><option value="tarjeta">Tarjeta</option><option value="transferencia">Transferencia</option></select>';
  html += '<div style="display:flex;gap:8px;margin-top:12px"><button onclick="confirmarVenta()" style="flex:1;padding:10px;background:#10b981;border:none;border-radius:8px;color:white;font-weight:600;cursor:pointer">Cobrar</button><button onclick="document.getElementById(\'modal-venta\').remove()" style="flex:1;padding:10px;background:#334155;border:none;border-radius:8px;color:white;cursor:pointer">Cancelar</button></div>';
  
  var modal = document.createElement('div');
  modal.id = 'modal-venta';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center';
  modal.innerHTML = '<div style="background:#1e293b;border:2px solid #10b981;border-radius:16px;padding:20px;width:90%;max-width:500px"><h3 style="color:white;margin-bottom:12px">🛒 Nueva Venta</h3>' + html + '</div>';
  document.body.appendChild(modal);
  modal.onclick = function(e) { if (e.target === modal) modal.remove(); };
};

window.actualizarTotalVenta = function() {
  var total = 0;
  var cards = document.querySelectorAll('.product-card');
  cards.forEach(function(card, i) {
    var qty = parseInt(document.getElementById('qty-'+i)?.value) || 0;
    var precio = parseFloat(card.querySelector('.product-price')?.textContent?.replace('$','')) || 0;
    total += qty * precio;
  });
  var el = document.getElementById('venta-total-preview');
  if (el) el.textContent = '$' + total.toFixed(2);
};

window.confirmarVenta = async function() {
  var items = [];
  var cards = document.querySelectorAll('.product-card');
  cards.forEach(function(card, i) {
    var qty = parseInt(document.getElementById('qty-'+i)?.value) || 0;
    if (qty > 0) {
      var id = card.getAttribute('data-id') || ('prod-' + i);
      var nombre = card.querySelector('.product-name')?.textContent || 'Producto';
      var precio = parseFloat(card.querySelector('.product-price')?.textContent?.replace('$','')) || 0;
      items.push({id: id, nombre: nombre, cantidad: qty, precio: precio});
    }
  });
  
  if (!items.length) { alert('Selecciona al menos un producto'); return; }
  
  var metodo = document.getElementById('metodo-pago')?.value || 'efectivo';
  
  var res = await fetch('/api/ventas/registrar', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({items: items, metodo_pago: metodo, vendedor: 'desarrollador'})
  });
  var d = await res.json();
  
  if (d.ok) {
    alert('✅ Venta registrada! Total: $' + d.total.toFixed(2) + ' | ID: ' + d.venta_id);
    var modal = document.getElementById('modal-venta');
    if (modal) modal.remove();
    // Recargar catálogo
    if (typeof showCatalogo === 'function') showCatalogo();
  } else {
    alert('Error: ' + (d.error || 'Desconocido'));
  }
};
