// tpv_splash_init.js — Splash de inicialización visible
(function() {
    'use strict';

    var style = document.createElement('style');
    style.textContent = [
        '@keyframes tpvSpin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}',
        '@keyframes tpvPulse{0%,100%{opacity:1}50%{opacity:.6}}',
        '#tpv-init-splash{position:fixed;inset:0;z-index:99999;',
        '  background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0;',
        '  font-family:system-ui,sans-serif;display:flex;flex-direction:column;',
        '  align-items:center;justify-content:center;padding:20px;text-align:center;',
        '  transition:opacity .4s ease}',
        '#tpv-init-splash .logo{font-size:3rem;margin-bottom:16px;animation:tpvPulse 1.5s infinite}',
        '#tpv-init-splash .title{font-size:1.4rem;font-weight:700;margin-bottom:4px;',
        '  background:linear-gradient(135deg,#60a5fa,#06b6d4);-webkit-background-clip:text;',
        '  -webkit-text-fill-color:transparent;background-clip:text}',
        '#tpv-init-splash .sub{font-size:.75rem;color:#64748b;margin-bottom:20px}',
        '#tpv-init-splash .spinner{width:32px;height:32px;border:3px solid rgba(255,255,255,.1);',
        '  border-top-color:#06b6d4;border-radius:50%;animation:tpvSpin .8s linear infinite;margin-bottom:16px}',
        '#tpv-init-splash .bar{width:240px;max-width:80vw;height:4px;',
        '  background:rgba(255,255,255,.08);border-radius:999px;overflow:hidden}',
        '#tpv-init-splash .fill{height:100%;width:0%;',
        '  background:linear-gradient(90deg,#4f46e5,#06b6d4);transition:width .3s ease}',
        '#tpv-init-splash .pct{font-size:.7rem;color:#64748b;margin-top:8px}',
        '#tpv-init-splash .steps{margin-top:16px;font-size:.65rem;color:#475569;max-width:280px}'
    ].join('');
    (document.head || document.documentElement).appendChild(style);

    var ol = document.createElement('div');
    ol.id = 'tpv-init-splash';
    ol.innerHTML =
        '<div class="logo">🚀</div>' +
        '<div class="title">TPV Ultra Smart</div>' +
        '<div class="sub">Inicializando sistema...</div>' +
        '<div class="spinner"></div>' +
        '<div class="bar"><div class="fill" id="tpv-init-fill"></div></div>' +
        '<div class="pct" id="tpv-init-pct">0%</div>' +
        '<div class="steps" id="tpv-init-steps"></div>';
    (document.body || document.documentElement).appendChild(ol);

    var fill = document.getElementById('tpv-init-fill');
    var pct = document.getElementById('tpv-init-pct');
    var stepsEl = document.getElementById('tpv-init-steps');

    var STEPS = [
        'Núcleo Chaquopy',
        'SQLite WAL',
        'Capa Criptográfica',
        'Módulos Flask (28)',
        'Motor ReAct IA',
        'Guardrails Seguridad',
        'Frontend PWA',
        'BiometricPrompt',
        'DAOs Ventas',
        'Sistema Listo'
    ];
    var i = 0;

    function next() {
        if (i >= STEPS.length) {
            stepsEl.textContent = '✓ ' + STEPS[STEPS.length-1];
            setTimeout(function() {
                ol.style.opacity = '0';
                setTimeout(function() { if (ol.parentNode) ol.parentNode.removeChild(ol); }, 400);
            }, 300);
            return;
        }
        stepsEl.textContent = (i > 0 ? '✓ ' : '') + STEPS[i-1 < 0 ? 0 : i-1] + ' → ' + STEPS[i];
        var p = Math.round(((i + 1) / STEPS.length) * 100);
        fill.style.width = p + '%';
        pct.textContent = p + '%';
        i++;
        setTimeout(next, 250);
    }

    // Detectar login visible → quitar splash inmediatamente
    var checkLogin = setInterval(function() {
        var inputs = document.querySelectorAll('input[type=text], input[placeholder]');
        for (var j = 0; j < inputs.length; j++) {
            if (inputs[j].offsetParent !== null && inputs[j].offsetWidth > 0) {
                clearInterval(checkLogin);
                ol.style.opacity = '0';
                setTimeout(function() { if (ol.parentNode) ol.parentNode.removeChild(ol); }, 400);
                return;
            }
        }
    }, 500);

    // Timeout garantizado: 6s máximo
    setTimeout(function() {
        if (ol.parentNode) {
            ol.style.opacity = '0';
            setTimeout(function() { if (ol.parentNode) ol.parentNode.removeChild(ol); }, 400);
        }
    }, 6000);

    setTimeout(next, 200);
})();
