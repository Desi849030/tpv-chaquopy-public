// ia_assistant_ui.js - TPV Smart v1.0
// AGENTE IA DINAMICO E INTERACTIVO
// Principios:
//   1. Al abrir: muestra datos REALES del servidor (ventas, stock, KPIs por rol)
//   2. Auto-retry con backoff - NUNCA muestra "servidor inicializando"
//   3. Saludo contextual con datos SQLite en tiempo real
//   4. Alertas proactivas cada 30s con badge
//   5. Sugerencias dinamicas que cambian segun contexto
//   6. El agente interactua: pregunta, sugiere, aprende
(function(){
"use strict";

var SID = 'session_' + Date.now();
var hist = [];
var currentRole = (typeof AUTH!=='undefined'&&AUTH.usuario&&AUTH.usuario.rol)?AUTH.usuario.rol:'cliente';
var currentUserName = '';
var alertsTimer = null;
var retryTimer = null;
var serverReady = false;
var sending = false;
var greetingLoaded = false;
var retryCount = 0;
var REQ_TIMEOUT = 8000;
var lastServerAnswer = '';

function $(s){ return document.querySelector(s); }

// ============================================================
//  LIMPIEZA AL CERRAR SESION
// ============================================================
function destroy(){
    if(alertsTimer){ clearInterval(alertsTimer); alertsTimer = null; }
    if(retryTimer){ clearTimeout(retryTimer); retryTimer = null; }
    sending = false;
    serverReady = false;
    greetingLoaded = false;
    retryCount = 0;
    hist = [];
    lastServerAnswer = '';
    SID = 'session_' + Date.now();
    var panel = $('#tpv-chat-panel');
    if(panel) panel.classList.remove('open');
    var msgs = $('.tpvc-msgs');
    if(msgs) msgs.innerHTML = '';
    updateBadge(0);
}

window._tpvChatDestroy = destroy;

// ============================================================
//  CSS INJECTION
// ============================================================
function injectCSS(){
    var c = document.createElement('style');
    c.type = 'text/css';
    c.textContent = '#tpv-chat-fab{position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#00b894,#00cec9);color:#fff;font-size:0;border:none;cursor:pointer;box-shadow:0 4px 20px rgba(0,184,148,0.45);z-index:10000;display:flex;align-items:center;justify-content:center;transition:all .3s cubic-bezier(.4,0,.2,1);animation:tpv-fab-pulse 3s ease-in-out infinite}#tpv-chat-fab:hover{transform:scale(1.12);box-shadow:0 6px 28px rgba(0,184,148,0.6)}#tpv-chat-fab:active{transform:scale(.95)}#tpv-chat-fab svg{width:30px;height:30px}#tpv-chat-fab .tpv-fab-badge{position:absolute;top:-2px;right:-2px;min-width:18px;height:18px;border-radius:9px;background:#e74c3c;color:#fff;font-size:10px;font-weight:700;display:none;align-items:center;justify-content:center;padding:0 4px;border:2px solid #fff}@keyframes tpv-fab-pulse{0%,100%{box-shadow:0 4px 20px rgba(0,184,148,0.45)}50%{box-shadow:0 4px 30px rgba(0,184,148,0.7),0 0 0 8px rgba(0,184,148,0.1)}}#tpv-chat-panel{position:fixed;bottom:96px;right:24px;width:380px;max-width:calc(100vw - 48px);height:520px;max-height:calc(100vh - 120px);background:linear-gradient(180deg,#0f1923,#1a2332);border-radius:20px;box-shadow:0 12px 48px rgba(0,0,0,.4);z-index:10000;display:none;flex-direction:column;overflow:hidden;font-family:Segoe UI,system-ui,sans-serif;border:1px solid rgba(0,206,201,.15)}#tpv-chat-panel.open{display:flex;animation:tpv-panel-in .3s ease-out}@keyframes tpv-panel-in{from{opacity:0;transform:translateY(20px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}.tpvc-head{background:linear-gradient(135deg,#00b894,#00cec9);color:#fff;padding:14px 16px;display:flex;justify-content:space-between;align-items:center}.tpvc-head h3{margin:0;font-size:14px;font-weight:700;display:flex;align-items:center;gap:6px}.tpvc-head-sub{font-size:10px;opacity:.85;margin-top:2px;font-weight:400}.tpvc-role-badge{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;font-size:10px;font-weight:800;border:2px solid rgba(255,255,255,.7);margin-left:4px;transition:all .3s ease}.tpvc-role-label{font-size:10px;opacity:.8;transition:all .3s ease}.tpvc-status-dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-left:6px;transition:background .3s}.tpvc-status-dot.online{background:#2ecc71;box-shadow:0 0 6px rgba(46,204,113,.5)}.tpvc-status-dot.offline{background:#e74c3c;box-shadow:0 0 6px rgba(231,76,60,.5)}.tpvc-status-dot.connecting{background:#f39c12;box-shadow:0 0 6px rgba(243,156,18,.5);animation:tpv-dot-blink 1s infinite}@keyframes tpv-dot-blink{0%,100%{opacity:1}50%{opacity:.3}}.tpvc-close{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:18px;cursor:pointer;padding:6px 10px;border-radius:50%;transition:background .2s;width:30px;height:30px;display:flex;align-items:center;justify-content:center}.tpvc-close:hover{background:rgba(255,255,255,.35)}.tpvc-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;scroll-behavior:smooth}.tpvc-msgs::-webkit-scrollbar{width:4px}.tpvc-msgs::-webkit-scrollbar-thumb{background:rgba(0,206,201,.3);border-radius:4px}.tpvc-msg{max-width:88%;padding:10px 14px;border-radius:16px;font-size:13px;line-height:1.5;word-wrap:break-word;animation:tpv-msg-in .25s ease-out;white-space:pre-wrap}@keyframes tpv-msg-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}.tpvc-bot{background:rgba(0,184,148,.12);color:#d4edda;align-self:flex-start;border-bottom-left-radius:4px;border:1px solid rgba(0,184,148,.15)}.tpvc-user{background:linear-gradient(135deg,#00b894,#00cec9);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}.tpvc-system{background:rgba(243,156,18,.1);color:#f0d78c;align-self:center;border:1px solid rgba(243,156,18,.2);font-size:11px;text-align:center;padding:6px 14px;border-radius:12px;max-width:95%}.tpvc-typing{align-self:flex-start;color:#00cec9;font-size:12px;font-style:italic;padding:6px 14px;animation:tpv-typing-dot 1.5s infinite}@keyframes tpv-typing-dot{0%,100%{opacity:.4}50%{opacity:1}}.tpvc-input{display:flex;padding:10px 12px;border-top:1px solid rgba(0,206,201,.1);gap:8px;background:rgba(15,25,35,.8)}.tpvc-input input{flex:1;background:rgba(26,35,50,.9);border:1px solid rgba(0,206,201,.2);border-radius:24px;padding:10px 16px;color:#e0e0e0;font-size:13px;outline:none;transition:border-color .2s}.tpvc-input input::placeholder{color:#5a6a7a}.tpvc-input input:focus{border-color:#00cec9;box-shadow:0 0 0 2px rgba(0,206,201,.15)}.tpvc-input input:disabled{opacity:.5}.tpvc-input button{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#00b894,#00cec9);border:none;color:#fff;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;transition:all .2s;flex-shrink:0}.tpvc-input button:hover{transform:scale(1.08);box-shadow:0 3px 12px rgba(0,184,148,.4)}.tpvc-input button:disabled{opacity:.4;cursor:not-allowed;transform:none}.tpvc-suggestions{display:flex;flex-wrap:wrap;gap:6px;padding:2px 14px 6px 14px;align-self:flex-start;max-width:88%}.tpvc-sug-btn{background:rgba(0,206,201,.1);color:#00cec9;border:1px solid rgba(0,206,201,.25);border-radius:16px;padding:5px 12px;font-size:11px;cursor:pointer;transition:all .2s;font-family:inherit;white-space:nowrap}.tpvc-sug-btn:hover{background:rgba(0,206,201,.25);border-color:rgba(0,206,201,.5)}@media(max-width:400px){#tpv-chat-panel{width:calc(100vw - 16px);right:8px;bottom:80px;height:440px}}';
    document.head.appendChild(c);
}

// ============================================================
//  UTILIDADES
// ============================================================
var ROLE_COLORS = {desarrollador:'#9b59b6',administrador:'#e74c3c',supervisor:'#f39c12',vendedor:'#3498db',cliente:'#2ecc71'};
var ROLE_ICONS = {desarrollador:'D',administrador:'A',supervisor:'S',vendedor:'V',cliente:'C'};

function cleanText(t){
    if(!t) return '';
    return String(t).replace(/[^\x20-\x7E\n\r\t]/g, '');
}

function ce(t, a){
    var e = document.createElement(t);
    for(var k in a) if(a.hasOwnProperty(k)) e[k] = a[k];
    return e;
}

function fetchSafe(url, options, ms){
    ms = ms || REQ_TIMEOUT;
    return new Promise(function(resolve, reject){
        var ctrl = new AbortController();
        var timer = setTimeout(function(){ ctrl.abort(); reject(new Error('Timeout')); }, ms);
        var opts = options || {};
        opts.signal = ctrl.signal;
        fetch(url, opts).then(function(res){
            clearTimeout(timer);
            if(!res.ok){ reject(new Error('HTTP_' + res.status)); return; }
            res.text().then(function(text){
                try{ resolve(JSON.parse(text)); }
                catch(e){ reject(new Error('JSON_INVALID')); }
            }).catch(function(err){ clearTimeout(timer); reject(err); });
        }).catch(function(err){ clearTimeout(timer); reject(err); });
    });
}

// ============================================================
//  RENDER
// ============================================================
function renderMsg(text, isBot){
    var txt = cleanText(text);
    if(!txt) return;
    var d = ce('div', {className: 'tpvc-msg ' + (isBot ? 'tpvc-bot' : 'tpvc-user')});
    d.textContent = txt;
    var c = $('.tpvc-msgs');
    if(c){ c.appendChild(d); c.scrollTop = c.scrollHeight; }
    hist.push({text: txt, bot: isBot, ts: Date.now()});
}

function renderSystemMsg(text){
    var txt = cleanText(text);
    if(!txt) return;
    var d = ce('div', {className: 'tpvc-system'});
    d.textContent = txt;
    var c = $('.tpvc-msgs');
    if(c){ c.appendChild(d); c.scrollTop = c.scrollHeight; }
}

function renderSuggestions(suggestions){
    if(!suggestions || !suggestions.length) return;
    var c = $('.tpvc-msgs');
    if(!c) return;
    var old = c.querySelectorAll('.tpvc-suggestions');
    for(var i = 0; i < old.length; i++) old[i].remove();
    var wrap = ce('div', {className: 'tpvc-suggestions'});
    for(var i = 0; i < suggestions.length && i < 4; i++){
        (function(txt){
            var btn = ce('button', {className: 'tpvc-sug-btn', textContent: cleanText(txt)});
            btn.onclick = function(){ quickAsk(txt); };
            wrap.appendChild(btn);
        })(suggestions[i]);
    }
    c.appendChild(wrap);
    c.scrollTop = c.scrollHeight;
}

var lastAlertText = '';
function updateBadge(count, text){
    var b = $('.tpv-fab-badge');
    if(!b) return;
    b.textContent = count > 9 ? '9+' : count;
    b.style.display = count > 0 ? 'flex' : 'none';
    if(text){ lastAlertText = text; b.title = text; b.style.cursor = 'help'; }
    else if(lastAlertText){ b.title = lastAlertText; b.style.cursor = 'help'; }
}

function setStatusDot(status){
    var dot = $('.tpvc-status-dot');
    if(!dot) return;
    dot.className = 'tpvc-status-dot ' + (status || 'connecting');
}

function updateRoleDisplay(role){
    if(!role) return;
    currentRole = role;
    var color = ROLE_COLORS[role] || '#3498db';
    var icon = ROLE_ICONS[role] || 'V';
    var badge = $('.tpvc-role-badge');
    var lbl = $('.tpvc-role-label');
    if(badge){ badge.textContent = icon; badge.style.borderColor = color; badge.style.color = color; }
    if(lbl){ lbl.textContent = role.charAt(0).toUpperCase() + role.slice(1); lbl.style.color = color; }
    // Informar al servidor del rol
    fetch('/api/ia/role', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: SID, role: role, user_name: currentUserName})
    }).catch(function(){});
}

