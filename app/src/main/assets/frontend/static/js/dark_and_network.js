/* ========== v24: Dark Mode Toggle + Network Status ========== */
(function(){
  "use strict";

  /* ----- DARK MODE ----- */
  function initDarkMode(){
    var saved = localStorage.getItem('tpv-dark-mode');
    if(saved === 'true' || (!saved && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)){
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    var btn = document.createElement('button');
    btn.id = 'dark-mode-toggle';
    btn.title = 'Modo oscuro';
    btn.innerHTML = '\uD83C\uDF19';
    document.body.appendChild(btn);
    btn.addEventListener('click', function(){
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if(isDark){
        document.documentElement.removeAttribute('data-theme');
        btn.innerHTML = '\uD83C\uDF19';
        localStorage.setItem('tpv-dark-mode', 'false');
        if(window._toast) window._toast('Modo claro activado', 'info');
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        btn.innerHTML = '\u2600\uFE0F';
        localStorage.setItem('tpv-dark-mode', 'true');
        if(window._toast) window._toast('Modo oscuro activado', 'info');
      }
    });
    /* Actualizar icono al cargar */
    setTimeout(function(){
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      btn.innerHTML = isDark ? '\u2600\uFE0F' : '\uD83C\uDF19';
    }, 100);
  }

  /* ----- NETWORK STATUS ----- */
  function initNetworkStatus(){
    var badge = document.createElement('div');
    badge.id = 'tpv-network-badge';
    badge.className = 'online';
    badge.innerHTML = '\u2705 Conectado';
    document.body.appendChild(badge);

    /* Agregar dot al user bar */
    var userBar = document.getElementById('user-bar');
    if(userBar){
      var dot = document.createElement('span');
      dot.id = 'network-status-dot';
      dot.className = 'online';
      dot.title = 'En línea';
      userBar.appendChild(dot);
    }

    function showStatus(type){
      badge.className = type + ' show';
      badge.innerHTML = type === 'online'
        ? '\u26A1 Conexi\u00F3n restaurada'
        : '\uD83D\uDCDE Sin conexi\u00F3n — datos guardados localmente';
      if(userBar){
        var d = document.getElementById('network-status-dot');
        if(d){
          d.className = type;
          d.title = type === 'online' ? 'En l\u00EDnea' : 'Sin conexi\u00F3n';
        }
      }
      setTimeout(function(){ badge.classList.remove('show'); }, 3500);
    }

    window.addEventListener('online', function(){
      showStatus('online');
    });
    window.addEventListener('offline', function(){
      showStatus('offline');
    });

    /* Monitorear Flask server con ping */
    var lastOnline = true;
    function pingServer(){
      var xhr = new XMLHttpRequest();
      xhr.timeout = 3000;
      xhr.open('GET', '/api/auth/me', true);
      xhr.onload = function(){
        var nowOnline = xhr.status > 0 && xhr.status < 500;
        if(nowOnline !== lastOnline){
          lastOnline = nowOnline;
          showStatus(nowOnline ? 'online' : 'offline');
        }
        setTimeout(pingServer, 30000);
      };
      xhr.onerror = function(){
        if(lastOnline){
          lastOnline = false;
          showStatus('offline');
        }
        setTimeout(pingServer, 15000);
      };
      xhr.ontimeout = function(){
        setTimeout(pingServer, 15000);
      };
      try { xhr.send(); } catch(e){}
    }
    setTimeout(pingServer, 2000);
  }

  /* ----- INIT ----- */
  function init(){
    setTimeout(function(){
      initDarkMode();
      initNetworkStatus();
      console.log('[v24] Dark mode + network status listo');
    }, 300);
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
