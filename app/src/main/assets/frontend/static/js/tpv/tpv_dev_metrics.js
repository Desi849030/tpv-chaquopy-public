// tpv_dev_metrics.js - Panel de métricas del desarrollador
(function() {
  var DM = {
    endpoint: "/api/dev/metrics",
    intervalId: null,
    el: function(id) { return document.getElementById(id); },
    fmt: function(n) { return new Intl.NumberFormat("es", {minimumFractionDigits:2}).format(n); },
    
    init: function() {
      console.log('🔧 DM.init() ejecutado');
      this.fetch();
      this.intervalId = setInterval(function() { DM.fetch(); }, 10000);
    },
    
    fetch: function() {
      var statusEl = this.el("dm-status");
      if (statusEl) statusEl.textContent = "cargando...";
      
      fetch(this.endpoint, { cache: "no-store" })
        .then(function(res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          return res.json();
        })
        .then(function(data) {
          if (!data.ok) throw new Error(data.error || "Error");
          DM.render(data);
          if (statusEl) statusEl.textContent = "actualizado";
        })
        .catch(function(err) {
          console.error("Métricas error:", err);
          if (statusEl) statusEl.textContent = "error: " + err.message;
        });
    },
    
    render: function(d) {
      console.log('📊 DM.render() con datos:', d);
      this.renderRam(d.ram);
      this.renderStorage(d.storage);
      this.renderInventario(d.inventario);
      this.renderFooter(d);
    },
    
    renderRam: function(r) {
      if (!r) return;
      this.el("dm-ram-proceso").textContent = r.proceso_mb > 0 ? r.proceso_mb + " MB" : "--";
      this.el("dm-ram-fuente").textContent = "fuente: " + r.fuente;
      if (r.sistema_total_mb > 0) {
        this.el("dm-ram-sys-wrap").style.display = "block";
        var pct = r.sistema_pct || 0;
        this.el("dm-ram-sys-pct").textContent = pct + "%";
        this.el("dm-ram-bar").style.width = pct + "%";
        this.el("dm-ram-total").textContent = r.sistema_total_mb + " MB";
        this.el("dm-ram-usado").textContent = r.sistema_usado_mb + " MB";
        this.el("dm-ram-libre").textContent = r.sistema_libre_mb + " MB";
      }
    },
    
    renderStorage: function(s) {
      if (!s) return;
      this.el("dm-db-size").textContent = s.db_size_kb > 0 ? s.db_size_kb + " KB" : "--";
      this.el("dm-db-path").textContent = s.db_path || "--";
      var pct = s.disco_pct || 0;
      this.el("dm-disco-pct").textContent = pct + "%";
      this.el("dm-disco-bar").style.width = pct + "%";
      if (s.disco_total_mb > 0) {
        this.el("dm-disco-total").textContent = s.disco_total_mb + " MB";
        this.el("dm-disco-usado").textContent = s.disco_usado_mb + " MB";
        this.el("dm-disco-libre").textContent = s.disco_libre_mb + " MB";
      }
    },
    
    renderInventario: function(inv) {
      if (!inv) return;
      this.el("dm-inv-total").textContent = inv.total_productos;
      this.el("dm-inv-unidades").textContent = inv.total_unidades;
      this.el("dm-inv-sin-stock").textContent = inv.productos_sin_stock;
      this.el("dm-inv-sin-precio").textContent = inv.productos_sin_precio;
      this.el("dm-inv-invalidos").textContent = inv.productos_precio_invalido;
      this.el("dm-inv-valor-venta").textContent = this.fmt(inv.valor_venta_total) + " CUP";
      this.el("dm-inv-valor-costo").textContent = this.fmt(inv.valor_costo_total) + " CUP";
      this.el("dm-inv-ganancia").textContent = this.fmt(inv.ganancia_potencial) + " CUP";
      this.el("dm-inv-margen-pct").textContent = inv.margen_bruto_pct + "%";
      this.el("dm-inv-rentabilidad").textContent = inv.formula_rentabilidad || "N/A";
      this.el("dm-inv-cobertura").textContent = inv.formula_cobertura || "N/A";
    },
    
    renderFooter: function(d) {
      if (d.uptime_s) {
        this.el("dm-uptime").textContent = Math.floor(d.uptime_s / 60) + "m " + (d.uptime_s % 60) + "s";
      }
      this.el("dm-timestamp").textContent = d.timestamp || "--";
    }
  };
  
  // Iniciar cuando el DOM esté listo
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() { DM.init(); });
  } else {
    DM.init();
  }
})();
