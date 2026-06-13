document.addEventListener('keydown', function(e) {
    if (e.key === 'F1') { e.preventDefault(); document.getElementById('tpv-caja-tab')?.click(); }
    if (e.key === 'F2') { e.preventDefault(); document.getElementById('gestion-productos-tab')?.click(); }
    if (e.key === 'Escape') { if (typeof tpv_cancelarPedido === 'function') tpv_cancelarPedido(); }
});
window.tpv_haptic = (p=10) => { if ('vibrate' in navigator) navigator.vibrate(p); };
