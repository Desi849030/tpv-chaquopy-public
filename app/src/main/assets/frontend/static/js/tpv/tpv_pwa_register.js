if ('serviceWorker' in navigator && navigator.serviceWorker) {
    navigator.serviceWorker.register('/service-worker.js')
        .then(function() { console.log('PWA lista'); })
        .catch(function(e) { console.warn('SW no soportado:', e); });
}
