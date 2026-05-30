// Agente IA Chat - TPV Ultra Smart
(function() {
  if (document.getElementById('chat-tpv')) return;
  
  var html = '<div id="chat-tpv" style="position:fixed;bottom:16px;right:16px;z-index:9999;font-family:sans-serif">';
  html += '<button id="chat-btn" style="width:50px;height:50px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#5b21b6);border:none;color:white;font-size:1.3rem;cursor:pointer;box-shadow:0 4px 20px rgba(124,58,237,.5)" onclick="toggleChat()">AI</button>';
  html += '<div id="chat-box" style="display:none;position:absolute;bottom:58px;right:0;width:300px;background:#1e293b;border:1px solid #334155;border-radius:12px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.5)">';
  html += '<div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:8px 12px;color:white;font-weight:700;font-size:.8rem">Agente IA TPV</div>';
  html += '<div id="chat-msgs" style="height:250px;overflow-y:auto;padding:8px;background:#0f172a;font-size:.78rem;display:flex;flex-direction:column;gap:6px"></div>';
  html += '<div style="padding:6px;display:flex;gap:4px;flex-wrap:wrap;background:#1e293b;border-top:1px solid #334155">';
  html += '<button onclick="quickAsk(\'Cuanto vendimos hoy?\')" style="background:#334155;border:none;color:#e2e8f0;padding:3px 8px;border-radius:8px;cursor:pointer;font-size:.6rem">Ventas</button>';
  html += '<button onclick="quickAsk(\'Stock bajo?\')" style="background:#334155;border:none;color:#e2e8f0;padding:3px 8px;border-radius:8px;cursor:pointer;font-size:.6rem">Stock</button>';
  html += '<button onclick="quickAsk(\'Recomiendame\')" style="background:#334155;border:none;color:#e2e8f0;padding:3px 8px;border-radius:8px;cursor:pointer;font-size:.6rem">Recomendar</button>';
  html += '</div>';
  html += '<div style="padding:6px;display:flex;gap:4px;background:#1e293b;border-top:1px solid #334155">';
  html += '<input id="chat-inp" placeholder="Escribe..." style="flex:1;padding:6px 10px;background:#0f172a;border:1px solid #334155;border-radius:16px;color:white;font-size:.75rem" onkeypress="if(event.key===\'Enter\')sendMsg()">';
  html += '<button onclick="sendMsg()" style="background:linear-gradient(135deg,#6366f1,#4f46e5);border:none;color:white;padding:6px 12px;border-radius:16px;cursor:pointer;font-weight:600;font-size:.7rem">Enviar</button>';
  html += '</div></div></div>';
  
  document.body.insertAdjacentHTML('beforeend', html);
  
  window.toggleChat = function() {
    var b = document.getElementById('chat-box');
    b.style.display = b.style.display === 'none' ? 'block' : 'none';
  };
  
  window.quickAsk = function(msg) {
    document.getElementById('chat-inp').value = msg;
    sendMsg();
  };
  
  window.sendMsg = async function() {
    var inp = document.getElementById('chat-inp');
    var msg = inp.value.trim();
    if (!msg) return;
    
    var msgs = document.getElementById('chat-msgs');
    msgs.innerHTML += '<div style="text-align:right"><span style="background:#6366f1;padding:6px 10px;border-radius:10px;color:white;font-size:.75rem">'+msg+'</span></div>';
    inp.value = '';
    
    try {
      var res = await fetch('/api/agent/chat', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({mensaje:msg, rol:'desarrollador'})
      });
      var data = await res.json();
      var respuesta = typeof data.respuesta === 'string' ? data.respuesta : (data.respuesta?.response || 'No entendi');
      msgs.innerHTML += '<div><span style="background:#1e293b;padding:6px 10px;border-radius:10px;color:#e2e8f0;font-size:.75rem">'+respuesta+'</span></div>';
    } catch(e) {
      msgs.innerHTML += '<div><span style="background:#450a0a;padding:6px 10px;border-radius:10px;color:#fca5a5;font-size:.75rem">Error</span></div>';
    }
    msgs.scrollTop = msgs.scrollHeight;
  };
  
  // Saludo
  setTimeout(function() {
    var msgs = document.getElementById('chat-msgs');
    if (msgs) msgs.innerHTML = '<div><span style="background:#1e293b;padding:6px 10px;border-radius:10px;color:#e2e8f0;font-size:.75rem">Hola! Preguntame sobre ventas, stock o metricas.</span></div>';
  }, 2000);
})();
