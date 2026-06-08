// tpv_ping.js - Ping silencioso cada 6 segundos para detectar online/offline
// Reemplaza navigator.onLine events con ping real al servidor Flask
(function() {
    "use strict";
    var INTERVAL = 6000;
    var PING_URL = "/api/ping";
    var TIMEOUT = 3000;
    var _online = navigator.onLine;
    var _wasOffline = false;
    var _timer = null;
    var _count = 0;

    function _updateUI(online) {
        window._realOnline = online;
        var ind = document.getElementById("offline-indicator");
        var badge = document.getElementById("status-badge");
        var txt = document.getElementById("status-text");
        if (ind) ind.style.display = online ? "none" : "block";
        if (badge && txt) {
            var ico = badge.querySelector("i");
            badge.classList.toggle("bg-success", online);
            badge.classList.toggle("bg-danger", !online);
            badge.classList.toggle("offline", !online);
            if (ico) ico.className = online ? "bi bi-wifi" : "bi bi-wifi-off";
            txt.textContent = online ? "Online" : "Offline";
        }
        if (online && _wasOffline) {
            _wasOffline = false;
            console.log("[PING] Conexion restaurada (ping #" + _count + ")");
            if (typeof loadProducts === "function") {
                try { loadProducts(); } catch(e) {}
            }
            if (typeof conf_setLanguage === "function") {
                try { conf_setLanguage(window.tpvState && window.tpvState.config ? window.tpvState.config.lang : "es"); } catch(e) {}
            }
        } else if (!online && !_wasOffline) {
            _wasOffline = true;
            console.log("[PING] Sin conexion al servidor (ping #" + _count + ")");
        }
    }

    function ping() {
        _count++;
        try {
            var ctrl = new AbortController();
            var timer = setTimeout(function() { ctrl.abort(); }, TIMEOUT);
            fetch(PING_URL, { method: "HEAD", cache: "no-store", signal: ctrl.signal })
            .then(function(r) {
                clearTimeout(timer);
                _updateUI(r.ok);
            })
            .catch(function() {
                clearTimeout(timer);
                _updateUI(false);
            });
        } catch(e) {
            _updateUI(false);
        }
    }

    function start() {
        if (_timer) return;
        _updateUI(_online);
        ping();
        _timer = setInterval(ping, INTERVAL);
        console.log("[PING] Monitor iniciado (cada " + (INTERVAL/1000) + "s)");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }

    window.addEventListener("online", function() { ping(); });
    window.addEventListener("offline", function() { ping(); });

    window._tpvPing = { start: start, stop: function() { clearInterval(_timer); _timer = null; } };
})();
