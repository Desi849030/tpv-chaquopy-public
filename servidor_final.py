import os
import sys
import uuid
from flask import Flask, send_file, send_from_directory, jsonify, request

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

app = Flask(__name__)

# ========== IA ==========
def ask_llm(msg):
    msg = msg.lower().strip()
    if 'ventas' in msg:
        return "📊 Las ventas de hoy son $1,234.56 en 15 transacciones."
    if 'stock' in msg:
        return "📦 Hay 1,523 productos en inventario."
    if 'precio' in msg or 'cuesta' in msg:
        return "💰 El café cuesta $2.50, el pan $1.50."
    if 'hola' in msg:
        return "👋 ¡Hola! Soy tu asistente TPV."
    return "🤔 Prueba con 'ventas', 'stock' o 'ayuda'."

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

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    return jsonify({"status": "ok"})

# ========== SERVIR ARCHIVOS ESTÁTICOS ==========
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Sirve archivos estáticos desde la ubicación correcta"""
    static_dir = f"{base_dir}/app/src/main/assets/frontend/static"
    file_path = os.path.join(static_dir, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path)
    
    # Buscar en subcarpetas
    for sub in ['css', 'js', 'lib', 'fonts']:
        file_path = os.path.join(static_dir, sub, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
    
    return "", 404

@app.route('/')
def index():
    index_path = f"{base_dir}/app/src/main/assets/frontend/templates/index.html"
    if os.path.exists(index_path):
        return send_file(index_path)
    return "Index no encontrado", 404

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV - BACKUP RESTAURADO")
    print("="*60)
    print("📱 Usuario: CUALQUIERA")
    print("🔑 Contraseña: CUALQUIERA")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
