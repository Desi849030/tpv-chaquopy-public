import os, sys, json, uuid
from datetime import datetime

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

from flask import Flask, request, jsonify, send_file

# Importar ia_assistant - usa respuestas inteligentes sin LLM pesado
try:
    from ia_assistant import process_question, chat, get_default_response
    print("✅ ia_assistant cargado (modo inteligente sin LLM pesado)")
    IA_ACTIVA = True
except ImportError as e:
    print(f"⚠️ ia_assistant no disponible: {e}")
    IA_ACTIVA = False
    def chat(msg, sid="default", role="admin"):
        return {"response": f"Echo: {msg}"}

app = Flask(__name__, static_url_path='/static', static_folder=f"{base_dir}/app/src/main/static")

@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({
        "success": True,
        "token": "bypass_token",
        "user": {"id": 1, "role": "admin", "name": "Administrador"}
    })

@app.route('/api/auth/me', methods=['GET'])
def me():
    return jsonify({"id": 1, "role": "admin", "name": "Administrador"})

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    return jsonify({"valid": True})

@app.route('/api/agent/identity', methods=['GET'])
def agent_identity():
    return jsonify({
        "id": "agent_tpv_001",
        "name": "Asistente TPV Smart",
        "version": "13.0.0",
        "status": "active",
        "mode": "offline_ligero",
        "capabilities": ["chat", "sales", "inventory", "analytics"],
        "features": {
            "chat": True,
            "analytics": True,
            "inventory": True,
            "sales": True
        }
    })

@app.route('/api/agent/chat', methods=['POST'])
@app.route('/agent/chat', methods=['POST'])
def agent_chat():
    try:
        data = request.get_json(silent=True) or {}
        msg = data.get('mensaje', data.get('message', data.get('text', '')))
        
        if not msg:
            return jsonify({"reply": "¿En qué puedo ayudarte?", "status": "ok"})
        
        print(f"💬 Usuario: {msg}")
        
        if IA_ACTIVA:
            # Usar la IA inteligente sin LLM pesado
            session_id = data.get('session_id', 'default')
            role = data.get('role', 'admin')
            
            # Usar process_question que tiene respuestas inteligentes
            try:
                result = process_question(session_id, msg, role, "Usuario")
                respuesta = result.get('answer', '')
            except:
                # Fallback a chat simple
                result = chat(msg, session_id, role)
                respuesta = result.get('response', '')
        else:
            # Respuesta simple
            respuesta = f"Pregunta recibida: {msg}\n(Modo sin IA)"
        
        print(f"🤖 Respuesta: {respuesta[:100]}...")
        
        return jsonify({
            "reply": respuesta,
            "response": respuesta,
            "message": respuesta,
            "text": respuesta,
            "status": "ok",
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "reply": "Error al procesar. Intenta de nuevo.",
            "status": "error"
        })

@app.route('/api/catalogo', methods=['GET'])
@app.route('/api/ventas/totales', methods=['GET'])
@app.route('/api/ventas/hoy', methods=['GET'])
@app.route('/api/metrics', methods=['GET'])
@app.route('/api/publico/catalogo', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def datos_vacios():
    if request.path == '/api/health':
        return jsonify({"status": "ok", "version": "13.0.0"})
    return jsonify([])

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(f"🔄 Ruta: /api/{path}")
    return jsonify({"status": "ok"})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Buscar index.html
    index_paths = [
        f"{base_dir}/app/src/main/assets/frontend/templates/index.html",
        f"{base_dir}/app/src/main/static/index.html",
        f"{base_dir}/static/index.html",
    ]
    for idx_path in index_paths:
        if os.path.exists(idx_path):
            return send_file(idx_path)
    
    return """
    <html>
    <head><title>TPV Smart - IA Offline Ligera</title></head>
    <body style="text-align:center;padding:40px;font-family:sans-serif;background:#1a1a2e;color:white;">
        <h1 style="color:#00d4ff;">🤖 TPV Smart v13.0</h1>
        <p style="color:#00ff88;">✅ IA Inteligente Activada (sin LLM pesado)</p>
        <p style="color:#ffd700;">🔓 Modo Bypass</p>
        <div style="background:#16213e;padding:20px;border-radius:10px;display:inline-block;">
            <p>📱 Usuario: CUALQUIERA</p>
            <p>🔑 Contraseña: CUALQUIERA</p>
        </div>
        <p style="color:#666;margin-top:30px;">IA: Respuestas inteligentes predefinidas</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("="*60)
    print("🤖 TPV - IA INTELIGENTE SIN LLM PESADO")
    print("="*60)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"✅ IA Activa: {IA_ACTIVA}")
    print(f"📦 Modelo: NO LLM (usa reglas inteligentes)")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
