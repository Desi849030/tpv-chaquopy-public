// tpv_pwa_register.js — Registro de Service Worker para PWA offline
    navigator.serviceWorker.register('/service-worker.js')
        .then(function() { console.log('PWA lista'); })
        .catch(function(e) { console.warn('SW no soportado:', e); });
}
