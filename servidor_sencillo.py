import os
import sys
import uuid
from flask import Flask, send_file, jsonify, request

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

try:
    from ia_assistant_simple import ask_llm
    print("✅ IA cargada")
except:
    def ask_llm(msg): return f"Recibí: {msg}"
    print("⚠️ IA no disponible")

app = Flask(__name__)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', 'admin')
    print(f"✅ Login: {username}")
    return jsonify({
        "success": True,
        "token": f"token_{uuid.uuid4().hex[:8]}",
        "user": {"id": 1, "role": "admin", "name": "Administrador"}
    })

@app.route('/api/agent/identity', methods=['GET'])
def identity():
    return jsonify({
        "id": "agent_001",
        "name": "TPV Assistant",
        "version": "1.0",
        "status": "active"
    })

@app.route('/api/agent/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message', data.get('mensaje', ''))
    if not msg:
        return jsonify({"reply": "¿Qué necesitas?"})
    print(f"💬 {msg}")
    respuesta = ask_llm(msg)
    return jsonify({"reply": respuesta, "response": respuesta, "status": "ok"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return send_file(f"{base_dir}/app/src/main/assets/frontend/templates/index.html")

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV - VERSIÓN SIMPLE")
    print("="*60)
    print("📱 Usuario: CUALQUIERA")
    print("🔑 Contraseña: CUALQUIERA")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
