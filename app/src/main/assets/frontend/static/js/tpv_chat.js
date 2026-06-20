/* tpv_chat.js v8.7-universal - Reset atomico por usuario */

async function _syncChatIdentity() {
    try {
        const r = await fetch('/api/agent/identity', {credentials: 'same-origin', cache: 'no-store'});
        const d = await r.json();
        if (d.ok) {
            const prevUserId = window.TPV_USER_ID;
            window.TPV_ROL = d.rol;
            window.TPV_USER = d.nombre;
            window.TPV_USER_ID = d.usuario_id;
            window.TPV_AUTH = d.autenticado;
            if (prevUserId && prevUserId !== d.usuario_id) {
                console.log('[Chat] Cambio de usuario:', prevUserId, '->', d.usuario_id);
                if (window.tpvChat && typeof window.tpvChat.resetParaNuevoUsuario === 'function') {
                    window.tpvChat.resetParaNuevoUsuario();
                }
            }
        } else {
            window.TPV_ROL = null; window.TPV_USER = null;
            window.TPV_USER_ID = null; window.TPV_AUTH = false;
            if (window.tpvChat && typeof window.tpvChat.resetParaNuevoUsuario === 'function') {
                window.tpvChat.resetParaNuevoUsuario();
            }
        }
    } catch(e) { console.warn('[Chat] Sync error:', e); }
}

document.addEventListener('DOMContentLoaded', _syncChatIdentity);
window.addEventListener('tpv_role_changed', _syncChatIdentity);