// ============================================================
//  SALUDO CONTEXTUAL INMEDIATO (local, sin servidor)
// ============================================================
function getImmediateGreeting(role){
    var h = new Date().getHours();
    var saludo = 'Buenos dias';
    if(h >= 12 && h < 18) saludo = 'Buenas tardes';
    else if(h >= 18) saludo = 'Buenas noches';

    var nameStr = currentUserName ? ', ' + currentUserName : '';

    if(role === 'desarrollador'){
        return saludo + nameStr + '! Soy tu asistente IA.\n\nCargando datos del sistema...\n\nMientras tanto puedes escribir lo que necesites.';
    } else if(role === 'administrador'){
        return saludo + nameStr + '! Soy tu asistente IA.\n\nObteniendo resumen del negocio...\n\nPreguntame lo que necesites.';
    } else if(role === 'supervisor'){
        return saludo + nameStr + '! Soy tu asistente IA.\n\nCargando metricas de tu equipo...\n\nEscribe en lenguaje natural.';
    } else if(role === 'vendedor'){
        return saludo + nameStr + '! Soy tu asistente IA.\n\nCargando ventas del dia...\n\nPreguntame sobre productos, precios o stock.';
    } else {
        return saludo + nameStr + '! Bienvenido.\n\nBusca productos, consulta precios o pregunta lo que necesites.';
    }
}

