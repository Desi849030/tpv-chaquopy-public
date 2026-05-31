// ==================== CONEXIÓN DE BOTONES A APIs ====================

// Botón: Registrar Venta
window.registrarVenta = async function() {
  var modal = document.createElement('div');
  modal.id = 'modal-venta';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center';
  
  // Obtener productos del catálogo
  var res = await fetch('/api/catalogo');
  var data = await res.json();
  var productos = data.productos || [];
  
  var html = '<div style="background:#1e293b;border:2px solid #10b981;border-radius:16px;padding:20px;width:90%;max-width:500px;max-height:80vh;overflow-y:auto">';
  html += '<h3 style="color:white;margin-bottom:12px">🛒 Registrar Venta</h3>';
  html += '<div style="max-height:300px;overflow-y:auto">';
  
  productos.forEach(function(p, i) {
    html += '<div style="display:flex;align-items:center;gap:8px;padding:8px;border-bottom:1px solid #334155">';
    html += '<span style="flex:1;font-size:.8rem;color:white">'+p.imagen+' '+p.nombre+' - $'+p.precio.toFixed(2)+'</span>';
    html += '<input type="number" id="qty-'+i+'" value="0" min="0" max="'+p.stock+'" style="width:60px;padding:4px;background:#0f172a;border:1px solid #334155;border-radius:4px;color:white;text-align:center;font-size:.8rem" onchange="actualizarTotal()">';
    html += '</div>';
  });
  
  html += '</div>';
  html += '<div style="display:flex;justify-content:space-between;padding:10px;font-weight:700;font-size:1.1rem;color:white;margin-top:10px"><span>Total:</span><span id="venta-total" style="color:#10b981">$0.00</span></div>';
  html += '<select id="metodo-pago" style="width:100%;padding:8px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-top:8px"><option value="efectivo">💵 Efectivo</option><option value="tarjeta">💳 Tarjeta</option><option value="transferencia">🏦 Transferencia</option></select>';
  html += '<div style="display:flex;gap:8px;margin-top:12px"><button onclick="confirmarVenta()" style="flex:1;padding:12px;background:#10b981;border:none;border-radius:8px;color:white;font-weight:600;cursor:pointer;font-size:.9rem">💵 Cobrar</button><button onclick="document.getElementById(\'modal-venta\').remove()" style="flex:1;padding:12px;background:#334155;border:none;border-radius:8px;color:white;cursor:pointer;font-size:.9rem">Cancelar</button></div>';
  html += '</div>';
  
  modal.innerHTML = html;
  document.body.appendChild(modal);
  modal.onclick = function(e) { if (e.target === modal) modal.remove(); };
};

window.actualizarTotal = function() {
  var total = 0;
  var inputs = document.querySelectorAll('#modal-venta input[type=number]');
  var cards = document.querySelectorAll('.product-card');
  inputs.forEach(function(inp, i) {
    var qty = parseInt(inp.value) || 0;
    var precio = parseFloat(cards[i]?.querySelector('.product-price')?.textContent?.replace('$','')) || 0;
    total += qty * precio;
  });
  var el = document.getElementById('venta-total');
  if (el) el.textContent = '$' + total.toFixed(2);
};

