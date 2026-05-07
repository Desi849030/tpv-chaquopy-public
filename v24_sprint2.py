#!/usr/bin/env python3
"""v24 Sprint 2: Dark Mode Completo + Network Status"""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(BASE, "app/src/main/assets/frontend")
STATIC = os.path.join(FE, "static")
JS_DIR = os.path.join(STATIC, "js")
CSS_DIR = os.path.join(STATIC, "css")

# ============================================================
# 1) DARK MODE CSS COMPLETO
# ============================================================
dark_css = r'''/* ========== v24: Dark Mode Completo ========== */
:root {
  --bg-body: #f0f2f5;
  --bg-card: #ffffff;
  --bg-input: #f8fafc;
  --bg-nav: #1e293b;
  --bg-tab-active: #667eea;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-inverse: #ffffff;
  --border-color: #e2e8f0;
  --shadow-color: rgba(0,0,0,0.08);
  --kpi-gradient-1: #667eea;
  --kpi-gradient-2: #764ba2;
  --glass-bg: rgba(255,255,255,0.75);
  --glass-border: rgba(255,255,255,0.3);
  --table-header: #f1f5f9;
  --table-stripe: #f8fafc;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --info: #3b82f6;
}

[data-theme="dark"] {
  --bg-body: #0f172a;
  --bg-card: #1e293b;
  --bg-input: #334155;
  --bg-nav: #020617;
  --bg-tab-active: #818cf8;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-inverse: #0f172a;
  --border-color: #334155;
  --shadow-color: rgba(0,0,0,0.3);
  --glass-bg: rgba(30,41,59,0.85);
  --glass-border: rgba(51,65,85,0.5);
  --table-header: #1e293b;
  --table-stripe: #162032;
  --success: #34d399;
  --danger: #f87171;
  --warning: #fbbf24;
  --info: #60a5fa;
}

/* Aplicar variables a elementos clave */
[data-theme="dark"] body,
[data-theme="dark"] .container-fluid,
[data-theme="dark"] .tab-content,
[data-theme="dark"] .card,
[data-theme="dark"] .panel,
[data-theme="dark"] .modal-content,
[data-theme="dark"] .dropdown-menu,
[data-theme="dark"] .form-control,
[data-theme="dark"] .form-select {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

[data-theme="dark"] body {
  background-color: var(--bg-body) !important;
}

[data-theme="dark"] .table,
[data-theme="dark"] .table th,
[data-theme="dark"] .table td {
  background-color: transparent !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

[data-theme="dark"] .table thead th {
  background-color: var(--table-header) !important;
  color: var(--text-secondary) !important;
}

[data-theme="dark"] .table-striped tbody tr:nth-of-type(odd) {
  background-color: var(--table-stripe) !important;
}

[data-theme="dark"] input,
[data-theme="dark"] select,
[data-theme="dark"] textarea {
  background-color: var(--bg-input) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

[data-theme="dark"] input::placeholder {
  color: var(--text-secondary) !important;
}

[data-theme="dark"] .btn-primary {
  background: linear-gradient(135deg, var(--bg-tab-active), var(--kpi-gradient-2)) !important;
}

[data-theme="dark"] .btn-secondary,
[data-theme="dark"] .btn-outline-secondary {
  background-color: var(--bg-input) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

[data-theme="dark"] .nav-tabs .nav-link {
  color: var(--text-secondary) !important;
  background-color: transparent !important;
  border-color: transparent !important;
}

[data-theme="dark"] .nav-tabs .nav-link.active {
  color: var(--text-inverse) !important;
  background-color: var(--bg-tab-active) !important;
}

[data-theme="dark"] .badge {
  color: var(--text-inverse) !important;
}

[data-theme="dark"] .glass-card {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid var(--glass-border) !important;
}

[data-theme="dark"] .card {
  box-shadow: 0 4px 16px var(--shadow-color) !important;
}

[data-theme="dark"] #catalog-search {
  background-color: var(--bg-input) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

[data-theme="dark"] #catalog-search::placeholder {
  color: var(--text-secondary) !important;
}

[data-theme="dark"] #tpv-chat-fab,
[data-theme="dark"] #ia-bubble-container {
  filter: brightness(0.9);
}

[data-theme="dark"] .modal-header,
[data-theme="dark"] .modal-footer {
  border-color: var(--border-color) !important;
}

[data-theme="dark"] .list-group-item {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

/* Toggle button */
#dark-mode-toggle {
  position: fixed;
  bottom: 90px;
  right: 16px;
  z-index: 9998;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #fff;
  font-size: 22px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(251,191,36,0.4);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
#dark-mode-toggle:active {
  transform: scale(0.9);
}
[data-theme="dark"] #dark-mode-toggle {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 4px 16px rgba(99,102,241,0.4);
}

/* ========== v24: Network Status Indicator ========== */
#tpv-network-badge {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%) translateY(-100px);
  z-index: 99998;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  transition: transform 0.4s cubic-bezier(.4,0,.2,1);
  pointer-events: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
#tpv-network-badge.online {
  background: linear-gradient(135deg, #10b981, #059669);
}
#tpv-network-badge.offline {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
#tpv-network-badge.show {
  transform: translateX(-50%) translateY(0);
}

/* Status dot en user bar */
#network-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-left: 8px;
  vertical-align: middle;
  transition: background 0.3s;
}
#network-status-dot.online { background: #10b981; box-shadow: 0 0 6px #10b981; }
#network-status-dot.offline { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
'''
dark_path = os.path.join(CSS_DIR, "v24_dark_complete.css")
with open(dark_path, 'w') as f:
    f.write(dark_css)
print(f"[OK] {dark_path} ({len(dark_css)} bytes)")

# ============================================================
# 2) DARK MODE + NETWORK JS
# ============================================================
dark_js = r'''/* ========== v24: Dark Mode Toggle + Network Status ========== */
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
'''
dark_js_path = os.path.join(JS_DIR, "dark_and_network.js")
with open(dark_js_path, 'w') as f:
    f.write(dark_js)
print(f"[OK] {dark_js_path} ({len(dark_js)} bytes)")

# ============================================================
# 3) AGREGAR A index.html
# ============================================================
index_path = os.path.join(FE, "templates", "index.html")
with open(index_path, 'r') as f:
    html = f.read()

if 'v24_dark_complete.css' not in html:
    html = html.replace(
        '</head>',
        '  <link rel="stylesheet" href="static/css/v24_dark_complete.css">\n</head>'
    )
    print("[OK] v24_dark_complete.css agregado a index.html")

if 'dark_and_network.js' not in html:
    html = html.replace(
        '<script src="static/js/catalog_and_order.js"></script>',
        '<script src="static/js/catalog_and_order.js"></script>\n    <script src="static/js/dark_and_network.js"></script>'
    )
    print("[OK] dark_and_network.js agregado a index.html")

with open(index_path, 'w') as f:
    f.write(html)

print("\n=== v24 SPRINT 2 COMPLETADO ===")
print(f"Archivos creados:")
print(f"  - v24_dark_complete.css ({len(dark_css)} bytes)")
print(f"  - dark_and_network.js ({len(dark_js)} bytes)")
print("Modificados:")
print("  - index.html (2 inserciones)")