function getRoleSuggestions(role){
    if(role === 'desarrollador') return ['estado del sistema', 'ventas de hoy', 'seguridad'];
    if(role === 'administrador') return ['resumen del dia', 'stock bajo', 'finanzas'];
    if(role === 'supervisor') return ['ventas de hoy', 'equipo', 'stock bajo'];
    if(role === 'vendedor') return ['ventas de hoy', 'cuanto cuesta X', 'stock bajo'];
    return ['que productos tienen', 'cuanto cuesta X', 'mis puntos'];
}

// ============================================================
//  ENVIAR MENSAJE
// ============================================================
async function send(){
    if(sending) return;
    var inp = $('.tpvc-input input');
    if(!inp) return;
    var q = inp.value.trim();
    if(!q) return;

    sending = true;
    inp.value = '';
    inp.disabled = true;

    renderMsg(q, false);
    var typing = ce('div', {className: 'tpvc-typing', textContent: 'Analizando...'});
    var msgs = $('.tpvc-msgs');
    if(msgs){ msgs.appendChild(typing); msgs.scrollTop = msgs.scrollHeight; }

    if(!serverReady){
        typing.textContent = 'Conectando con el servidor...';
        var connected = await tryConnect();
        if(!connected){
            if(typing.parentNode) typing.remove();
            renderMsg('El servidor no responde. Reintentaré en unos segundos...\n\nEscribe "ayuda" para ver opciones offline.', true);
            renderSuggestions(['ayuda', 'ventas de hoy', 'resumen']);
            sending = false;
            inp.disabled = false;
            inp.focus();
            scheduleReconnect();
            return;
        }
        typing.textContent = 'Analizando...';
    }

    try{
        var d = await fetchSafe('/api/ia/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: q, session_id: SID, role: currentRole, user_name: currentUserName})
        }, REQ_TIMEOUT);

        if(typing.parentNode) typing.remove();
        serverReady = true;
        retryCount = 0;
        setStatusDot('online');

        var ans = d.answer || d.response || null;
        if(!ans){
            renderMsg('No pude generar una respuesta. Intenta de nuevo.', true);
        } else {
            lastServerAnswer = ans;
            if(d.role && d.role !== currentRole) updateRoleDisplay(d.role);
            renderMsg(ans, true);
            if(d.suggestions && d.suggestions.length) renderSuggestions(d.suggestions);
        }
        updateBadge(0);
    } catch(e){
        if(typing.parentNode) typing.remove();
        if(retryCount < 2){
            retryCount++;
            renderSystemMsg('Reintentando (' + retryCount + '/2)...');
            setTimeout(function(){
                sending = false;
                inp.value = q;
                send();
            }, 1500);
            return;
        }
        retryCount = 0;
        setStatusDot('offline');
        serverReady = false;
        renderMsg('Error de conexión temporal. Intenta de nuevo en unos segundos.', true);
        scheduleReconnect();
    } finally {
        sending = false;
        inp.disabled = false;
        inp.focus();
    }
}

