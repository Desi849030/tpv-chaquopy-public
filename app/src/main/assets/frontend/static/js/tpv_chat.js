/* ============================================================================
   tpv_chat.js — Agente IA TPV (profesional)
   - Detecta rol y nombre reales del usuario (AUTH.usuario).
   - Saludo personalizado por nombre + rol.
   - Botón flotante ARRASTRABLE (recuerda posición).
   - Sugerencias según el rol. Respuestas con el rol correcto al backend.
   - 100% offline (usa /api/agent/chat del backend embebido).
   ========================================================================= */
(function () {
  'use strict';
  if (document.getElementById('chat-tpv')) return;

  // ---- Helpers de usuario ----
  function _usuario() {
    var u = (window.AUTH && AUTH.usuario) ? AUTH.usuario : null;
    if (!u && window.tpvState && tpvState.usuarioActual) u = tpvState.usuarioActual;
    return u || {};
  }
  function _rol() { return (_usuario().rol || 'vendedor'); }
  function _nombre() {
    var u = _usuario();
    return (u.nombre || u.username || '').split(' ')[0] || 'usuario';
  }
  function _rolLabel(r) {
    return ({ desarrollador: 'Desarrollador', administrador: 'Administrador',
              supervisor: 'Supervisor', vendedor: 'Vendedor', cajero: 'Cajero',
              cliente: 'Cliente' })[r] || r;
  }
  function _rolIcon(r) {
    return ({ desarrollador: '💻', administrador: '👔', supervisor: '👁️',
              vendedor: '🛒', cajero: '💵', cliente: '🛒' })[r] || '👤';
  }

  // Sugerencias contextuales por rol
  function _sugerencias() {
    var r = _rol();
    if (r === 'vendedor' || r === 'cajero')
      return [['¿Cuánto vendí hoy?', 'Mis ventas'], ['¿Qué productos hay?', 'Catálogo'], ['Recomiéndame algo', 'Recomendar']];
    if (r === 'supervisor')
      return [['Resumen de ventas de hoy', 'Resumen'], ['¿Stock bajo?', 'Stock'], ['Rendimiento de vendedores', 'Vendedores']];
    // admin / dev
    return [['Resumen del negocio hoy', 'Resumen'], ['¿Stock crítico?', 'Stock'], ['Productos más vendidos', 'Top'], ['Estado del sistema', 'Sistema']];
  }

  // ---- Estilos ----
  var css = document.createElement('style');
  css.textContent =
    '#chat-tpv{position:fixed;z-index:9999;font-family:Poppins,sans-serif}' +
    '#chat-btn{width:56px;height:56px;border-radius:50%;border:none;color:#fff;cursor:grab;' +
      'background:linear-gradient(135deg,#4f46e5,#06b6d4);box-shadow:0 8px 24px rgba(79,70,229,.5);' +
      'font-size:1.4rem;display:flex;align-items:center;justify-content:center;transition:transform .15s;touch-action:none}' +
    '#chat-btn:active{cursor:grabbing;transform:scale(.94)}' +
    '#chat-box{position:absolute;bottom:66px;right:0;width:320px;max-width:88vw;border-radius:16px;overflow:hidden;' +
      'box-shadow:0 18px 50px rgba(0,0,0,.45);border:1px solid #2b3542;display:none;animation:chatIn .2s ease}' +
    '@keyframes chatIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}' +
    '#chat-head{background:linear-gradient(135deg,#4f46e5,#6366f1);padding:10px 14px;color:#fff;display:flex;align-items:center;gap:8px}' +
    '#chat-msgs{height:280px;overflow-y:auto;padding:10px;background:#0f141b;font-size:.8rem;display:flex;flex-direction:column;gap:8px}' +
    '.chat-b{padding:8px 11px;border-radius:12px;max-width:85%;line-height:1.4;word-wrap:break-word}' +
    '.chat-u{align-self:flex-end;background:linear-gradient(135deg,#4f46e5,#6366f1);color:#fff;border-bottom-right-radius:4px}' +
    '.chat-a{align-self:flex-start;background:#1a212b;color:#e8edf4;border-bottom-left-radius:4px;border:1px solid #2b3542}' +
    '.chat-typing{align-self:flex-start;color:#94a3b8;font-style:italic;font-size:.75rem}' +
    '#chat-sug{display:flex;gap:5px;flex-wrap:wrap;padding:8px;background:#141b24;border-top:1px solid #2b3542}' +
    '#chat-sug button{background:#222b37;border:1px solid #2b3542;color:#cbd5e1;padding:4px 10px;border-radius:14px;cursor:pointer;font-size:.68rem;transition:background .15s}' +
    '#chat-sug button:hover{background:#4f46e5;color:#fff}' +
    '#chat-foot{padding:8px;display:flex;gap:6px;background:#141b24;border-top:1px solid #2b3542}' +
    '#chat-inp{flex:1;padding:8px 12px;background:#0f141b;border:1px solid #2b3542;border-radius:18px;color:#fff;font-size:.78rem;outline:none}' +
    '#chat-inp:focus{border-color:#4f46e5}' +
    '#chat-send{background:linear-gradient(135deg,#4f46e5,#6366f1);border:none;color:#fff;padding:0 14px;border-radius:18px;cursor:pointer;font-weight:600;font-size:.75rem}';
  document.head.appendChild(css);

  // ---- HTML ----
  var box =
    '<div id="chat-box">' +
      '<div id="chat-head"><span id="chat-head-ic"><i class="bi bi-stars"></i></span>' +
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
    '<button id="chat-btn" title="Asistente IA (arrástrame)"><i class="bi bi-chat-dots-fill"></i></button>';

  var wrap = document.createElement('div');
  wrap.id = 'chat-tpv';
  wrap.innerHTML = box;
  document.body.appendChild(wrap);

  // Restaurar posición guardada
  try {
    var pos = JSON.parse(localStorage.getItem('tpv_chat_pos') || 'null');
    if (pos && pos.left != null) { wrap.style.left = pos.left + 'px'; wrap.style.top = pos.top + 'px'; wrap.style.right = 'auto'; wrap.style.bottom = 'auto'; }
    else { wrap.style.right = '16px'; wrap.style.bottom = '16px'; }
  } catch (e) { wrap.style.right = '16px'; wrap.style.bottom = '16px'; }

  var msgsEl = document.getElementById('chat-msgs');
  var saludado = false;

  function burbuja(texto, quien) {
    var d = document.createElement('div');
    d.className = 'chat-b ' + (quien === 'u' ? 'chat-u' : 'chat-a');
    d.textContent = texto;
    msgsEl.appendChild(d);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return d;
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
    if (saludado) return;
    saludado = true;
    var r = _rol();
    document.getElementById('chat-head-ic').textContent = _rolIcon(r);
    document.getElementById('chat-head-sub').textContent = _nombre() + ' · ' + _rolLabel(r);
    var hora = new Date().getHours();
    var saludo = hora < 12 ? 'Buenos días' : (hora < 19 ? 'Buenas tardes' : 'Buenas noches');
    burbuja(saludo + ', ' + _nombre() + ' ' + _rolIcon(r) + '. Soy tu asistente TPV. ' +
            'Como ' + _rolLabel(r) + ', puedo ayudarte con ' +
            (r === 'vendedor' || r === 'cajero' ? 'tus ventas, el catálogo y recomendaciones.' :
             r === 'supervisor' ? 'reportes, stock y rendimiento del equipo.' :
             'ventas, inventario, reportes y el estado del sistema.') +
            ' ¿En qué te ayudo?', 'a');
    pintarSugerencias();
  }

  // Detecta si el mensaje pide una ACCIÓN que modifica datos. Devuelve el plan
  // (url, método, body, descripción para confirmar) o null si es una consulta.
  function _detectarAccion(texto) {
    var t = (texto || '').toLowerCase();
    var rol = _rol();
    var puedeAdmin = (rol === 'administrador' || rol === 'desarrollador');

    // Respaldo / backup
    if (/\b(respaldo|backup|copia de seguridad|guarda(r)? copia)\b/.test(t)) {
      return { descripcion: '¿Crear un respaldo (backup) de la base de datos ahora?',
               url: '/api/db/backup', metodo: 'POST', exito: 'Respaldo creado.' };
    }
    // Sincronizar con Supabase
    if (/\b(sincroniz|sube a la nube|subir a supabase|sync)\b/.test(t) && puedeAdmin) {
      return { descripcion: '¿Sincronizar todos los datos con Supabase ahora?',
               url: '/api/supabase/sync-full', metodo: 'POST', exito: 'Sincronización lanzada.' };
    }
    // Importar catálogo a inventario
    if (/\b(importar catalogo|importar catálogo|reabastec|cargar catalogo|importar productos al almac)\b/.test(t) && puedeAdmin) {
      return { descripcion: '¿Importar el catálogo de productos al almacén general?',
               url: '/api/inventario/importar-catalogo', metodo: 'POST',
               exito: 'Catálogo importado al almacén.', refrescar: 'dashboard_cargar' };
    }
    return null;
  }

  var api = {
    toggle: function () {
      var b = document.getElementById('chat-box');
      var abrir = b.style.display === 'none' || !b.style.display;
      b.style.display = abrir ? 'block' : 'none';
      if (abrir) { saludar(); document.getElementById('chat-inp').focus(); }
    },
    // El agente da la bienvenida al entrar: abre el chat, saluda y avisa
    // proactivamente de cosas importantes (stock crítico).
    bienvenida: async function () {
      var b = document.getElementById('chat-box');
      if (b) b.style.display = 'block';
      saludar();
      // Aviso proactivo de stock crítico (si el rol tiene acceso a inventario).
      try {
        var r = await fetch('/api/inventario/general', { credentials: 'same-origin' });
        if (r.ok) {
          var d = await r.json();
          var inv = d.inventario || [];
          var criticos = inv.filter(function (p) {
            return parseFloat(p.stock_actual || 0) <= parseFloat(p.stock_minimo || 5);
          });
          if (criticos.length) {
            var nombres = criticos.slice(0, 4).map(function (p) { return p.nombre; }).join(', ');
            burbuja('🔔 Aviso: tienes ' + criticos.length + ' producto(s) con stock crítico' +
                    (nombres ? ' (' + nombres + ')' : '') + '. ¿Quieres que prepare un pedido de reabastecimiento?', 'a');
          }
        }
      } catch (e) {}
      // Auto-ocultar a los 9s si el usuario no interactúa (no molestar).
      setTimeout(function () {
        if (b && !window._tpvChatInteract) b.style.display = 'none';
      }, 9000);
    },
    send: async function () {
      var inp = document.getElementById('chat-inp');
      var msg = (inp.value || '').trim();
      if (!msg) return;
      window._tpvChatInteract = true;  // el usuario está interactuando
      burbuja(msg, 'u');
      inp.value = '';

      // ¿Es una ACCIÓN que modifica datos? Pedir confirmación antes de ejecutar.
      var accion = _detectarAccion(msg);
      if (accion) {
        var ok = (typeof tpvConfirm === 'function')
          ? await tpvConfirm({ title: 'Confirmar acción', message: accion.descripcion, okText: 'Sí, hazlo', cancelText: 'Cancelar', danger: accion.peligrosa })
          : confirm(accion.descripcion);
        if (!ok) { burbuja('De acuerdo, no hice ningún cambio. 👍', 'a'); return; }
        burbuja('⏳ Ejecutando…', 'a');
        try {
          var rr = await fetch(accion.url, {
            method: accion.metodo || 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: accion.body ? JSON.stringify(accion.body) : null
          });
          var dd = await rr.json().catch(function () { return {}; });
          burbuja(rr.ok && (dd.ok !== false)
            ? '✅ ' + (accion.exito || 'Hecho.') + (dd.mensaje ? ' ' + dd.mensaje : '')
            : '⚠️ No se pudo completar: ' + (dd.error || dd.mensaje || 'error'), 'a');
          if (accion.refrescar && typeof window[accion.refrescar] === 'function') {
            try { window[accion.refrescar](); } catch (e) {}
          }
        } catch (e) {
          burbuja('⚠️ Error de conexión al ejecutar la acción.', 'a');
        }
        return;
      }
      var typing = document.createElement('div');
      typing.className = 'chat-typing';
      typing.textContent = 'Asistente escribiendo…';
      msgsEl.appendChild(typing);
      msgsEl.scrollTop = msgsEl.scrollHeight;
      try {
        var res = await fetch('/api/agent/chat', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ mensaje: msg, rol: _rol(), nombre: _nombre(), usuario: _usuario() })
        });
        var data = await res.json();
        typing.remove();
        var r = data.respuesta;
        if (r && typeof r === 'object') r = r.response || r.answer || JSON.stringify(r);
        r = r || data.answer || data.response || 'No tengo una respuesta para eso todavía.';
        burbuja(r, 'a');
      } catch (e) {
        typing.remove();
        burbuja('⚠️ No pude conectar con el asistente. Revisa que el servidor esté activo.', 'a');
      }
    }
  };
  window.tpvChat = api;
  window.toggleChat = api.toggle;   // compat
  window.sendMsg = api.send;        // compat
  window.quickAsk = function (m) { document.getElementById('chat-inp').value = m; api.send(); };

  // ---- Arrastre del botón (ratón + táctil) ----
  (function () {
    var btn = document.getElementById('chat-btn');
    var dragging = false, moved = false, sx, sy, ox, oy;

    // El icono <i> dentro del botón no debe capturar los eventos.
    btn.style.pointerEvents = 'auto';
    var ic = btn.querySelector('i');
    if (ic) ic.style.pointerEvents = 'none';

    var _lastToggle = 0;
    function _toggleSafe() {
      var now = Date.now();
      if (now - _lastToggle < 350) return; // evitar doble disparo (touch+click)
      _lastToggle = now;
      api.toggle();
    }
    // Respaldo: click directo abre/cierra (ratón / WebView).
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      if (!moved) _toggleSafe();
      moved = false;
    });

    function start(x, y) {
      dragging = true; moved = false;
      var rect = wrap.getBoundingClientRect();
      ox = rect.left; oy = rect.top; sx = x; sy = y;
    }
    function move(x, y) {
      if (!dragging) return;
      var dx = x - sx, dy = y - sy;
      if (Math.abs(dx) > 6 || Math.abs(dy) > 6) moved = true;
      var nl = Math.min(Math.max(0, ox + dx), window.innerWidth - 60);
      var nt = Math.min(Math.max(0, oy + dy), window.innerHeight - 60);
      wrap.style.left = nl + 'px'; wrap.style.top = nt + 'px';
      wrap.style.right = 'auto'; wrap.style.bottom = 'auto';
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      if (moved) {
        var rect = wrap.getBoundingClientRect();
        try { localStorage.setItem('tpv_chat_pos', JSON.stringify({ left: rect.left, top: rect.top })); } catch (e) {}
      }
      // El toggle lo hace el handler 'click' (mejor compatibilidad WebView).
    }
    btn.addEventListener('mousedown', function (e) { start(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { move(e.clientX, e.clientY); });
    window.addEventListener('mouseup', end);
    btn.addEventListener('touchstart', function (e) { var t = e.touches[0]; start(t.clientX, t.clientY); }, { passive: true });
    window.addEventListener('touchmove', function (e) { if (dragging && moved) { var t = e.touches[0]; move(t.clientX, t.clientY); e.preventDefault(); } }, { passive: false });
    window.addEventListener('touchend', function () {
      var wasDragging = dragging;
      end();
      // En táctil, si no hubo arrastre, disparar toggle (algunos WebView no
      // generan 'click' sintético tras touch). _toggleSafe evita doble disparo.
      if (wasDragging && !moved) _toggleSafe();
      moved = false;
    });
  })();
})();
