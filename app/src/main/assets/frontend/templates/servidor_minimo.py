from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>TPV Test</title></head>
    <body style="background:#1a1a2e;color:white;text-align:center;padding:50px;">
        <h1 style="color:#00d4ff;">✅ SERVIDOR FUNCIONANDO</h1>
        <p>Puerto 5050 activo</p>
        <button onclick="testChat()" style="padding:15px 30px;background:#00d4ff;border:none;border-radius:10px;cursor:pointer;">
            Probar Chat
        </button>
        <div id="resultado" style="margin-top:20px;background:#16213e;padding:20px;border-radius:10px;"></div>
        <script>
        async function testChat() {
            const div = document.getElementById('resultado');
            div.innerHTML = '⏳ Enviando...';
            try {
                const resp = await fetch('/api/agent/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: 'hola'})
                });
                const data = await resp.json();
                div.innerHTML = '✅ Respuesta: ' + JSON.stringify(data, null, 2);
            } catch(e) {
                div.innerHTML = '❌ Error: ' + e.message;
            }
        }
        </script>
    </body>
    </html>
    """

@app.route('/api/agent/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message', 'sin mensaje')
    print(f"📨 Chat recibido: {msg}")
    return jsonify({
        "reply": f"Recibí: '{msg}'",
        "status": "ok",
        "success": True
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    print(f"🔑 Login: {data}")
    return jsonify({
        "success": True,
        "token": "test_token",
        "user": {"id": 1, "role": "admin", "name": "Test"}
    })

@app.route('/api/agent/identity', methods=['GET'])
def identity():
    return jsonify({
        "id": "agent_001",
        "name": "Test Agent",
        "version": "1.0",
        "status": "active"
    })

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(f"📌 Ruta no definida: /api/{path}")
    return jsonify({"status": "ok", "path": path})

if __name__ == '__main__':
    print("="*60)
    print("🧪 SERVIDOR MÍNIMO DE PRUEBA")
    print("="*60)
    print("✅ Servidor corriendo en http://127.0.0.1:5050")
    print("📋 Abre esta URL en Chrome")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