function quickAsk(q){
    var inp = $('.tpvc-input input');
    if(inp) inp.value = q;
    send();
}

// ============================================================
//  AUTO-RETRY CON BACKOFF
// ============================================================
async function tryConnect(){
    for(var i = 0; i < 3; i++){
        try{
            setStatusDot('connecting');
            var d = await fetchSafe('/api/ia/ping', null, 3000);
            if(d && (d.status === 'ok' || d.ia_module)){
                serverReady = true;
                setStatusDot('online');
                return true;
            }
        } catch(e){}
        await new Promise(function(r){ setTimeout(r, 500 * (i + 1)); });
    }
    return false;
}

function scheduleReconnect(){
    if(serverReady) return;
    if(retryTimer) clearTimeout(retryTimer);
    retryTimer = setTimeout(async function(){
        var ok = await tryConnect();
        if(ok){
            renderSystemMsg('Conexión restaurada');
            loadServerData();
        } else {
            scheduleReconnect();
        }
    }, 8000);
}

// ============================================================
//  DATOS DEL SERVIDOR (interaccion REAL con SQLite)
// ============================================================
function loadServerData(){
    // 1. Obtener status y rol real
    fetchSafe('/api/ia/status', null, 3000).then(function(d){
        if(d){
            if(d.current_role && d.current_role !== currentRole) updateRoleDisplay(d.current_role);
            if(d.current_user && !currentUserName) currentUserName = d.current_user;
            serverReady = true;
            setStatusDot('online');
        }
    }).catch(function(){});

    // 2. Obtener saludo REAL del servidor con datos de SQLite
    if(!greetingLoaded){
        fetchSafe('/api/ia/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: 'hola', session_id: SID, role: currentRole, user_name: currentUserName})
        }, 5000).then(function(d){
            if(greetingLoaded) return;
            var ans = d.answer || null;
            if(ans && ans.length > 30){
                var msgs = $('.tpvc-msgs');
                if(msgs){
                    // Reemplazar el saludo local con datos reales del servidor
                    var firstBot = msgs.querySelector('.tpvc-bot');
                    if(firstBot){
                        firstBot.textContent = cleanText(ans);
                    } else {
                        renderMsg(ans, true);
                    }
                    if(d.suggestions && d.suggestions.length) renderSuggestions(d.suggestions);
                    if(d.role && d.role !== currentRole) updateRoleDisplay(d.role);
                    greetingLoaded = true;
                    lastServerAnswer = ans;
                }
            }
        }).catch(function(){});
    }

    // 3. Alertas proactivas
    fetchAlerts();
}

