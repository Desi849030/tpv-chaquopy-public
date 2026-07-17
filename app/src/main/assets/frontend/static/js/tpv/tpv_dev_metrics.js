window.DM = {
  fetch: function() {
    var s = document.getElementById('dm-status');
    if(s) s.textContent = 'actualizando...';
    fetch('/api/dev/metrics').then(function(r){return r.json()}).then(function(d){
      if(!d.ok){if(s) s.textContent='Error: '+(d.error||'?'); return;}
      if(s) s.textContent='actualizado';
      var m = d.metrics || {};
      // RAM
      DM.set('dm-ram-proceso', m.ram_proceso);
      DM.set('dm-ram-sys-pct', m.ram_sistema);
      DM.set('dm-ram-total', m.ram_total);
      DM.set('dm-ram-usado', m.ram_usado);
      DM.set('dm-ram-libre', m.ram_libre);
      DM.set('dm-ram-fuente', m.ram_fuente);
      DM.bar('dm-ram-bar', m.ram_sistema_pct);
      if(m.ram_sistema){
        var w=document.getElementById('dm-ram-sys-wrap'); if(w) w.style.display='block';
      }
      // Almacenamiento
      DM.set('dm-db-size', m.db_size);
      DM.set('dm-db-path', m.db_path);
      DM.set('dm-db-indexes', m.db_indexes);
      DM.set('dm-disco-pct', m.disco_pct);
      DM.set('dm-disco-total', m.disco_total);
      DM.set('dm-disco-usado', m.disco_usado);
      DM.set('dm-disco-libre', m.disco_libre);
      DM.bar('dm-disco-bar', m.disco_pct_num);
      // Inventario
      DM.set('dm-inv-total', m.inv_total);
      DM.set('dm-inv-unidades', m.inv_unidades);
      DM.set('dm-inv-sin-stock', m.inv_sin_stock);
      DM.set('dm-inv-sin-precio', m.inv_sin_precio);
      DM.set('dm-inv-invalidos', m.inv_invalidos);
      DM.set('dm-inv-valor-venta', m.inv_valor_venta);
      DM.set('dm-inv-valor-costo', m.inv_valor_costo);
      DM.set('dm-inv-ganancia', m.inv_ganancia);
      DM.set('dm-inv-margen-pct', m.inv_margen);
      DM.set('dm-inv-rentabilidad', m.inv_rentabilidad);
      DM.set('dm-inv-cobertura', m.inv_cobertura);
      // Categorias
      var ce = document.getElementById('dm-inv-categorias');
      if(ce && m.categorias){
        var h='';
        m.categorias.forEach(function(c){
          h+='<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px"><span>'+c.nombre+'</span><span style="font-weight:600;color:#00cec9">'+c.count+'</span></div>';
        });
        ce.innerHTML=h;
      }
      // Top 5
      var t5 = document.getElementById('dm-inv-top5');
      if(t5 && m.top5){
        var h2='';
        m.top5.forEach(function(p,i){
          h2+='<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px"><span>'+(i+1)+'. '+p.nombre+'</span><span style="font-weight:600;color:#00cec9">$'+p.valor+'</span></div>';
        });
        t5.innerHTML=h2;
      }
      // Uptime
      DM.set('dm-uptime', m.uptime);
            // Tablas BD
      var tb = document.getElementById('dm-tablas');
      var tbRes = document.getElementById('dm-tablas-resumen');
      if(tb && m.tablas){
        var total = 0;
        var html = '<div class="row g-1">';
        for(var t in m.tablas){
          var cnt = m.tablas[t];
          total += cnt;
          var bg = cnt > 0 ? 'bg-success' : 'bg-secondary';
          html += '<div class="col-6 col-md-4 col-lg-3"><div class="d-flex justify-content-between p-1" style="font-size:11px"><span class="text-truncate" title="'+t+'">'+t+'</span><span class="badge '+bg+'">'+cnt+'</span></div></div>';
        }
        html += '</div>';
        tb.innerHTML = html;
        if(tbRes) tbRes.textContent = total + ' tablas';
      }
      DM.set('dm-timestamp', m.timestamp);
    }).catch(function(e){
      if(s) s.textContent='Error de conexion';
    });
  },
  set: function(id, val) {
    var el = document.getElementById(id);
    if(el && val !== undefined && val !== null) el.textContent = val;
  },
  bar: function(id, pct) {
    var el = document.getElementById(id);
    if(el && pct !== undefined) el.style.width = Math.min(100, Math.max(0, pct))+'%';
  }
};
// Auto-cargar al activar tab
document.addEventListener('DOMContentLoaded', function(){
  var tab = document.getElementById('dev-metrics-tab');
  if(tab) tab.addEventListener('shown.bs.tab', function(){ DM.fetch(); });
  setTimeout(DM.fetch, 1500);
});
