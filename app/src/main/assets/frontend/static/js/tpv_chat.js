// tpv_chat.js v5 — Burbuja arrastrable + botón Enviar GRANDE
(function() {
  'use strict';
  if (document.getElementById('chat-tpv')) return;

  var css = document.createElement('style');
  css.textContent = [
    '#chat-tpv{position:fixed;z-index:9999;font-family:Poppins,sans-serif}',
    '#chat-btn{width:60px;height:60px;border-radius:50%;border:none;color:#fff;',
    '  cursor:grab;background:linear-gradient(135deg,#4f46e5,#06b6d4);',
    '  box-shadow:0 8px 24px rgba(79,70,229,.5);font-size:1.6rem;',
    '  display:flex;align-items:center;justify-content:center;',
    '  touch-action:none;user-select:none;-webkit-user-select:none;',
    '  -webkit-tap-highlight-color:transparent;transition:transform .15s ease}',
    '#chat-btn:active{cursor:grabbing;transform:scale(.92)}',
    '#chat-box{position:absolute;bottom:72px;right:0;width:min(360px,92vw);',
    '  border-radius:18px;overflow:hidden;',
    '  box-shadow:0 24px 60px rgba(0,0,0,.5);border:1px solid #2b3542;',
    '  display:none;animation:chatSlideUp .25s ease}',
    '@keyframes chatSlideUp{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}',
    '#chat-head{background:linear-gradient(135deg,#4f46e5,#6366f1);padding:12px 16px;',
    '  color:#fff;display:flex;align-items:center;gap:10px}',
    '#chat-head-ic{font-size:1.4rem}',
    '#chat-msgs{height:300px;overflow-y:auto;padding:12px;background:#0f141b;',
    '  font-size:.85rem;display:flex;flex-direction:column;gap:8px}',
    '.chat-b{padding:10px 13px;border-radius:14px;max-width:85%;line-height:1.4;word-wrap:break-word}',
    '.chat-u{align-self:flex-end;background:linear-gradient(135deg,#4f46e5,#6366f1);color:#fff;border-bottom-right-radius:4px}',
    '.chat-a{align-self:flex-start;background:#1a212b;color:#e8edf4;border-bottom-left-radius:4px;border:1px solid #2b3542}',
    '#chat-sug{display:flex;gap:6px;flex-wrap:wrap;padding:10px;background:#141b24;border-top:1px solid #2b3542}',
    '#chat-sug button{background:#222b37;border:1px solid #2b3542;color:#cbd5e1;',
    '  padding:6px 12px;border-radius:16px;cursor:pointer;font-size:.72rem}',
    '#chat-sug button:hover{background:#4f46e5;color:#fff}',
    '#chat-foot{padding:10px;display:flex;gap:8px;background:#141b24;border-top:1px solid #2b3542;align-items:stretch}',
    '#chat-inp{flex:1;padding:10px 14px;background:#0f141b;border:1px solid #2b3542;',
    '  border-radius:22px;color:#fff;font-size:.85rem;outline:none;min-height:44px}',
    '#chat-inp:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.15)}',
    '#chat-send{background:linear-gradient(135deg,#4f46e5,#6366f1);border:none;color:#fff;',
    '  padding:0 20px;border-radius:22px;cursor:pointer;font-weight:600;font-size:.85rem;',
    '  min-height:44px;min-width:90px;display:inline-flex;align-items:center;justify-content:center;',
    '  gap:6px;white-space:nowrap;transition:all .15s;box-shadow:0 4px 12px rgba(79,70,229,.3);',
    '  flex-shrink:0}',
    '#chat-send:active{transform:scale(.96)}',
    '#chat-send:hover{box-shadow:0 6px 16px rgba(79,70,229,.4)}'
  ].join('');
  document.head.appendChild(css);

  var box =
    '<div id="chat-box">' +
      '<div id="chat-head"><span id="chat-head-ic">💬</span>' +
        '<div style="flex:1;line-height:1.1"><div style="font-weight:700;font-size:.9rem">Asistente TPV</div>' +
        '<div id="chat-head-sub" style="font-size:.68rem;opacity:.85"></div></div>' +
        '<button onclick="window.tpvChat.toggle()" style="background:none;border:none;color:#fff;cursor:pointer;font-size:1.2rem;padding:4px">✕</button>' +
      '</div>' +
      '<div id="chat-msgs"></div>' +
      '<div id="chat-sug"></div>' +
      '<div id="chat-foot">' +
        '<input id="chat-inp" placeholder="Escribe tu pregunta..." ' +
        'onkeypress="if(event.key===\'Enter\')window.tpvChat.send()">' +
        '<button id="chat-send" onclick="window.tpvChat.send()">➤ Enviar</button>' +
      '</div>' +
    '</div>' +
    '<button id="chat-btn" title="Asistente IA (mantén y arrastra para mover)">💬</button>';

  var wrap = document.createElement('div');
  wrap.id = 'chat-tpv';
  wrap.innerHTML = box;
  document.body.appendChild(wrap);

  // Posición inicial con LEFT/TOP absolutos (CLAVE para drag)
  var btnSize = 60;
  var initialLeft = window.innerWidth - btnSize - 16;
  var initialTop = window.innerHeight - btnSize - 16;
  try {
    var pos = JSON.parse(localStorage.getItem('tpv_chat_pos') || 'null');
    if (pos && typeof pos.left === 'number' && typeof pos.top === 'number') {
      initialLeft = Math.max(4, Math.min(pos.left, window.innerWidth - btnSize - 4));
      initialTop = Math.max(4, Math.min(pos.top, window.innerHeight - btnSize - 4));
    }
  } catch (e) {}
  wrap.style.left = initialLeft + 'px';
  wrap.style.top = initialTop + 'px';

  var msgsEl = document.getElementById('chat-msgs');
  var api = {
    toggle: function() {
      var boxEl = document.getElementById('chat-box');
      if (boxEl) boxEl.style.display = boxEl.style.display === 'none' || !boxEl.style.display ? 'block' : 'none';
    },
    send: function() {
      var inp = document.getElementById('chat-inp');
      if (!inp || !inp.value.trim()) return;
      var msg = inp.value.trim();
      inp.value = '';
      burbuja(msg, 'u');
      fetch('/api/agent/chat', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mensaje: msg})
      }).then(function(r) { return r.ok ? r.json() : null; })
        .then(function(data) {
          if (data && data.respuesta) burbuja(data.respuesta, 'a');
          else burbuja('Lo siento, no pude procesar tu mensaje.', 'a');
        }).catch(function() {
          burbuja('Error de conexión con el agente.', 'a');
        });
    }
  };
  window.tpvChat = api;

  function burbuja(texto, quien) {
    var div = document.createElement('div');
    div.className = 'chat-b ' + (quien === 'u' ? 'chat-u' : 'chat-a');
    div.textContent = texto;
    msgsEl.appendChild(div);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  // === DRAG con Pointer Events ===
  var btn = document.getElementById('chat-btn');
  if (!btn) return;
  var dragging = false, moved = false;
  var startX = 0, startY = 0, originX = 0, originY = 0;
  var activePointerId = null;

  function onPointerDown(e) {
    if (activePointerId !== null) return;
    activePointerId = e.pointerId;
    dragging = true; moved = false;
    startX = e.clientX; startY = e.clientY;
    var rect = wrap.getBoundingClientRect();
    originX = rect.left; originY = rect.top;
    try { btn.setPointerCapture(e.pointerId); } catch (err) {}
    e.preventDefault();
  }
  function onPointerMove(e) {
    if (!dragging || e.pointerId !== activePointerId) return;
    var dx = e.clientX - startX, dy = e.clientY - startY;
    if (Math.abs(dx) > 6 || Math.abs(dy) > 6) moved = true;
    if (!moved) return;
    var nl = Math.max(4, Math.min(originX + dx, window.innerWidth - btnSize - 4));
    var nt = Math.max(4, Math.min(originY + dy, window.innerHeight - btnSize - 4));
    wrap.style.left = nl + 'px';
    wrap.style.top = nt + 'px';
    e.preventDefault();
  }
  function onPointerUp(e) {
    if (e.pointerId !== activePointerId) return;
    try { btn.releasePointerCapture(e.pointerId); } catch (err) {}
    activePointerId = null;
    if (dragging && moved) {
      var rect = wrap.getBoundingClientRect();
      var midX = window.innerWidth / 2;
      var snapLeft = rect.left < midX ? 8 : (window.innerWidth - btnSize - 8);
      wrap.style.transition = 'left .25s cubic-bezier(.4,0,.2,1)';
      wrap.style.left = snapLeft + 'px';
      setTimeout(function() { wrap.style.transition = ''; }, 280);
      try { localStorage.setItem('tpv_chat_pos', JSON.stringify({left: snapLeft, top: rect.top})); } catch (err) {}
    }
    dragging = false;
    if (!moved) api.toggle();
    moved = false;
  }

  btn.addEventListener('pointerdown', onPointerDown);
  btn.addEventListener('pointermove', onPointerMove);
  btn.addEventListener('pointerup', onPointerUp);
  btn.addEventListener('pointercancel', onPointerUp);
  btn.addEventListener('lostpointercapture', onPointerUp);
  btn.addEventListener('click', function(e) { if (moved) { e.preventDefault(); e.stopPropagation(); return false; } });
  btn.addEventListener('touchstart', function(e) { e.preventDefault(); }, {passive: false});
  btn.addEventListener('touchmove', function(e) { e.preventDefault(); }, {passive: false});

  console.log('[CHAT] Burbuja 💬 inicializada en (' + initialLeft + ', ' + initialTop + ')');
})();
