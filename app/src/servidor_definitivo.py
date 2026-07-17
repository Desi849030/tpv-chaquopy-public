import os
import sys
import uuid
import json
from flask import Flask, send_file, send_from_directory, jsonify, request

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# IA
try:
    from ia_assistant_simple import ask_llm
    print("✅ IA cargada")
except:
    def ask_llm(msg): return f"Recibí: {msg}"
    print("⚠️ IA no disponible")

app = Flask(__name__)

# ========== API ==========
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

@app.route('/api/auth/me', methods=['GET'])
def me():
    return jsonify({"id": 1, "role": "admin", "name": "Administrador"})

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    return jsonify({"valid": True})

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
    print(f"💬 Pregunta: {msg}")
    respuesta = ask_llm(msg)
    print(f"🤖 Respuesta: {respuesta[:50]}...")
    return jsonify({"reply": respuesta, "response": respuesta, "status": "ok"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/catalogo', methods=['GET'])
def catalogo():
    return jsonify([])

@app.route('/api/ventas/totales', methods=['GET'])
def ventas_totales():
    return jsonify([])

@app.route('/api/ventas/hoy', methods=['GET'])
def ventas_hoy():
    return jsonify([])

@app.route('/api/metrics', methods=['GET'])
def metrics():
    return jsonify([])

@app.route('/api/publico/catalogo', methods=['GET'])
def publico_catalogo():
    return jsonify([])

@app.route('/api/state', methods=['GET'])
def state():
    return jsonify({})

@app.route('/api/i18n/dict', methods=['GET'])
def i18n():
    return jsonify({})

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    print(f"📌 /api/{path}")
    return jsonify({"status": "ok"})

# ========== SERVIR TU DISEÑO ORIGINAL ==========
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Sirve archivos estáticos desde app/src/main/static/"""
    static_dir = f"{base_dir}/app/src/main/static"
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Archivo no encontrado", 404

@app.route('/')
def index():
    """Sirve tu index.html original sin modificar"""
    index_path = f"{base_dir}/app/src/main/assets/frontend/templates/index.html"
    if os.path.exists(index_path):
        return send_file(index_path)
    return "Index no encontrado", 404

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV - TU DISEÑO ORIGINAL")
    print("="*60)
    print("📱 Usuario: CUALQUIERA")
    print("🔑 Contraseña: CUALQUIERA")
    print("📁 Static: app/src/main/static/")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