window.confirmarVenta = async function() {
  var items = [];
  var inputs = document.querySelectorAll('#modal-venta input[type=number]');
  var cards = document.querySelectorAll('.product-card');
  
  inputs.forEach(function(inp, i) {
    var qty = parseInt(inp.value) || 0;
    if (qty > 0) {
      var nombre = cards[i]?.querySelector('.product-name')?.textContent || 'Producto';
      var precio = parseFloat(cards[i]?.querySelector('.product-price')?.textContent?.replace('$','')) || 0;
      items.push({id: 'prod-'+i, nombre: nombre, cantidad: qty, precio: precio});
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
    alert('✅ Venta registrada!\nTotal: $' + d.total.toFixed(2) + '\nID: ' + d.venta_id);
    document.getElementById('modal-venta').remove();
    if (typeof showCatalogo === 'function') showCatalogo();
    if (typeof showVentas === 'function') showVentas();
  } else {
    alert('❌ Error: ' + (d.error || 'Desconocido'));
  }
};

// Botón: Cerrar Caja
window.cerrarCaja = async function() {
  var hoy = new Date().toISOString().split('T')[0];
  if (!confirm('¿Cerrar caja del día ' + hoy + '?')) return;
  
  var res = await fetch('/api/ventas/cierre', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({fecha: hoy, cerrado_por: 'desarrollador'})
  });
  var d = await res.json();
  
  if (d.ok) {
    alert('✅ Caja cerrada!\nTotal: $' + d.total_ventas.toFixed(2) + '\nTransacciones: ' + d.num_transacciones);
  } else {
    alert('⚠️ ' + (d.error || 'Ya estaba cerrada o sin ventas'));
  }
};

// Botón: Exportar Reporte
window.exportarReporte = function() {
  var hoy = new Date().toISOString().split('T')[0];
  window.open('/api/reportes/exportar?desde=2026-05-01&hasta=' + hoy, '_blank');
};

// Botón: Ver Ventas Hoy
window.verVentasHoy = async function() {
  var res = await fetch('/api/ventas/hoy');
  var d = await res.json();
  
  var html = '<div style="position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center">';
  html += '<div style="background:#1e293b;border:2px solid #6366f1;border-radius:16px;padding:20px;width:90%;max-width:600px;max-height:80vh;overflow-y:auto">';
  html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h3 style="color:white">💰 Ventas de Hoy</h3><button onclick="this.closest(\'div\').parentElement.remove()" style="background:rgba(255,255,255,.1);border:none;color:white;width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:1.2rem">×</button></div>';
  
  if (d.ventas && d.ventas.length > 0) {
    html += '<table style="width:100%;border-collapse:collapse;color:white;font-size:.8rem"><tr style="background:#0f172a"><th style="padding:8px">Producto</th><th style="padding:8px;text-align:right">Cant</th><th style="padding:8px;text-align:right">Precio</th><th style="padding:8px;text-align:right">Total</th></tr>';
    d.ventas.forEach(function(v) {
      html += '<tr style="border-bottom:1px solid #334155"><td style="padding:8px">'+v.producto+'</td><td style="padding:8px;text-align:right">'+v.cantidad+'</td><td style="padding:8px;text-align:right">$'+v.precio_unit.toFixed(2)+'</td><td style="padding:8px;text-align:right;color:#10b981;font-weight:700">$'+v.total.toFixed(2)+'</td></tr>';
    });
    html += '<tr style="font-weight:700"><td colspan="3" style="padding:8px;text-align:right">TOTAL:</td><td style="padding:8px;text-align:right;color:#10b981;font-size:1rem">$'+d.total.toFixed(2)+'</td></tr>';
    html += '</table>';
  } else {
    html += '<p style="color:#94a3b8;text-align:center;padding:20px">No hay ventas hoy</p>';
  }
  html += '</div></div>';
  
  var div = document.createElement('div');
  div.innerHTML = html;
  document.body.appendChild(div.firstElementChild);
  div.firstElementChild.onclick = function(e) { if (e.target === this) this.remove(); };
};

// Botón: Dashboard (métricas en ventana)
window.verDashboard = async function() {
  var res = await fetch('/api/metrics');
  var d = await res.json();
  
  var html = '<div style="position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center">';
  html += '<div style="background:#1e293b;border:2px solid #6366f1;border-radius:16px;padding:20px;width:90%;max-width:500px">';
  html += '<h3 style="color:white;margin-bottom:12px">📊 Dashboard</h3>';
  html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">';
  html += '<div style="background:#0f172a;padding:12px;border-radius:8px;text-align:center"><h2 style="color:#10b981">$'+d.ingresos_hoy.toFixed(2)+'</h2><small style="color:#94a3b8">Ventas Hoy</small></div>';
  html += '<div style="background:#0f172a;padding:12px;border-radius:8px;text-align:center"><h2 style="color:#6366f1">'+d.ventas_hoy+'</h2><small style="color:#94a3b8">Transacciones</small></div>';
  html += '<div style="background:#0f172a;padding:12px;border-radius:8px;text-align:center"><h2 style="color:#f59e0b">'+d.productos+'</h2><small style="color:#94a3b8">Productos</small></div>';
  html += '<div style="background:#0f172a;padding:12px;border-radius:8px;text-align:center"><h2 style="color:#ef4444">$'+d.ganancia_hoy.toFixed(2)+'</h2><small style="color:#94a3b8">Ganancia</small></div>';
  html += '</div><p style="color:#94a3b8;margin-top:12px">🏆 Top: '+d.top_producto+'</p>';
  html += '<button onclick="this.closest(\'div\').parentElement.remove()" style="width:100%;padding:10px;background:#334155;border:none;border-radius:8px;color:white;margin-top:12px;cursor:pointer">Cerrar</button>';
  html += '</div></div>';
  
  var div = document.createElement('div');
  div.innerHTML = html;
  document.body.appendChild(div.firstElementChild);
  div.firstElementChild.onclick = function(e) { if (e.target === this) this.remove(); };
};

// Agregar botones al menú de navegación
setTimeout(function() {
  var nav = document.getElementById('nav-bar');
  if (!nav) return;
  
  var botones = [
    {texto: '🛒 Vender', fn: registrarVenta},
    {texto: '💰 Ventas Hoy', fn: verVentasHoy},
    {texto: '🔒 Cerrar Caja', fn: cerrarCaja},
    {texto: '📥 Exportar', fn: exportarReporte},
    {texto: '📊 Dashboard', fn: verDashboard}
  ];
  
  botones.forEach(function(b) {
    if (document.getElementById('btn-' + b.texto)) return;
    var btn = document.createElement('button');
    btn.id = 'btn-' + b.texto;
    btn.className = 'nav-btn';
    btn.textContent = b.texto;
    btn.onclick = b.fn;
    nav.appendChild(btn);
  });
  
  console.log('✅ Botones conectados: Vender, Ventas Hoy, Cerrar Caja, Exportar, Dashboard');
}, 1500);
