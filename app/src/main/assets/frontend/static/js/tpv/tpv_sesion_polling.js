// tpv_sesion_polling.js — Sesión, logout, polling de pedidos
async function auth_logout() {
    if (!confirm('¿Cerrar sesión?')) return;

    // v6.25: Limpiar chat IA ANTES de cualquier otra cosa (cancela timers/fetches)
    if (typeof window._tpvChatDestroy === 'function') {
        try { window._tpvChatDestroy(); } catch(e) {}
    }

    // Cerrar SSE primero
    if (_sseConn) { try { _sseConn.close(); } catch(e){} _sseConn = null; }
    if (AUTH.pollingNotif) { clearInterval(AUTH.pollingNotif); AUTH.pollingNotif = null; }
    // Limpiar polling de vendedores si existe
    if (window._vendPolling) { clearInterval(window._vendPolling); window._vendPolling = null; }

    // Auto-backup con TIMEOUT de 3s MAXIMO (no bloquea el logout)
    try {
        showToast('💾 Guardando respaldo...', 'info');
        var backupCtrl = new AbortController();
        setTimeout(function(){ backupCtrl.abort(); }, 3000);
        await fetch('/api/auth/auto-backup', { method:'POST', credentials:'same-origin', signal: backupCtrl.signal });
    } catch(e) {
        // Timeout o error - no importa, continuar con el logout
    }

    // Logout del servidor (con timeout)
    try {
        var logoutCtrl = new AbortController();
        setTimeout(function(){ logoutCtrl.abort(); }, 2000);
        await fetch('/api/auth/logout', { method:'POST', signal: logoutCtrl.signal });
    } catch(e) {}

    // Limpiar panel debug al cerrar sesión
    if (typeof window._dbg_limpiar === 'function') window._dbg_limpiar();
    AUTH.usuario = null;
    localStorage.removeItem("tpv_rol");
    localStorage.removeItem("tpv_user");
    localStorage.removeItem("tpv_rol");
    localStorage.removeItem("tpv_user");
    // Resetear chat IA a Usuario
    if (typeof updateRoleDisplay === "function") updateRoleDisplay("cliente");
    _prevN = -1;

    document.getElementById('user-bar')?.classList.add('d-none');
    document.getElementById('notif-bell-wrap')?.classList.add('d-none');

    document.querySelectorAll('#main-nav-tabs li, #main-nav-tabs .nav-item').forEach(el => {
        el.style.display = '';
    });

    const ls = document.getElementById('login-screen');
    ls.classList.remove('d-none');
    ls.style.opacity = '0';
    requestAnimationFrame(() => { ls.style.transition = 'opacity .28s'; ls.style.opacity = '1'; });

    const appDiv = document.getElementById('tpv-app');
    if (appDiv) appDiv.style.display = 'none';

    document.getElementById('login-error').style.display  = 'none';
    document.getElementById('login-hint').style.display   = 'none';
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('login-username').focus();
}

// ══════════════════════════════════════════════════════════════
//  CAMPANA — POLLING PEDIDOS (cada 8 s)
// ══════════════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════════════
//  SSE — Server-Sent Events (reemplaza polling de 8 s)
// ══════════════════════════════════════════════════════════════
let _prevN = -1;
let _sseConn = null;

function _iniciarPolling() {
    // Limpiar conexión anterior si existe
    if (_sseConn) { try { _sseConn.close(); } catch(e){} _sseConn = null; }
    _prevN = -1;

    // Usar SSE si el navegador lo soporta
    if (typeof EventSource !== 'undefined') {
        _sseConn = new EventSource('/api/sse');

        _sseConn.onmessage = (e) => {
            try {
                const ev = JSON.parse(e.data);
                if (ev.tipo === 'pedido_nuevo' || ev.tipo === 'pedidos_update') {
                    _actualizarBadgePedidos(ev.pendientes || 0, ev.nuevos || 0);
                } else if (ev.tipo === 'venta_nueva') {
                    // Admin recibe ventas en tiempo real
                    if (window.AUTH?.usuario?.rol === 'administrador' || window.AUTH?.usuario?.rol === 'desarrollador') {
                        _admin_renderVendedores && _admin_renderVendedores(new Date().toISOString().split('T')[0]);
                    }
                } else if (ev.tipo === 'stock_update') {
                    window._adminGeneral = null; // invalidar caché
                }
            } catch(e2) {}
        };

        _sseConn.onerror = () => {
            // Si SSE falla, fallback a polling cada 15 s
            if (_sseConn) { _sseConn.close(); _sseConn = null; }
            if (!AUTH.pollingNotif) {
                AUTH.pollingNotif = setInterval(_pollPedidos, 15050);
                _pollPedidos();
            }
        };

        // Primera carga inmediata
        _pollPedidos();
    } else {
        // Navegador sin SSE: polling clásico 8 s
        AUTH.pollingNotif = setInterval(_pollPedidos, 8000);
        _pollPedidos();
    }
}

function _actualizarBadgePedidos(n, nuevos) {
    const badge = document.getElementById('bell-badge');
    const btn   = document.querySelector('.bell-btn');
    if (badge) { badge.textContent = n; badge.classList.toggle('d-none', n === 0); }
    if (btn)   btn.classList.toggle('ring', n > 0);
    const tb = document.getElementById('tienda-pedidos-badge');
    if (tb) { tb.textContent = n; tb.classList.toggle('d-none', n === 0); }
    if (nuevos > 0) _toastPedido(nuevos);
    _prevN = n;
}

async function _pollPedidos() {
    if (!AUTH.usuario) return;
    try {
        const r    = await fetch('/api/pedidos?estado=pendiente', { signal: AbortSignal.timeout(4000) });
        if (!r.ok) return;
        const data = await r.json();
        const n    = (data.pedidos || []).length;
        const nuevos = (_prevN >= 0 && n > _prevN) ? n - _prevN : 0;
        _actualizarBadgePedidos(n, nuevos);
    } catch(e) {}
}

function _toastPedido(cant) {
    document.querySelector('.toast-ped')?.remove();
    const t = document.createElement('div');
    t.className = 'toast-ped';
    t.innerHTML = `<div style="font-size:1.7rem">🔔</div>
        <div><div class="fw-bold">${cant} pedido${cant>1?'s':''} nuevo${cant>1?'s':''}</div>
        <div class="text-muted" style="font-size:.82rem">Toca para ver</div></div>
        <button onclick="this.closest('.toast-ped').remove();document.getElementById('tienda-tab')?.click()"
                style="background:none;border:none;cursor:pointer;font-size:1.1rem;color:#94a3b8">✕</button>`;
    document.body.appendChild(t);
    setTimeout(() => t?.remove(), 7000);
}

