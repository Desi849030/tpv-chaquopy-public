// Fix: Mostrar login screen inmediatamente al cargar
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var ls = document.getElementById('login-screen');
        if (ls) {
            ls.style.display = 'flex';
            ls.style.opacity = '1';
            console.log('✅ Login screen activado por fix');
        } else {
            console.log('❌ login-screen no encontrado, creando...');
            // Crear login básico de emergencia
            var div = document.createElement('div');
            div.id = 'login-screen';
            div.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#0a0e1a;display:flex;align-items:center;justify-content:center;z-index:9999';
            div.innerHTML = '<div style="text-align:center;color:white"><h2>TPV UltraSmart</h2><input id="login-username" placeholder="Usuario" style="margin:10px;padding:10px;border-radius:8px;border:none"><br><input id="login-password" type="password" placeholder="Contraseña" style="margin:10px;padding:10px;border-radius:8px;border:none"><br><button id="login-btn" onclick="auth_login()" style="padding:10px 40px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:16px">Entrar</button></div>';
            document.body.appendChild(div);
        }
    }, 500);
});
