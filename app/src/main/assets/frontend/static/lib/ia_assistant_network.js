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
    var typing = ce('div', {className: 'tpvc-typing', id: 'tpv-typing-el'});typing.innerHTML='<span class=tpvc-dot></span><span class=tpvc-dot></span><span class=tpvc-dot></span>';
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
    // Draggable para FAB y offline indicator
    function makeDraggable(el){
      if(!el)return;
      var sx,sy,ox,oy,moving=false;
      el.addEventListener('touchstart',function(e){
        if(e.target.closest('.tpvc-close,.tpvc-input'))return;
        moving=true;var t=e.touches[0];sx=t.clientX;sy=t.clientY;
        var r=el.getBoundingClientRect();ox=r.left;oy=r.top;
        el.style.transition='none';el.style.zIndex='10001';
      },{passive:true});
      el.addEventListener('touchmove',function(e){
        if(!moving)return;e.preventDefault();
        var t=e.touches[0];var dx=t.clientX-sx;var dy=t.clientY-sy;
        var nx=ox+dx;var ny=oy+dy;
        nx=Math.max(0,Math.min(nx,window.innerWidth-el.offsetWidth));
        ny=Math.max(0,Math.min(ny,window.innerHeight-el.offsetHeight));
        el.style.position='fixed';el.style.left=nx+'px';el.style.top=ny+'px';el.style.right='auto';el.style.bottom='auto';
        sx=t.clientX;sy=t.clientY;ox=nx;oy=ny;
      },{passive:false});
      el.addEventListener('touchend',function(){moving=false;el.style.transition='';el.style.zIndex='';});
      el.addEventListener('mousedown',function(e){
        if(e.target.closest('.tpvc-close,.tpvc-input'))return;
        moving=true;sx=e.clientX;sy=e.clientY;
        var r=el.getBoundingClientRect();ox=r.left;oy=r.top;
        el.style.transition='none';el.style.zIndex='10001';
        e.preventDefault();
      });
      document.addEventListener('mousemove',function(e){
        if(!moving)return;
        var dx=e.clientX-sx;var dy=e.clientY-sy;
        var nx=ox+dx;var ny=oy+dy;
        nx=Math.max(0,Math.min(nx,window.innerWidth-el.offsetWidth));
        ny=Math.max(0,Math.min(ny,window.innerHeight-el.offsetHeight));
        el.style.position='fixed';el.style.left=nx+'px';el.style.top=ny+'px';el.style.right='auto';el.style.bottom='auto';
        sx=e.clientX;sy=e.clientY;ox=nx;oy=ny;
      });
      document.addEventListener('mouseup',function(){moving=false;el.style.transition='';el.style.zIndex='';});
    }
    setTimeout(function(){
      makeDraggable(document.getElementById('tpv-chat-fab'));
      makeDraggable(document.getElementById('offline-indicator'));
      makeDraggable(document.getElementById('ia-bubble-container'));
    },500);

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
 
