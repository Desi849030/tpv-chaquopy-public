// tpv_boot_splash.js v5 — Splash profesional con SVG + mesh gradient
(function() {
    'use strict';

    const STEPS = [
        { id: 'kernel',     label: 'Núcleo Chaquopy',          desc: 'Máquina virtual Python' },
        { id: 'storage',    label: 'SQLite WAL',                desc: 'Persistencia atómica local' },
        { id: 'crypto',     label: 'Capa Criptográfica',        desc: 'scrypt + HMAC-SHA256' },
        { id: 'network',    label: 'Túnel Supabase',            desc: 'Sincronización opcional' },
        { id: 'blueprints', label: 'Módulos Flask (28)',        desc: 'Arquitectura DDD modular' },
        { id: 'ai_engine',  label: 'Motor ReAct IA',            desc: 'Orquestación de herramientas' },
        { id: 'guardrails', label: 'Anti SQL-Injection',        desc: 'Rate limiter + PII mask' },
        { id: 'webview',    label: 'Frontend PWA',              desc: 'Offline-first con Service Worker' },
        { id: 'biometrics', label: 'BiometricPrompt',           desc: 'AndroidX Biometric' },
        { id: 'pos_core',   label: 'DAOs Ventas + Inventario',  desc: 'Atomicidad v10 + idempotencia' }
    ];

    const style = document.createElement('style');
    style.textContent = `
        @keyframes tpvMesh {
            0%,100% { background-position: 0% 50%, 100% 50%, 50% 0%, 50% 100%; }
            25%     { background-position: 100% 50%, 0% 50%, 50% 100%, 50% 0%; }
            50%     { background-position: 100% 100%, 0% 0%, 0% 50%, 100% 50%; }
            75%     { background-position: 0% 100%, 100% 0%, 100% 50%, 0% 50%; }
        }
        @keyframes tpvLogoFloat {
            0%,100% { transform: translateY(0) rotate(0deg); }
            50%     { transform: translateY(-8px) rotate(3deg); }
        }
        @keyframes tpvRing {
            0%   { transform: rotate(0deg); opacity: 0.7; }
            100% { transform: rotate(360deg); opacity: 0.3; }
        }
        @keyframes tpvSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes tpvShimmer {
            0%   { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        @keyframes tpvFadeOut {
            from { opacity: 1; transform: scale(1); }
            to   { opacity: 0; transform: scale(1.03); }
        }
        @keyframes tpvPulse {
            0%,100% { opacity: 0.5; }
            50%     { opacity: 1; }
        }
        #tpv-boot-splash {
            position: fixed; inset: 0; z-index: 99999;
            background:
                radial-gradient(circle at 20% 30%, rgba(79,70,229,0.35) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(6,182,212,0.3) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(139,92,246,0.2) 0%, transparent 70%),
                linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%);
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 24px; text-align: center;
            transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }
        #tpv-boot-splash .logo-wrap {
            position: relative;
            width: 120px; height: 120px;
            display: flex; align-items: center; justify-content: center;
            margin-bottom: 28px;
            animation: tpvLogoFloat 3s ease-in-out infinite;
        }
        #tpv-boot-splash .logo-ring {
            position: absolute; inset: 0;
            border-radius: 50%;
            border: 3px solid transparent;
            border-top-color: #4f46e5;
            border-right-color: #06b6d4;
            animation: tpvRing 2s linear infinite;
        }
        #tpv-boot-splash .logo-ring:nth-child(2) {
            inset: 8px;
            border-top-color: #06b6d4;
            border-right-color: #a78bfa;
            animation-duration: 1.5s;
            animation-direction: reverse;
        }
        #tpv-boot-splash .logo-inner {
            width: 80px; height: 80px; border-radius: 24px;
            background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
            display: flex; align-items: center; justify-content: center;
            font-size: 2.4rem;
            box-shadow: 0 16px 40px rgba(79, 70, 229, 0.6);
            position: relative;
            z-index: 1;
        }
        #tpv-boot-splash .title {
            font-size: 1.9rem; font-weight: 800; margin-bottom: 4px;
            background: linear-gradient(135deg, #60a5fa 0%, #06b6d4 50%, #a78bfa 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }
        #tpv-boot-splash .subtitle {
            font-size: 0.78rem; color: #64748b; margin-bottom: 28px;
            font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase;
        }
        #tpv-boot-splash .progress-container {
            width: 340px; max-width: 85vw; margin-bottom: 24px;
        }
        #tpv-boot-splash .progress-bar {
            height: 5px; background: rgba(255,255,255,0.06);
            border-radius: 999px; overflow: hidden; position: relative;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.4);
        }
        #tpv-boot-splash .progress-fill {
            height: 100%; width: 0%;
            background: linear-gradient(90deg, #4f46e5 0%, #06b6d4 50%, #a78bfa 100%);
            background-size: 200% 100%;
            border-radius: 999px;
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            box-shadow: 0 0 16px rgba(79, 70, 229, 0.8);
        }
        #tpv-boot-splash .progress-fill::after {
            content: ''; position: absolute; inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent);
            background-size: 200% 100%;
            animation: tpvShimmer 1.5s linear infinite;
        }
        #tpv-boot-splash .progress-text {
            display: flex; justify-content: space-between;
            margin-top: 10px; font-size: 0.7rem; color: #64748b;
            font-variant-numeric: tabular-nums; font-weight: 600;
            letter-spacing: 0.05em;
        }
        #tpv-boot-splash .steps {
            width: 360px; max-width: 92vw;
            display: flex; flex-direction: column; gap: 3px;
        }
        #tpv-boot-splash .step {
            display: flex; align-items: center; gap: 14px;
            padding: 9px 14px;
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 12px;
            font-size: 0.78rem;
            opacity: 0.25;
            transition: all 0.3s ease;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
        #tpv-boot-splash .step.active {
            opacity: 1;
            background: rgba(79, 70, 229, 0.18);
            border-color: rgba(79, 70, 229, 0.5);
            transform: translateX(6px);
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.25);
        }
        #tpv-boot-splash .step.done {
            opacity: 0.65;
            background: rgba(74, 222, 128, 0.05);
            border-color: rgba(74, 222, 128, 0.12);
        }
        #tpv-boot-splash .step .step-num {
            width: 24px; height: 24px; border-radius: 50%;
            background: rgba(255,255,255,0.06);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.68rem; font-weight: 700; color: #64748b;
            flex-shrink: 0; transition: all .3s;
        }
        #tpv-boot-splash .step.active .step-num {
            background: linear-gradient(135deg, #4f46e5, #06b6d4);
            color: #fff;
        }
        #tpv-boot-splash .step.done .step-num {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }
        #tpv-boot-splash .step .label-wrap { flex: 1; text-align: left; }
        #tpv-boot-splash .step .label { font-weight: 600; font-size: 0.82rem; }
        #tpv-boot-splash .step .desc {
            font-size: 0.66rem; color: #64748b; margin-top: 1px;
            font-weight: 400;
        }
        #tpv-boot-splash .step .status {
            font-size: 0.95rem; width: 20px; text-align: center; flex-shrink: 0;
        }
        #tpv-boot-splash .step.done .status { color: #4ade80; }
        #tpv-boot-splash .step.active .status {
            color: #fbbf24;
            display: inline-block;
            animation: tpvSpin 0.8s linear infinite;
        }
        #tpv-boot-splash .footer {
            margin-top: 24px; font-size: 0.65rem; color: #475569;
            letter-spacing: 0.15em; text-transform: uppercase;
            animation: tpvPulse 2.5s ease infinite;
            font-weight: 500;
        }
        #tpv-boot-splash .version-tag {
            margin-top: 8px; font-size: 0.6rem; color: #334155;
            font-variant-numeric: tabular-nums;
        }
    `;
    document.head.appendChild(style);

    const overlay = document.createElement('div');
    overlay.id = 'tpv-boot-splash';
    overlay.innerHTML = `
        <div class="logo-wrap">
            <div class="logo-ring"></div>
            <div class="logo-ring"></div>
            <div class="logo-inner">🚀</div>
        </div>
        <div class="title">TPV Ultra Smart</div>
        <div class="subtitle">Sistema de Punto de Venta Híbrido</div>
        <div class="progress-container">
            <div class="progress-bar"><div class="progress-fill" id="tpv-boot-progress"></div></div>
            <div class="progress-text">
                <span id="tpv-boot-step-name">Inicializando...</span>
                <span id="tpv-boot-percentage">0%</span>
            </div>
        </div>
        <div class="steps" id="tpv-boot-steps"></div>
        <div class="footer">Enterprise · Offline-First · AI-Powered</div>
        <div class="version-tag">v8.0 Rev. 14 · Chaquopy + Flask + ReAct IA</div>
    `;
    document.body.appendChild(overlay);

    const stepsEl = document.getElementById('tpv-boot-steps');
    STEPS.forEach((s, i) => {
        const row = document.createElement('div');
        row.className = 'step';
        row.id = 'boot-' + s.id;
        row.innerHTML =
            '<div class="step-num">' + (i+1).toString().padStart(2,'0') + '</div>' +
            '<div class="label-wrap">' +
                '<div class="label">' + s.label + '</div>' +
                '<div class="desc">' + s.desc + '</div>' +
            '</div>' +
            '<span class="status">⏳</span>';
        stepsEl.appendChild(row);
    });

    const progressEl = document.getElementById('tpv-boot-progress');
    const percentEl = document.getElementById('tpv-boot-percentage');
    const stepNameEl = document.getElementById('tpv-boot-step-name');
    let current = 0;

    function next() {
        if (current > 0) {
            const prev = document.getElementById('boot-' + STEPS[current-1].id);
            if (prev) {
                prev.classList.remove('active');
                prev.classList.add('done');
                prev.querySelector('.status').textContent = '✓';
            }
        }
        if (current >= STEPS.length) {
            stepNameEl.textContent = 'Sistema listo';
            setTimeout(() => {
                overlay.style.animation = 'tpvFadeOut 0.5s forwards';
                setTimeout(() => overlay.remove(), 500);
            }, 400);
            return;
        }
        const step = STEPS[current];
        const cur = document.getElementById('boot-' + step.id);
        if (cur) {
            cur.classList.add('active');
            cur.querySelector('.status').textContent = '⟳';
        }
        stepNameEl.textContent = step.label;
        const pct = Math.round(((current + 1) / STEPS.length) * 100);
        progressEl.style.width = pct + '%';
        percentEl.textContent = pct + '%';
        current++;
        setTimeout(next, 220 + Math.random() * 150);
    }
    setTimeout(next, 250);
    console.log('[BOOT] Splash v5 profesional iniciado');
})();