(function () {
  'use strict';
  if (document.getElementById('chat-tpv')) return;

  function _usuario() {
    var u = (window.AUTH && AUTH.usuario) ? AUTH.usuario : null;
    if (!u && window.tpvState && tpvState.usuarioActual) u = tpvState.usuarioActual;
    if (!u && window.TPV_USER_ID) {
        u = {usuario_id: window.TPV_USER_ID, nombre: window.TPV_USER, rol: window.TPV_ROL};
    }
    return u || {};
  }
  function _rol() { return (_usuario().rol || 'cliente'); }
  function _nombre() {
    var u = _usuario();
    return (u.nombre || u.username || '').split(' ')[0] || 'usuario';
  }
  function _userId() { return _usuario().usuario_id || _usuario().id || 'anon'; }
  function _chatKey() { return 'chat_history_' + _userId(); }
  function _rolLabel(r) {
    return ({desarrollador:'Desarrollador',administrador:'Administrador',supervisor:'Supervisor',vendedor:'Vendedor',cajero:'Cajero',cliente:'Cliente'})[r] || r;
  }
  function _rolIcon(r) {
    return ({desarrollador:'💻',administrador:'👔',supervisor:'👁️',vendedor:'🛒',cajero:'💵',cliente:'🛒'})[r] || '👤';
  }
  function _sugerencias() {
    var r = _rol();
    if (r === 'cliente') return [['¿Qué productos tienen?','Catálogo'],['¿Hay ofertas?','Ofertas'],['¿En qué tienda hay café?','Tiendas'],['Categorías','Categorías']];
    if (r === 'vendedor' || r === 'cajero') return [['¿Cuánto vendí hoy?','Mis ventas'],['Stock bajo','Stock']];
    if (r === 'supervisor') return [['Dashboard de hoy','Dashboard'],['Stock crítico','Stock']];
    if (r === 'administrador') return [['Balance del día','Balance'],['Gastos','Gastos']];
    if (r === 'desarrollador') return [['Estado del sistema','Sistema'],['Logs','Logs']];
    return [['Ayuda','Ayuda']];
  }

  var css = document.createElement('style');
  css.textContent =
    '#chat-tpv{position:fixed;z-index:9999;font-family:Poppins,sans-serif}' +
    '#chat-btn{width:56px;height:56px;border-radius:50%;border:none;color:#fff;cursor:grab;background:linear-gradient(135deg,#4f46e5,#06b6d4);box-shadow:0 8px 24px rgba(79,70,229,.5);font-size:1.4rem;display:flex;align-items:center;justify-content:center;touch-action:none}' +
    '#chat-btn:active{cursor:grabbing;transform:scale(.94)}' +
    '#chat-box{position:absolute;bottom:66px;right:0;width:340px;max-width:calc(100vw - 20px);border-radius:16px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.45);border:1px solid #2b3542;display:none;box-sizing:border-box}' +
    '#chat-head{background:linear-gradient(135deg,#4f46e5,#6366f1);padding:10px 14px;color:#fff;display:flex;align-items:center;gap:8px}' +
    '#chat-msgs{height:280px;overflow-y:auto;padding:10px;background:#0f141b;font-size:.8rem;display:flex;flex-direction:column;gap:8px}' +
    '.chat-b{padding:8px 11px;border-radius:12px;max-width:85%;line-height:1.4;word-wrap:break-word}' +
    '.chat-u{align-self:flex-end;background:linear-gradient(135deg,#4f46e5,#6366f1);color:#fff;border-bottom-right-radius:4px}' +
    '.chat-a{align-self:flex-start;background:#1a212b;color:#e8edf4;border-bottom-left-radius:4px;border:1px solid #2b3542}' +
    '.chat-typing{align-self:flex-start;color:#94a3b8;font-style:italic;font-size:.75rem}' +
    '#chat-sug{display:flex;gap:5px;flex-wrap:wrap;padding:8px;background:#141b24;border-top:1px solid #2b3542}' +
    '#chat-sug button{background:#222b37;border:1px solid #2b3542;color:#cbd5e1;padding:4px 10px;border-radius:14px;cursor:pointer;font-size:.68rem}' +
    '#chat-sug button:hover{background:#4f46e5;color:#fff}' +
    '#chat-foot{padding:8px;display:flex;gap:6px;background:#141b24;border-top:1px solid #2b3542;align-items:center;box-sizing:border-box}' +
    '#chat-inp{flex:1 1 auto;min-width:0;padding:8px 12px;background:#0f141b;border:1px solid #2b3542;border-radius:18px;color:#fff;font-size:.78rem;outline:none;box-sizing:border-box}' +
    '#chat-inp:focus{border-color:#4f46e5}' +
    '#chat-send{background:linear-gradient(135deg,#4f46e5,#6366f1);border:none;color:#fff;padding:8px 16px;border-radius:18px;cursor:pointer;font-weight:600;font-size:.78rem;min-height:36px;white-space:nowrap;flex-shrink:0}';
  document.head.appendChild(css);

  var box =
    '<div id="chat-box">' +
      '<div id="chat-head"><span id="chat-head-ic">💬</span>' +
        '<div style="flex:1;line-height:1.1"><div style="font-weight:700;font-size:.85rem">Asistente TPV</div>' +
        '<div id="chat-head-sub" style="font-size:.66rem;opacity:.85"></div></div>' +
        '<button onclick="window.tpvChat.toggle()" style="background:none;border:none;color:#fff;cursor:pointer;font-size:1.1rem">✕</button>' +
      '</div>' +
      '<div id="chat-msgs"></div>' +
      '<div id="chat-sug"></div>' +
      '<div id="chat-foot">' +
        '<input id="chat-inp" placeholder="Escribe tu pregunta..." onkeypress="if(event.key===\'Enter\')window.tpvChat.send()">' +
        '<button id="chat-send" onclick="window.tpvChat.send()">Enviar</button>' +
      '</div>' +
    '</div>' +
    '<button id="chat-btn" title="Asistente IA">💬</button>';

  var wrap = document.createElement('div');
  wrap.id = 'chat-tpv';
  wrap.innerHTML = box;
  document.body.appendChild(wrap);

  try {
    var pos = JSON.parse(localStorage.getItem('tpv_chat_pos') || 'null');
    if (pos && pos.left != null) { wrap.style.left = pos.left + 'px'; wrap.style.top = pos.top + 'px'; wrap.style.right = 'auto'; wrap.style.bottom = 'auto'; }
    else { wrap.style.right = '16px'; wrap.style.bottom = '16px'; }
  } catch (e) { wrap.style.right = '16px'; wrap.style.bottom = '16px'; }

  var msgsEl = document.getElementById('chat-msgs');

  function burbuja(texto, quien) {
    var d = document.createElement('div');
    d.className = 'chat-b ' + (quien === 'u' ? 'chat-u' : 'chat-a');
    d.textContent = texto;
    msgsEl.appendChild(d);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    _guardarHistorial();
    return d;
  }

  function _guardarHistorial() {
    try {
      var key = _chatKey();
      if (!key || key === 'chat_history_anon') return;
      var historial = [];
      msgsEl.querySelectorAll('.chat-b').forEach(function(b) {
        historial.push({texto: b.textContent, quien: b.classList.contains('chat-u') ? 'u' : 'a'});
      });
      localStorage.setItem(key, JSON.stringify(historial.slice(-50)));
    } catch(e) {}
  }

  function _cargarHistorial() {
    try {
      var key = _chatKey();
      if (!key || key === 'chat_history_anon') return;
      var historial = JSON.parse(localStorage.getItem(key) || '[]');
      historial.forEach(function(m) {
        var d = document.createElement('div');
        d.className = 'chat-b ' + (m.quien === 'u' ? 'chat-u' : 'chat-a');
        d.textContent = m.texto;
        msgsEl.appendChild(d);
      });
      msgsEl.scrollTop = msgsEl.scrollHeight;
    } catch(e) {}
  }

  function pintarSugerencias() {
    var cont = document.getElementById('chat-sug');
    cont.innerHTML = '';
    _sugerencias().forEach(function (s) {
      var b = document.createElement('button');
      b.textContent = s[1];
      b.onclick = function () { document.getElementById('chat-inp').value = s[0]; api.send(); };
      cont.appendChild(b);
    });
  }

  function saludar() {
    if (window._tpvChatSaludado) return;
    window._tpvChatSaludado = true;
    var r = _rol();
    document.getElementById('chat-head-ic').textContent = _rolIcon(r);
    document.getElementById('chat-head-sub').textContent = _nombre() + ' · ' + _rolLabel(r);
    var hora = new Date().getHours();
    var saludo = hora < 12 ? 'Buenos días' : (hora < 19 ? 'Buenas tardes' : 'Buenas noches');
    if (r === 'cliente' && !window.AUTH?.usuario) {
        burbuja(saludo + ' 🛍️. Soy tu asistente. Puedo ayudarte a buscar productos, ver precios, ofertas y en qué tienda hay lo que necesitas. ¿Qué te ayudo a encontrar?', 'a');
    } else {
        burbuja(saludo + ' ' + _nombre() + ' ' + _rolIcon(r) + '. ¿En qué puedo ayudarte?', 'a');
    }
    console.log('[Chat] Saludo emitido para rol:', r, 'usuario:', _nombre());
    pintarSugerencias();
  }

  var api = {
    resetParaNuevoUsuario: function() {
      console.log('[Chat] Reset atomico');
      window._tpvChatSaludado = false;
      window._tpvChatInteract = false;
      msgsEl.innerHTML = '';
      var sug = document.getElementById('chat-sug');
      if (sug) sug.innerHTML = '';
      var sub = document.getElementById('chat-head-sub');
      if (sub) sub.textContent = '';
      var b = document.getElementById('chat-box');
      if (b) b.style.display = 'none';
      _cargarHistorial();
    },
    toggle: function () {
      var b = document.getElementById('chat-box');
      var abrir = b.style.display === 'none' || !b.style.display;
      b.style.display = abrir ? 'block' : 'none';
      if (abrir) {
        _syncChatIdentity().then(function() {
          saludar();
          document.getElementById('chat-inp').focus();
        });
      }
    },
    send: async function () {
      var inp = document.getElementById('chat-inp');
      var msg = (inp.value || '').trim();
      if (!msg) return;
      window._tpvChatInteract = true;
      await _syncChatIdentity();
      burbuja(msg, 'u');
      inp.value = '';
      var typing = document.createElement('div');
      typing.className = 'chat-typing';
      typing.textContent = 'Asistente escribiendo…';
      msgsEl.appendChild(typing);
      msgsEl.scrollTop = msgsEl.scrollHeight;
      try {
        var res = await fetch('/api/agent/chat', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          credentials: 'same-origin',
          body: JSON.stringify({mensaje: msg, nombre: _nombre()})
        });
        var data = await res.json();
        typing.remove();
        var r = data.respuesta;
        if (r && typeof r === 'object') r = r.response || r.answer || JSON.stringify(r);
        r = r || data.answer || data.response || 'No tengo respuesta.';
        burbuja(r, 'a');
      } catch (e) {
        typing.remove();
        burbuja('⚠️ Error de conexion.', 'a');
      }
    }
  };
  window.tpvChat = api;
  window.toggleChat = api.toggle;
  window.sendMsg = api.send;

  // === DRAG CON POINTER EVENTS (garantizado en móvil) ===
  (function () {
    var btn = document.getElementById('chat-btn');
    if (!btn) return;
    var dragging = false, moved = false, sx, sy, ox, oy;
    var _lastToggle = 0;
    var activePointerId = null;

    function _toggleSafe() {
      var now = Date.now();
      if (now - _lastToggle < 350) return;
      _lastToggle = now;
      api.toggle();
    }

    function start(x, y) {
      dragging = true; moved = false;
      sx = x; sy = y;
      var rect = wrap.getBoundingClientRect();
      ox = rect.left; oy = rect.top;
    }
    function move(x, y) {
      if (!dragging) return;
      var dx = x - sx, dy = y - sy;
      if (Math.abs(dx) > 6 || Math.abs(dy) > 6) moved = true;
      if (!moved) return;
      var btnSize = 56;
      var nl = Math.min(Math.max(4, ox + dx), window.innerWidth - btnSize - 4);
      var nt = Math.min(Math.max(4, oy + dy), window.innerHeight - btnSize - 4);
      wrap.style.left = nl + 'px';
      wrap.style.top = nt + 'px';
      wrap.style.right = 'auto';
      wrap.style.bottom = 'auto';
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      if (moved) {
        var rect = wrap.getBoundingClientRect();
        var midX = window.innerWidth / 2;
        var snapLeft = rect.left < midX ? 8 : (window.innerWidth - 60);
        wrap.style.transition = 'left 0.2s ease';
        wrap.style.left = snapLeft + 'px';
        setTimeout(function() { wrap.style.transition = ''; }, 250);
        try {
          localStorage.setItem('tpv_chat_pos', JSON.stringify({left: snapLeft, top: rect.top}));
        } catch (e) {}
      }
      if (!moved) _toggleSafe();
      moved = false;
    }

    // Pointer Events: unifican mouse + touch + pen
    btn.addEventListener('pointerdown', function(e) {
      if (activePointerId !== null) return;
      activePointerId = e.pointerId;
      start(e.clientX, e.clientY);
      try { btn.setPointerCapture(e.pointerId); } catch(err) {}
      e.preventDefault();
    });
    btn.addEventListener('pointermove', function(e) {
      if (!dragging || e.pointerId !== activePointerId) return;
      move(e.clientX, e.clientY);
      e.preventDefault();
    });
    btn.addEventListener('pointerup', function(e) {
      if (e.pointerId !== activePointerId) return;
      try { btn.releasePointerCapture(e.pointerId); } catch(err) {}
      activePointerId = null;
      end();
    });
    btn.addEventListener('pointercancel', function(e) {
      if (e.pointerId !== activePointerId) return;
      activePointerId = null;
      end();
    });
    btn.addEventListener('click', function(e) {
      if (moved) { e.preventDefault(); e.stopPropagation(); return false; }
    });
    // Prevenir scroll del body al tocar el botón
    btn.addEventListener('touchstart', function(e) { e.preventDefault(); }, {passive: false});
    btn.addEventListener('touchmove', function(e) { e.preventDefault(); }, {passive: false});
  })();

  setTimeout(_cargarHistorial, 500);
})();
