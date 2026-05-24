// ══════════════════════════════════════════════════════════════
//  TPV AGENT — Asistente IA Conversacional v7.0
// ══════════════════════════════════════════════════════════════
const TPV_AGENT = {
    activo: false,
    panel: null,
    rol: null,
    init(rol) {
        this.rol = rol;
        if (document.getElementById('agent-container')) return;
        const container = document.createElement('div');
        container.id = 'agent-container';
        container.innerHTML = `
            <div id="agent-btn" onclick="TPV_AGENT.toggle()" style="position:fixed;bottom:20px;right:20px;z-index:9999;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#5b21b6);box-shadow:0 4px 20px rgba(124,58,237,0.4);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform 0.2s;font-size:24px;color:white;">🤖</div>
            <div id="agent-panel" style="position:fixed;bottom:90px;right:20px;z-index:9998;width:320px;max-width:90vw;height:400px;max-height:60vh;background:white;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,0.15);display:none;flex-direction:column;overflow:hidden;border:1px solid #e2e8f0;">
                <div style="padding:12px 16px;background:#f8fafc;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;"><strong>🤖 Asistente TPV</strong><button onclick="TPV_AGENT.toggle()" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:#64748b;">×</button></div>
                <div id="agent-messages" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;"></div>
                <div style="padding:12px;border-top:1px solid #e2e8f0;display:flex;gap:8px;">
                    <input id="agent-input" type="text" placeholder="Pregunta algo..." style="flex:1;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;outline:none;" onkeypress="if(event.key==='Enter')TPV_AGENT.send()">
                    <button onclick="TPV_AGENT.send()" style="background:#7c3aed;color:white;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;">➤</button>
                </div>
            </div>`;
        document.body.appendChild(container);
        this.addMessage('¡Hola! Soy tu asistente TPV. ¿En qué puedo ayudarte?', 'agent');
        this.activo = true;
    },
    toggle() {
        const panel = document.getElementById('agent-panel');
        panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
        if (panel.style.display === 'flex') document.getElementById('agent-input')?.focus();
    },
    addMessage(text, from) {
        const container = document.getElementById('agent-messages');
        const div = document.createElement('div');
        const isUser = from === 'user';
        div.style.cssText = `padding:10px;border-radius:12px;max-width:85%;font-size:0.9rem;background:${isUser?'#7c3aed':'#f1f5f9'};color:${isUser?'white':'#334155'};align-self:${isUser?'flex-end':'flex-start'};margin-bottom:4px;`;
        div.innerText = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },
    async send() {
        const input = document.getElementById('agent-input');
        const msg = input.value.trim();
        if (!msg) return;
        this.addMessage(msg, 'user');
        input.value = '';
        try {
            const res = await fetch('/api/agent/query', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({query:msg, rol:this.rol})
            });
            const data = await res.json();
            setTimeout(() => this.addMessage(data.respuesta || 'Error', 'agent'), 400);
            if (data.tipo === 'action' && data.data?.target) {
                setTimeout(() => document.getElementById(data.data.target)?.click(), 600);
            }
        } catch(e) {
            this.addMessage('Error de conexión', 'agent');
        }
    }
};
document.addEventListener('DOMContentLoaded', () => {
    if (window.AUTH?.usuario) TPV_AGENT.init(window.AUTH.usuario.rol);
});
