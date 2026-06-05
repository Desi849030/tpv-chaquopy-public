// tpv_dev_metrics.js v3 — Panel métricas del desarrollador
// FIX: Creado/actualizado automáticamente por fix_frontend_real.sh
(function() {
  "use strict";
  var DM = {
    endpoint: "/api/dev/metrics",
    intervalId: null,

    el: function(id) {
      return document.getElementById(id);
    },

    fmt: function(n) {
      if (n === null || n === undefined) return "--";
      return new Intl.NumberFormat("es", {minimumFractionDigits: 2}).format(n);
    },

    _set: function(id, val) {
      var e = this.el(id);
      if (e) e.textContent = (val !== null && val !== undefined) ? String(val) : "--";
    },

    init: function() {
      this.fetch();
      var self = this;
      this.intervalId = setInterval(function() { self.fetch(); }, 30000);
    },

    fetch: function() {
      var self = this;
      var se = this.el("dm-status");
      if (se) se.textContent = "cargando...";
      fetch(this.endpoint, {cache: "no-store", credentials: "same-origin"}).then(function(r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function(d) {
        if (!d.ok) throw new Error(d.error || "Error del servidor");
        self.render(d);
        if (se) se.textContent = "actualizado";
      }).catch(function(e) {
        if (se) se.textContent = "error: " + e.message;
      });
    },

    render: function(d) {
      this.renderResumen(d);
      this.renderRam(d.ram);
      this.renderStorage(d.storage);
      this.renderInventario(d.inventario);
      this.renderCategorias(d.inventario);
      this.renderTop5(d.inventario);
      this.renderFooter(d);
    },

    renderResumen: function(d) {
      if (d.resumen) {
        this._set("dm-resumen-productos", d.resumen.total_productos || 0);
        this._set("dm-resumen-ventas-hoy", d.resumen.ventas_hoy || 0);
        this._set("dm-resumen-ingresos", this.fmt(d.resumen.ingresos_hoy) + " CUP");
      }
    },

    renderRam: function(r) {
      if (!r) return;
      this._set("dm-ram-proceso", r.proceso_mb > 0 ? r.proceso_mb + " MB" : "--");
      this._set("dm-ram-fuente", "fuente: " + (r.fuente || "desconocido"));
      if (r.sistema_total_mb > 0) {
        var w = this.el("dm-ram-sys-wrap");
        if (w) w.style.display = "block";
        this._set("dm-ram-sys-pct", (r.sistema_pct || 0) + "%");
        var b = this.el("dm-ram-bar");
        if (b) b.style.width = (r.sistema_pct || 0) + "%";
        this._set("dm-ram-total", r.sistema_total_mb + " MB");
        this._set("dm-ram-usado", r.sistema_usado_mb + " MB");
        this._set("dm-ram-libre", r.sistema_libre_mb + " MB");
      }
    },

    renderStorage: function(s) {
      if (!s) return;
      this._set("dm-db-size", s.db_size_kb > 0 ? s.db_size_kb + " KB" : "--");
      this._set("dm-db-path", s.db_path || "--");
      this._set("dm-db-indexes", (s.num_indexes || 0) + " índices");
      var p = s.disco_pct || 0;
      this._set("dm-disco-pct", p + "%");
      var b = this.el("dm-disco-bar");
      if (b) b.style.width = p + "%";
      if (s.disco_total_mb > 0) {
        this._set("dm-disco-total", s.disco_total_mb + " MB");
        this._set("dm-disco-usado", s.disco_usado_mb + " MB");
        this._set("dm-disco-libre", s.disco_libre_mb + " MB");
      }
    },

    renderInventario: function(inv) {
      if (!inv) return;
      this._set("dm-inv-total", inv.total_productos);
      this._set("dm-inv-unidades", inv.total_unidades);
      this._set("dm-inv-sin-stock", inv.productos_sin_stock);
      this._set("dm-inv-valor-venta", this.fmt(inv.valor_venta_total) + " CUP");
      this._set("dm-inv-valor-costo", this.fmt(inv.valor_costo_total) + " CUP");
      this._set("dm-inv-ganancia", this.fmt(inv.ganancia_potencial) + " CUP");
      this._set("dm-inv-margen-pct", (inv.margen_bruto_pct || 0) + "%");
    },

    renderCategorias: function(inv) {
      if (!inv || !inv.categorias || !inv.categorias.length) return;
      var el = this.el("dm-inv-categorias");
      if (!el) return;
      var html = "";
      for (var i = 0; i < inv.categorias.length; i++) {
        var c = inv.categorias[i];
        html += '<div style="font-size:11px;padding:2px 0;display:flex;justify-content:space-between">';
        html += '<span>' + (c.nombre || "General") + ':</span>';
        html += '<span style="color:#00cec9">' + c.productos + ' prod | ' + this.fmt(c.valor) + ' CUP</span>';
        html += '</div>';
      }
      el.innerHTML = html;
    },

    renderTop5: function(inv) {
      if (!inv || !inv.top5_valor || !inv.top5_valor.length) return;
      var el = this.el("dm-inv-top5");
      if (!el) return;
      var html = "";
      for (var i = 0; i < inv.top5_valor.length; i++) {
        var p = inv.top5_valor[i];
        html += '<div style="font-size:11px;padding:2px 0;display:flex;justify-content:space-between">';
        html += '<span>#' + (i + 1) + ' ' + (p.nombre || "--") + ':</span>';
        html += '<span style="color:#00cec9">' + this.fmt(p.valor_total) + ' CUP</span>';
        html += '</div>';
      }
      el.innerHTML = html;
    },

    renderFooter: function(d) {
      if (d.uptime_s) {
        this._set("dm-uptime", Math.floor(d.uptime_s / 60) + "m " + (d.uptime_s % 60) + "s");
      }
      this._set("dm-timestamp", d.timestamp || "--");
    }
  };

  // Auto-init cuando el tab se hace visible o al cargar
  function initWhenReady() {
    var pane = document.getElementById("dev-metrics-tab-pane");
    if (pane && pane.classList.contains("active")) {
      DM.init();
      return;
    }
    // Observar cuando el tab se active
    var observer = new MutationObserver(function(mutations) {
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].target.classList.contains("active") ||
            mutations[i].target.classList.contains("show")) {
          DM.init();
          observer.disconnect();
          return;
        }
      }
    });
    if (pane) {
      observer.observe(pane, {attributes: true, attributeFilter: ["class"]});
    }
    // Fallback: init después de 3 segundos
    setTimeout(function() { DM.init(); }, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWhenReady);
  } else {
    initWhenReady();
  }

  // Exportar para uso externo
  window.DM = DM;
})();
