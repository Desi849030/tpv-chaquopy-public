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

