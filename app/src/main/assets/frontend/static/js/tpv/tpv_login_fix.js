// v5 FIX: solo activar login existente
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var ls = document.getElementById('login-screen');
        if (ls) { ls.style.display = 'flex'; ls.style.opacity = '1'; }
        else { console.warn('[login-fix] esperando auth_setup...'); }
    }, 600);
});