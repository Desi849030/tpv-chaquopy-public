import os, sys, json, uuid
from flask import Flask, request, jsonify, send_file, send_from_directory

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# ========== IMPORTAR IA ==========
try:
    from ia_assistant_simple import ask_llm
    IA_ACTIVA = True
    print("✅ IA cargada")
except:
    IA_ACTIVA = False
    def ask_llm(msg):
        return f"Procesando: {msg}"

# ========== APP CON STATIC FOLDER ==========
app = Flask(__name__, 
    static_folder=f"{base_dir}/app/src/main/static",
    static_url_path='/static'
)

# ========== ENDPOINTS API ==========

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json(silent=True) or {}
    username = data.get('username', data.get('email', 'admin'))
    print(f"[LOGIN] {username}")
    return jsonify({
        "success": True,
        "token": f"token_{uuid.uuid4().hex[:8]}",
        "user": {
            "id": 1,
            "role": "admin",
            "name": "Administrador",
            "email": "admin@tpv.com",
            "username": username
        }
    })

@app.route('/api/auth/me', methods=['GET'])
def me():
    return jsonify({"id": 1, "role": "admin", "name": "Administrador"})

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    return jsonify({"valid": True})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({"success": True})

@app.route('/api/agent/identity', methods=['GET'])
def identity():
    return jsonify({
        "id": "agent_001",
        "name": "Asistente TPV",
        "version": "13.0.0",
        "status": "active",
        "capabilities": ["chat", "sales", "inventory"],
        "features": {"chat": True, "analytics": True}
    })

@app.route('/api/agent/chat', methods=['POST'])
@app.route('/agent/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        msg = data.get('mensaje', data.get('message', data.get('text', '')))
        
        if not msg:
            return jsonify({"reply": "¿En qué puedo ayudarte?", "status": "ok"})
        
        print(f"[CHAT] {msg}")
        respuesta = ask_llm(msg)
        print(f"[RESP] {respuesta[:50]}...")
        
        return jsonify({
            "reply": respuesta,
            "response": respuesta,
            "message": respuesta,
            "text": respuesta,
            "status": "ok",
            "success": True
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"reply": "Error", "status": "error"})

@app.route('/api/catalogo', methods=['GET'])
@app.route('/api/ventas/totales', methods=['GET'])
@app.route('/api/ventas/hoy', methods=['GET'])
@app.route('/api/metrics', methods=['GET'])
@app.route('/api/publico/catalogo', methods=['GET'])
@app.route('/api/state', methods=['GET'])
@app.route('/api/health', methods=['GET'])
@app.route('/api/i18n/dict', methods=['GET'])
def empty():
    if request.path == '/api/health':
        return jsonify({"status": "ok", "version": "13.0.0"})
    if request.path == '/api/i18n/dict':
        return jsonify({})
    return jsonify([])

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    print(f"[CATCH] /api/{path}")
    return jsonify({"status": "ok", "success": True})

# ========== SERVIR FRONTEND ==========
@app.route('/')
@app.route('/<path:path>')
def serve(path=''):
    # Si es un archivo con extensión, servir desde static
    if path and '.' in path:
        static_path = f"{base_dir}/app/src/main/static/{path}"
        if os.path.exists(static_path):
            return send_file(static_path)
        return "Archivo no encontrado", 404
    
    # Servir index.html
    index_path = f"{base_dir}/app/src/main/assets/frontend/templates/index.html"
    if os.path.exists(index_path):
        return send_file(index_path)
    
    return "TPV Smart v13.0", 200

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV SMART - SERVIDOR DEFINITIVO")
    print("="*60)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"✅ IA: {'ACTIVA' if IA_ACTIVA else 'NO DISPONIBLE'}")
    print(f"📁 Static: {app.static_folder}")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
