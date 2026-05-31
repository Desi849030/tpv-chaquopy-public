// ==================== PUENTE: IndexedDB → API ====================
// Sobrescribe funciones del frontend para usar APIs reales

setTimeout(function() {
  
  // 1. Cerrar caja → llamar API real
  if (typeof caja_cerrarDia !== 'undefined') {
    var originalCerrar = caja_cerrarDia;
    window.caja_cerrarDia = async function() {
      var fecha = new Date().toISOString().split('T')[0];
      if (!confirm('¿Cerrar caja del ' + fecha + '?')) return;
      try {
        var res = await fetch('/api/ventas/cierre', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({fecha: fecha})
        });
        var d = await res.json();
        if (d.ok) {
          alert('✅ Caja cerrada\nTotal: $' + d.total_ventas.toFixed(2) + '\nTransacciones: ' + d.num_transacciones);
          location.reload();
        } else {
          originalCerrar(); // Fallback a la función original
        }
      } catch(e) { originalCerrar(); }
    };
    console.log('✅ caja_cerrarDia → API real');
  }
  
  // 2. Exportar → descargar CSV real
  if (typeof conf_handleExport !== 'undefined') {
    window.conf_handleExport = function() {
      window.open('/api/reportes/exportar?desde=2026-05-01&hasta=' + new Date().toISOString().split('T')[0], '_blank');
    };
    console.log('✅ conf_handleExport → CSV real');
  }
  
  // 3. Dashboard → datos reales de API
  if (typeof dashboard_cargar !== 'undefined') {
    var originalDashboard = dashboard_cargar;
    window.dashboard_cargar = async function() {
      try {
        var res = await fetch('/api/metrics');
        var d = await res.json();
        // Actualizar elementos del dashboard si existen
        var elVentas = document.getElementById('dashboard-total-sales');
        var elGanancia = document.getElementById('dashboard-total-profit');
        var elProd = document.getElementById('dashboard-total-products');
        if (elVentas) elVentas.textContent = '$' + (d.ingresos_hoy || 0).toFixed(2);
        if (elGanancia) elGanancia.textContent = '$' + (d.ganancia_hoy || 0).toFixed(2);
        if (elProd) elProd.textContent = d.productos || 0;
      } catch(e) {}
      originalDashboard(); // También ejecutar original
    };
    console.log('✅ dashboard_cargar → API real');
  }
  
  // 4. Backup → API real
  if (typeof crear_backup_manual !== 'undefined') {
    window.crear_backup_manual = async function() {
      try {
        var res = await fetch('/api/db/backup', {method:'POST'});
        var d = await res.json();
        alert(d.ok ? '✅ Backup creado: ' + d.backup : 'Error: ' + d.error);
      } catch(e) { alert('Error al crear backup'); }
    };
    console.log('✅ crear_backup_manual → API real');
  }
  
  console.log('🚀 Puente IndexedDB → API activo');
}, 3000);
