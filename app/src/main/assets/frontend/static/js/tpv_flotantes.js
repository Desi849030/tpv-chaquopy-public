// Botones flotantes funcionales - No interfiere con el frontend
setTimeout(function() {
  var div = document.createElement('div');
  div.id = 'tpv-flotantes';
  div.innerHTML = `
    <button onclick="fetch('/api/catalogo').then(r=>r.json()).then(d=>{var m=document.createElement('div');m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;display:flex;align-items:center;justify-content:center';var h='<div style=background:#1e293b;border:2px solid #10b981;border-radius:16px;padding:20px;width:95%;max-width:500px;max-height:85vh;overflow-y:auto;color:white><h3>🛒 Nueva Venta</h3>';d.productos.forEach((p,i)=>{h+='<div style=display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #334155><span style=flex:1;font-size:.8rem>'+p.imagen+' '+p.nombre+' - $'+p.precio.toFixed(2)+'</span><input type=number id=vq-'+i+' value=0 min=0 style=width:55px;padding:4px;background:#0f172a;border:1px solid #334155;border-radius:6px;color:white;text-align:center;font-size:.75rem></div>'});h+='<div style=display:flex;justify-content:space-between;padding:12px 0;font-weight:700;font-size:1.1rem><span>TOTAL:</span><span id=vt-t>$0.00</span></div><select id=vt-m style=width:100%;padding:8px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:white;margin-bottom:8px><option value=efectivo>Efectivo</option><option value=tarjeta>Tarjeta</option></select><div style=display:flex;gap:8px><button onclick=confirmarTPV() style=flex:1;padding:12px;background:#10b981;border:none;border-radius:8px;color:white;font-weight:700;cursor:pointer>Cobrar</button><button onclick=this.closest(\\'div\\').parentElement.remove() style=flex:1;padding:12px;background:#334155;border:none;border-radius:8px;color:white;cursor:pointer>Cancelar</button></div></div>';m.innerHTML=h;document.body.appendChild(m);m.onclick=function(e){if(e.target===m)m.remove()};window._vt_prods=d.productos;setInterval(function(){var t=0;d.productos.forEach((p,i)=>{var q=parseInt(document.getElementById(\\'vq-\\'+i)?.value)||0;t+=q*p.precio});var el=document.getElementById(\\'vt-t\\');if(el)el.textContent=\\'$\\'+t.toFixed(2)},300)})" style="background:#10b981;border:none;color:white;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer;font-size:.8rem;margin:2px">🛒 Vender</button>
    
    <button onclick="fetch('/api/ventas/hoy').then(r=>r.json()).then(d=>{var m=document.createElement('div');m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;display:flex;align-items:center;justify-content:center';var h='<div style=background:#1e293b;border:2px solid #6366f1;border-radius:16px;padding:20px;width:95%;max-width:600px;max-height:80vh;overflow-y:auto;color:white><h3>💰 Ventas Hoy</h3>';if(d.ventas&&d.ventas.length){h+='<table style=width:100%;border-collapse:collapse;font-size:.8rem><tr style=background:#0f172a><th style=padding:8px>Producto</th><th style=padding:8px;text-align:right>Cant</th><th style=padding:8px;text-align:right>Total</th></tr>';d.ventas.forEach(v=>{h+='<tr style=border-bottom:1px solid #334155><td style=padding:8px>'+v.producto+'</td><td style=padding:8px;text-align:right>'+v.cantidad+'</td><td style=padding:8px;text-align:right;color:#10b981>$'+v.total.toFixed(2)+'</td></tr>'});h+='<tr style=font-weight:700><td colspan=2 style=padding:8px;text-align:right>TOTAL:</td><td style=padding:8px;text-align:right;color:#10b981;font-size:1rem>$'+d.total.toFixed(2)+'</td></tr></table>'}else{h+='<p style=text-align:center;color:#94a3b8;padding:20px>Sin ventas hoy</p>'}h+='<button onclick=this.closest(\\'div\\').parentElement.remove() style=width:100%;padding:10px;background:#334155;border:none;border-radius:8px;color:white;margin-top:12px;cursor:pointer>Cerrar</button></div>';m.innerHTML=h;document.body.appendChild(m);m.onclick=function(e){if(e.target===m)m.remove()}})" style="background:#6366f1;border:none;color:white;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer;font-size:.8rem;margin:2px">💰 Ventas</button>
    
    <button onclick="var h=new Date().toISOString().split('T')[0];if(confirm('¿Cerrar caja '+h+'?')){fetch('/api/ventas/cierre',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fecha:h})}).then(r=>r.json()).then(d=>alert(d.ok?'✅ Caja cerrada: $'+d.total_ventas.toFixed(2):'⚠️ '+d.error))}" style="background:#f59e0b;border:none;color:black;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer;font-size:.8rem;margin:2px">🔒 Cierre</button>
    
    <button onclick="window.open('/api/reportes/exportar?desde=2026-05-01&hasta='+new Date().toISOString().split('T')[0],'_blank')" style="background:#ef4444;border:none;color:white;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer;font-size:.8rem;margin:2px">📥 Exportar</button>
  `;
  div.style.cssText = 'position:fixed;bottom:16px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:999;background:#1e293b;padding:8px 12px;border-radius:20px;border:1px solid #334155;flex-wrap:wrap;justify-content:center';
  document.body.appendChild(div);
  
  // Función global para confirmar venta
  window.confirmarTPV = async function() {
    var items = [];
    (window._vt_prods || []).forEach(function(p, i) {
      var qty = parseInt(document.getElementById('vq-'+i)?.value) || 0;
      if (qty > 0) items.push({id: p.id, nombre: p.nombre, cantidad: qty, precio: p.precio});
    });
    if (!items.length) { alert('Selecciona productos'); return; }
    var metodo = document.getElementById('vt-m')?.value || 'efectivo';
    var res = await fetch('/api/ventas/registrar', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({items: items, metodo_pago: metodo})
    });
    var d = await res.json();
    if (d.ok) { alert('✅ Venta: $' + d.total.toFixed(2)); location.reload(); }
    else { alert('Error: ' + d.error); }
  };
}, 2000);
