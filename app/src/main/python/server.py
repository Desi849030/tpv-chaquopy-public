from flask import Flask, request, Response, stream_with_context
import threading
import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agente_apk import inicializar_ia, procesar_pregunta_stream

app = Flask(__name__)
ia_estado = "inactiva"
ia_error_msg = ""

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TPV Ultra Smart</title>
        <style>
            * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }
            body { margin: 0; padding: 0; background: #f0f2f5; height: 100vh; display: flex; justify-content: center; align-items: center; }
            .login-card { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 90%; max-width: 380px; }
            .brand { text-align: center; margin-bottom: 30px; }
            .brand h1 { color: #1a237e; margin: 0; font-size: 24px; font-weight: 800; }
            .brand p { color: #8e8e8e; margin: 5px 0 0; font-size: 14px; }
            .tabs { display: flex; background: #f0f2f5; padding: 5px; border-radius: 10px; margin-bottom: 25px; }
            .tab { flex: 1; text-align: center; padding: 10px; border-radius: 8px; font-weight: 600; color: #8e8e8e; cursor: pointer; transition: 0.3s; }
            .tab.active { background: white; color: #1a237e; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            .input-group { margin-bottom: 20px; position: relative; }
            .input-group label { display: block; color: #555; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
            .input-wrapper { display: flex; align-items: center; background: #f0f2f5; border-radius: 10px; padding: 0 15px; }
            .input-wrapper input { width: 100%; padding: 15px 0; background: transparent; border: none; outline: none; font-size: 16px; color: #333; }
            .toggle-pass { cursor: pointer; color: #8e8e8e; padding: 5px; user-select: none; }
            .btn-login { width: 100%; background: #1a237e; color: white; border: none; padding: 16px; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 10px; }
            
            /* CHAT FLOTANTE */
            #fab-btn { position: fixed; bottom: 25px; right: 25px; width: 56px; height: 56px; background: #1a237e; border-radius: 50%; box-shadow: 0 4px 12px rgba(26, 35, 126, 0.4); cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 9998; }
            #fab-btn svg { width: 28px; height: 28px; fill: white; }
            #chat-panel { position: fixed; bottom: 90px; right: 25px; width: 340px; height: 480px; background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 9999; overflow: hidden; }
            .chat-header { background: #1a237e; color: white; padding: 15px 20px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; }
            .chat-body { flex: 1; padding: 20px; overflow-y: auto; background: #f0f2f5; display: flex; flex-direction: column; gap: 12px; }
            .msg-bubble { max-width: 80%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; }
            .msg-user { align-self: flex-end; background: #1a237e; color: white; border-bottom-right-radius: 4px; }
            .msg-ai { align-self: flex-start; background: white; color: #333; border-bottom-left-radius: 4px; }
            .chat-footer { padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px; }
            .chat-footer input { flex: 1; padding: 12px 15px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 14px; }
            .chat-footer button { background: #1a237e; color: white; border: none; border-radius: 50%; width: 42px; height: 42px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        </style>
    </head>
    <body>
        <!-- LOGIN -->
        <div class="login-card">
            <div class="brand">
                <h1>TPV Ultra Smart</h1>
                <p>Acceso al Sistema</p>
            </div>
            <div class="tabs">
                <div class="tab active" onclick="selectTab(this)">Personal</div>
                <div class="tab" onclick="selectTab(this)">Cliente</div>
            </div>
            <div class="input-group">
                <label>Usuario</label>
                <div class="input-wrapper">
                    <input type="text" placeholder="admin">
                </div>
            </div>
            <div class="input-group">
                <label>Contraseña</label>
                <div class="input-wrapper">
                    <input type="password" id="pass" placeholder="********">
                    <span class="toggle-pass" onclick="togglePass()">
                        <svg id="eye" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </span>
                </div>
            </div>
            <button class="btn-login">ENTRAR</button>
        </div>

        <!-- CHAT IA -->
        <div id="fab-btn" onclick="toggleChat()">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/></svg>
        </div>
        <div id="chat-panel">
            <div class="chat-header">
                <span>Asistente Virtual</span>
                <button onclick="toggleChat()" style="background:none;border:none;color:white;font-size:20px;cursor:pointer;">✖</button>
            </div>
            <div class="chat-body" id="chat-body">
                <div class="msg-ai" id="initial-msg">Presione para activar la IA local.</div>
            </div>
            <div class="chat-footer">
                <input type="text" id="chat-input" placeholder="Escribe..." disabled>
                <button id="send-btn" disabled onclick="sendMessage()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>

        <script>
            function selectTab(el) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                el.classList.add('active');
            }
            function togglePass() {
                const input = document.getElementById('pass');
                input.type = input.type === 'password' ? 'text' : 'password';
            }

            let iaReady = false;
            function toggleChat() {
                const panel = document.getElementById('chat-panel');
                panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
                if (!iaReady && panel.style.display === 'flex') activateIA();
            }

            function activateIA() {
                document.getElementById('initial-msg').innerText = "Cargando motor IA...";
                fetch('/activar_ia').then(r => r.text()).then(checkStatus);
            }

            function checkStatus() {
                fetch('/estado_ia').then(r => r.text()).then(t => {
                    if (t === 'lista') {
                        iaReady = true;
                        document.getElementById('initial-msg').innerText = "¡IA Lista! ¿En qué puedo ayudarle?";
                        document.getElementById('chat-input').disabled = false;
                        document.getElementById('send-btn').disabled = false;
                    } else if (t === 'cargando') {
                        setTimeout(checkStatus, 2000);
                    } else {
                        document.getElementById('initial-msg').innerText = "Error al cargar. Revise Termux.";
                    }
                });
            }

            function addMsg(type) {
                const body = document.getElementById('chat-body');
                const div = document.createElement('div');
                div.className = 'msg-bubble ' + (type === 'user' ? 'msg-user' : 'msg-ai');
                body.appendChild(div);
                body.scrollTop = body.scrollHeight;
                return div;
            }

            async function sendMessage() {
                const input = document.getElementById('chat-input');
                const msg = input.value.trim();
                if (!msg || !iaReady) return;
                
                input.value = '';
                addMsg('user').innerText = msg;
                const aiBubble = addMsg('ai');
                aiBubble.innerText = '...';
                
                // Lógica de Streaming (Lee palabra por palabra)
                const response = await fetch('/chat_stream', {method: 'POST', body: msg});
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let text = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    text += decoder.decode(value);
                    aiBubble.innerText = text;
                    document.getElementById('chat-body').scrollTop = 999999;
                }
            }
            
            document.getElementById('chat-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/activar_ia')
def activar_ia():
    global ia_estado
    if ia_estado == "inactiva" or ia_estado == "error":
        ia_estado = "cargando"
        thread = threading.Thread(target=cargar_ia_background)
        thread.start()
    return "Iniciando"

def cargar_ia_background():
    global ia_estado, ia_error_msg
    try:
        if os.path.exists('models/qwen-coder.gguf'): ruta = 'models/qwen-coder.gguf'
        else: ruta = 'qwen-coder.gguf'
        
        resultado = inicializar_ia(ruta)
        ia_estado = "lista" if "Lista" in resultado else "error"
    except Exception as e:
        ia_estado = "error"

@app.route('/estado_ia')
def estado_ia(): return ia_estado

@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    user_input = request.data.decode('utf-8')
    if ia_estado == "lista":
        return Response(stream_with_context(procesar_pregunta_stream(user_input)), content_type='text/plain')
    return "Error: IA no lista."

def iniciar_servidor():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    iniciar_servidor()
