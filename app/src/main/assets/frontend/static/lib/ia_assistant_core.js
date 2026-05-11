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
