// tpv_auth.js — Puente boot-loader → login
(function(){
    function revealLogin(){
        if(window._splashHide){
            try{ window._splashHide(); }catch(e){ console.warn('_splashHide error:',e); }
        }
    }
    var intentos = 0;
    var maxIntentos = 40;
    function check(){
        intentos++;
        var ls = document.getElementById('login-screen');
        if(ls){ revealLogin(); }
        else if(intentos < maxIntentos){ setTimeout(check, 100); }
        else { revealLogin(); }
    }
    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', function(){ setTimeout(check, 300); });
    } else { setTimeout(check, 300); }
})();
