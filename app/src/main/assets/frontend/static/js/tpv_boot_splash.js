// tpv_boot_splash.js v6 — Splash con timeout GARANTIZADO
(function() {
    'use strict';

    // Crear overlay INMEDIATAMENTE (antes de cualquier otra cosa)
    var style = document.createElement('style');
    style.textContent = [
        '@keyframes tpvSpin {from{transform:rotate(0deg)}to{transform:rotate(360deg)}}',
        '@keyframes tpvPulse {0%,100%{opacity:1}50%{opacity:.5}}',
        '#tpv-boot-splash{position:fixed;inset:0;z-index:99999;',
        '  background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0;',
        '  font-family:system-ui,sans-serif;display:flex;flex-direction:column;',
        '  align-items:center;justify-content:center;padding:20px;text-align:center;',
        '  transition:opacity .4s ease}',
        '#tpv-boot-splash .logo{font-size:3.5rem;margin-bottom:16px;animation:tpvPulse 1.5s infinite}',
        '#tpv-boot-splash .title{font-size:1.5rem;font-weight:700;margin-bottom:8px;',
        '  background:linear-gradient(135deg,#60a5fa,#06b6d4);-webkit-background-clip:text;',
        '  -webkit-text-fill-color:transparent;background-clip:text}',
        '#tpv-boot-splash .status{font-size:.8rem;color:#94a3b8;margin-bottom:20px}',
        '#tpv-boot-splash .spinner{width:32px;height:32px;border:3px solid rgba(255,255,255,.1);',
        '  border-top-color:#06b6d4;border-radius:50%;animation:tpvSpin .8s linear infinite}',
        '#tpv-boot-splash .progress{width:240px;max-width:80vw;height:4px;',
        '  background:rgba(255,255,255,.08);border-radius:999px;overflow:hidden;margin-top:16px}',
        '#tpv-boot-splash .progress-fill{height:100%;width:0%;',
        '  background:linear-gradient(90deg,#4f46e5,#06b6d4);transition:width .3s ease}',
        '#tpv-boot-splash .pct{font-size:.7rem;color:#64748b;margin-top:8px}',
        '#tpv-boot-splash .error{color:#f87171;font-size:.75rem;margin-top:16px;',
        '  max-width:300px;display:none}',
        '#tpv-boot-splash .retry{margin-top:16px;padding:8px 20px;',
        '  background:#4f46e5;color:#fff;border:none;border-radius:8px;cursor:pointer;',
        '  font-size:.85rem;display:none}'
    ].join('');
    (document.head || document.documentElement).appendChild(style);

    var overlay = document.createElement('div');
    overlay.id = 'tpv-boot-splash';
    overlay.innerHTML =
        '<div class="logo">🚀</div>' +
        '<div class="title">TPV Ultra Smart</div>' +
        '<div class="status" id="tpv-splash-status">Inicializando sistema...</div>' +
        '<div class="spinner"></div>' +
        '<div class="progress"><div class="progress-fill" id="tpv-splash-progress"></div></div>' +
        '<div class="pct" id="tpv-splash-pct">0%</div>' +
        '<div class="error" id="tpv-splash-error"></div>' +
        '<button class="retry" id="tpv-splash-retry" onclick="location.reload()">Reintentar</button>';
    (document.body || document.documentElement).appendChild(overlay);

    var statusEl = document.getElementById('tpv-splash-status');
    var progressEl = document.getElementById('tpv-splash-progress');
    var pctEl = document.getElementById('tpv-splash-pct');
    var errorEl = document.getElementById('tpv-splash-error');
    var retryEl = document.getElementById('tpv-splash-retry');

    var STEPS = [
        'Inicializando núcleo...',
        'Cargando persistencia...',
        'Verificando seguridad...',
        'Conectando backend...',
        'Cargando catálogo...',
        'Preparando interfaz...',
        'Listo'
    ];
    var step = 0;

    function updateProgress() {
        if (step >= STEPS.length) return;
        statusEl.textContent = STEPS[step];
        var pct = Math.round(((step + 1) / STEPS.length) * 100);
        progressEl.style.width = pct + '%';
        pctEl.textContent = pct + '%';
        step++;
    }

    // Avanzar cada 400ms
    var interval = setInterval(updateProgress, 400);

    // Función para quitar el splash
    function hideSplash() {
        clearInterval(interval);
        var ol = document.getElementById('tpv-boot-splash');
        if (ol) {
            ol.style.opacity = '0';
            setTimeout(function() {
                if (ol.parentNode) ol.parentNode.removeChild(ol);
            }, 400);
        }
    }

    // Función para mostrar error
    function showError(msg) {
        clearInterval(interval);
        if (statusEl) statusEl.textContent = 'Error al cargar';
        if (errorEl) {
            errorEl.textContent = msg;
            errorEl.style.display = 'block';
        }
        if (retryEl) retryEl.style.display = 'block';
    }

    // Exponer globalmente para que el login lo llame
    window.tpvHideSplash = hideSplash;
    window.tpvShowSplashError = showError;

    // TIMEOUT GARANTIZADO: si después de 5s no se quitó, forzar quitar
    setTimeout(function() {
        var ol = document.getElementById('tpv-boot-splash');
        if (ol && ol.style.display !== 'none') {
            console.log('[SPLASH] Timeout 5s — forzando cierre');
            hideSplash();
        }
    }, 5000);

    // Detectar si el login aparece → quitar splash inmediatamente
    function checkLoginVisible() {
        var loginInputs = document.querySelectorAll('input[type=text], input[placeholder*=Usuario i], input[placeholder*=usuario i]');
        var loginButtons = document.querySelectorAll('button');
        var hasLogin = false;
        for (var i = 0; i < loginInputs.length; i++) {
            if (loginInputs[i].offsetParent !== null) { hasLogin = true; break; }
        }
        if (!hasLogin) {
            for (var i = 0; i < loginButtons.length; i++) {
                var txt = (loginButtons[i].textContent || '').toLowerCase();
                if (txt.indexOf('entrar') !== -1 || txt.indexOf('login') !== -1) {
                    if (loginButtons[i].offsetParent !== null) { hasLogin = true; break; }
                }
            }
        }
        if (hasLogin) {
            console.log('[SPLASH] Login detectado — cerrando splash');
            hideSplash();
            return true;
        }
        return false;
    }

    // Verificar cada 500ms si el login ya aparece
    var checkInterval = setInterval(function() {
        if (checkLoginVisible()) {
            clearInterval(checkInterval);
        }
    }, 500);

    // Detener el check después de 10s (no seguir para siempre)
    setTimeout(function() { clearInterval(checkInterval); }, 10000);

    // Si hay error JS, mostrarlo en el splash
    window.onerror = function(msg, url, line, col, err) {
        console.error('[SPLASH] JS Error:', msg, 'at', line + ':' + col);
        // Solo mostrar error si el splash sigue visible después de 3s
        setTimeout(function() {
            var ol = document.getElementById('tpv-boot-splash');
            if (ol && ol.style.display !== 'none' && ol.style.opacity !== '0') {
                showError('Error JS: ' + msg + ' (línea ' + line + ')');
            }
        }, 3000);
        return false;
    };

    console.log('[SPLASH] Splash v6 iniciado');
})();
