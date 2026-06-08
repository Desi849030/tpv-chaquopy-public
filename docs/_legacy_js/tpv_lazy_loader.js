// tpv_lazy_loader.js — Lazy load JS modules por tab
(function() {
    "use strict";
    var _loaded = {};
    var _tabMap = {
        "tienda-tab-pane": [
            "/static/js/tpv/tpv_tienda_init.js",
            "/static/js/tpv/tpv_tienda_carrito.js",
            "/static/js/tpv/tpv_tienda_pedidos.js",
            "/static/js/tpv/tpv_tienda_cliente.js"
        ],
        "dev-metrics-tab-pane": [
            "/static/js/tpv/tpv_dev_metrics.js"
        ],
        "privilegios-tab-pane": [
            "/static/js/tpv/tpv_gestion_usuarios.js"
        ],
        "seguridad-tab-pane": [
            "/static/js/tpv/tpv_debugger.js"
        ]
    };

    function loadScripts(urls, cb) {
        var pending = urls.length;
        if (pending === 0) { if (cb) cb(); return; }
        urls.forEach(function(url) {
            if (_loaded[url]) { pending--; if (pending === 0 && cb) cb(); return; }
            var s = document.createElement("script");
            s.src = url;
            s.onload = function() { _loaded[url] = true; pending--; if (pending === 0 && cb) cb(); };
            s.onerror = function() { console.warn("[LAZY] Error cargando: " + url); pending--; if (pending === 0 && cb) cb(); };
            document.body.appendChild(s);
        });
    }

    function init() {
        var tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabs.forEach(function(tab) {
            var target = tab.getAttribute("href") || tab.getAttribute("data-bs-target");
            if (!target) return;
            var paneId = target.replace("#", "");
            if (!_tabMap[paneId]) return;
            tab.addEventListener("shown.bs.tab", function() {
                loadScripts(_tabMap[paneId]);
            });
        });
        console.log("[LAZY] Tab lazy loader iniciado (" + Object.keys(_tabMap).length + " tabs registradas)");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