function fetchAlerts(){
    fetchSafe('/api/ia/alerts?session_id=' + SID, null, 3000).then(function(d){
        var alerts = (d && d.alerts) || [];
        if(alerts.length > 0){
            var primerTexto = (alerts[0].title || 'Nueva alerta') + ': ' + (alerts[0].body || '');
            updateBadge(alerts.length, primerTexto);
            for(var i = 0; i < alerts.length && i < 2; i++){
                var a = alerts[i];
                if(a.body && !a._shown){
                    renderSystemMsg(a.title + ': ' + a.body);
                    a._shown = true;
                }
            }
        }
    }).catch(function(){});
}

// ============================================================
//  INIT
// ============================================================
function init(){
    if($('#tpv-chat-fab')) return;

    injectCSS();

    // Detectar rol y nombre del usuario logueado
    try{
        var stored = localStorage.getItem('tpv_user') || sessionStorage.getItem('tpv_user') || '';
        if(stored){
            try{
                var u = JSON.parse(stored);
                if(u && u.rol) currentRole = u.rol;
                if(u && u.nombre) currentUserName = u.nombre;
                if(u && u.username) currentUserName = currentUserName || u.username;
            } catch(ex){}
        }
    } catch(ex){}

    // FAB
    var fab = ce('button', {
        id: 'tpv-chat-fab',
        innerHTML: '<svg viewBox="0 0 24 24" fill="none"><path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H6V22L10 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white" opacity=".95"/><path d="M13 6L8.5 12.5H11.5L11 16L15.5 9.5H12.5L13 6Z" fill="#00b894" stroke="#00b894" stroke-width=".5" stroke-linejoin="round"/></svg><span class="tpv-fab-badge" style="display:none">0</span>',
        onclick: function(){
            var p = $('#tpv-chat-panel');
            if(!p) return;
            var wasOpen = p.classList.contains('open');
            p.classList.toggle('open');
            if(p.classList.contains('open')){
                var inp = $('.tpvc-input input');
                if(inp) inp.focus();
                updateBadge(0);
                // Al abrir, actualizar datos del servidor
                if(!wasOpen) { if(!serverReady) { setTimeout(loadServerData, 1000); } else { loadServerData(); } }
            }
        }
    });
    document.body.appendChild(fab);

    // PANEL
    var roleColor = ROLE_COLORS[currentRole] || '#6c757d';
    var roleIcon = ROLE_ICONS[currentRole] || 'U';
    var roleLabel = currentRole === 'cliente' ? 'Invitado' : currentRole.charAt(0).toUpperCase() + currentRole.slice(1);

    var panel = ce('div', {id: 'tpv-chat-panel'});
    panel.innerHTML =
        '<div class="tpvc-head"><div><h3><svg style="width:16px;height:16px" viewBox="0 0 24 24" fill="none"><path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H6V22L10 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white" opacity=".9"/><path d="M13 6L8.5 12.5H11.5L11 16L15.5 9.5H12.5L13 6Z" fill="#0f1923" stroke="#0f1923" stroke-width=".5"/></svg> TPV Smart <span class="tpvc-role-badge" style="border-color:' + roleColor + ';color:' + roleColor + '">' + roleIcon + '</span> <span class="tpvc-role-label" style="font-size:10px;opacity:.8">' + roleLabel + '</span><span class="tpvc-status-dot connecting"></span></h3><div class="tpvc-head-sub">IA on-device v1.0</div></div><button class="tpvc-close" onclick="document.getElementById(\'tpv-chat-panel\').classList.remove(\'open\')">&times;</button></div>' +
        '<div class="tpvc-msgs"></div>' +
        '<div class="tpvc-input"><input type="text" placeholder="Escribe lo que necesites..." autocomplete="off"><button>></button></div>';
    document.body.appendChild(panel);

    var input = panel.querySelector('.tpvc-input input');
    var btn = panel.querySelector('.tpvc-input button');
    if(input) input.addEventListener('keydown', function(e){ if(e.key === 'Enter'){ e.preventDefault(); send(); } });
    if(btn) btn.addEventListener('click', function(){ send(); });

    window._tpvQAsk = quickAsk;

    // SALUDO INMEDIATO (local, sin esperar)
    renderMsg(getImmediateGreeting(currentRole), true);
    renderSuggestions(getRoleSuggestions(currentRole));
    setStatusDot('connecting');

    // Cargar datos REALES del servidor en background
    setTimeout(function(){
        loadServerData();
    }, 600);

    // Auto-retry si no conecta
    setTimeout(function(){
        if(!serverReady) scheduleReconnect();
    }, 5000);

    // Alertas proactivas cada 30s
    alertsTimer = setInterval(fetchAlerts, 30000);
    // Vibrar FAB si hay alertas al abrir panel
    var fab = $('#tpv-chat-fab');
    if(fab && lastAlertText){
        fab.style.animation = 'none';
        fab.offsetHeight;
        fab.style.animation = 'tpv-fab-pulse 0.5s ease-in-out 3, tpv-fab-pulse 3s ease-in-out 0s infinite';
    }
}

// Ejecutar init cuando el DOM este listo
if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

})();
 
