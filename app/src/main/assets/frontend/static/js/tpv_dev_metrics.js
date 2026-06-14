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

    // Muestra MB o GB según magnitud.
    mb: function(v) {
      v = Number(v) || 0;
      if (v >= 1024) return (v / 1024).toFixed(2) + " GB";
      return v.toFixed(0) + " MB";
    },

    render: function(d) {
      this.renderResumen(d);
      this.renderRam(d.ram);
      this.renderStorage(d.storage);
      this.renderTablas(d.tablas);
      this.renderFooter(d);
    },

    renderTablas: function(t) {
      var el = this.el("dm-tablas");
      if (!el) return;
      if (!t || !t.tablas || !t.tablas.length) {
        el.innerHTML = '<div class="text-muted small">Sin tablas</div>';
        return;
      }
      var resumen = this.el("dm-tablas-resumen");
      if (resumen) resumen.textContent = t.total_tablas + " tablas · " + t.total_filas + " filas";
      var html = '<div class="row g-1">';
      for (var i = 0; i < t.tablas.length; i++) {
        var row = t.tablas[i];
        var color = row.filas > 0 ? "text-info fw-bold" : "text-muted";
        html += '<div class="col-6 col-md-4 d-flex justify-content-between border-bottom py-1" style="font-size:12px">' +
                '<span class="text-truncate me-1">' + row.nombre + '</span>' +
                '<span class="' + color + '">' + (row.filas < 0 ? "?" : row.filas) + '</span></div>';
      }
      html += '</div>';
      el.innerHTML = html;
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
        this._set("dm-ram-total", this.mb(r.sistema_total_mb));
        this._set("dm-ram-usado", this.mb(r.sistema_usado_mb));
        this._set("dm-ram-libre", this.mb(r.sistema_libre_mb));
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
        this._set("dm-disco-total", this.mb(s.disco_total_mb));
        this._set("dm-disco-usado", this.mb(s.disco_usado_mb));
        this._set("dm-disco-libre", this.mb(s.disco_libre_mb));
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

  // Solo inicializa cuando el tab está visible (evita 403 al pedir métricas
  // sin estar logueado o sin abrir la pestaña).
  function initWhenReady() {
    var pane = document.getElementById("dev-metrics-tab-pane");
    if (!pane) return;
    if (pane.classList.contains("active")) {
      DM.init();
      return;
    }
    // Observar cuando el tab se active (no usar fallback por tiempo).
    var observer = new MutationObserver(function() {
      if (pane.classList.contains("active") || pane.classList.contains("show")) {
        DM.init();
      } else if (DM.intervalId) {
        // Detener el polling cuando se sale de la pestaña.
        clearInterval(DM.intervalId);
        DM.intervalId = null;
      }
    });
    observer.observe(pane, {attributes: true, attributeFilter: ["class"]});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWhenReady);
  } else {
    initWhenReady();
  }

  // Exportar para uso externo
  window.DM = DM;
})();


// Alias global para el botón onclick="devmetrics_cargar()"
window.devmetrics_cargar = function() {
    if (typeof DM !== 'undefined' && DM.fetch) {
        DM.fetch();
    }
};
