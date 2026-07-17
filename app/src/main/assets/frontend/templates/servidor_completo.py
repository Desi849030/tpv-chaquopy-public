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

# ========== APP ==========
app = Flask(__name__)

# Configurar rutas de archivos estáticos
STATIC_DIRS = [
    f"{base_dir}/app/src/main/assets/frontend/static",
    f"{base_dir}/app/src/main/assets/frontend",
    f"{base_dir}/app/src/main/static",
    f"{base_dir}/static",
]

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
        "capabilities": ["chat", "sales", "inventory", "analytics"],
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

# ========== SERVIR ARCHIVOS ESTÁTICOS ==========

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Sirve archivos estáticos desde múltiples ubicaciones"""
    for static_dir in STATIC_DIRS:
        file_path = os.path.join(static_dir, filename)
        if os.path.exists(file_path):
            print(f"[STATIC] {filename} -> {file_path}")
            return send_file(file_path)
    
    # Buscar en subcarpetas comunes
    subdirs = ['css', 'js', 'lib', 'fonts', 'app3', 'modules']
    for subdir in subdirs:
        for static_dir in STATIC_DIRS:
            file_path = os.path.join(static_dir, subdir, filename)
            if os.path.exists(file_path):
                print(f"[STATIC] {filename} -> {file_path}")
                return send_file(file_path)
    
    print(f"[STATIC] 404: {filename}")
    return "Archivo no encontrado", 404

@app.route('/')
@app.route('/<path:path>')
def serve_root(path=''):
    # Si es un archivo con extensión, intentar servirlo
    if path and '.' in path:
        # Buscar en directorios estáticos
        for static_dir in STATIC_DIRS:
            file_path = os.path.join(static_dir, path)
            if os.path.exists(file_path):
                return send_file(file_path)
        
        # Buscar en templates
        templates_dir = f"{base_dir}/app/src/main/assets/frontend/templates"
        file_path = os.path.join(templates_dir, path)
        if os.path.exists(file_path):
            return send_file(file_path)
        
        return "Archivo no encontrado", 404
    
    # Servir index.html
    index_paths = [
        f"{base_dir}/app/src/main/assets/frontend/templates/index.html",
        f"{base_dir}/app/src/main/assets/frontend/index.html",
        f"{base_dir}/app/src/main/static/index.html",
    ]
    
    for idx_path in index_paths:
        if os.path.exists(idx_path):
            print(f"[INDEX] Sirviendo: {idx_path}")
            return send_file(idx_path)
    
    return """
    <html>
    <head><title>TPV Smart</title></head>
    <body style="background:#1a1a2e;color:white;text-align:center;padding:50px;">
        <h1>🤖 TPV Smart v13.0</h1>
        <p>✅ Servidor funcionando</p>
        <p>📱 Usuario: CUALQUIERA</p>
        <p>🔑 Contraseña: CUALQUIERA</p>
        <p style="color:#666;font-size:0.8em;">IA: {} | Puerto: 5050</p>
    </body>
    </html>
    """.format("Activa" if IA_ACTIVA else "No disponible")

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV SMART - SERVIDOR COMPLETO")
    print("="*60)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"✅ IA: {'ACTIVA' if IA_ACTIVA else 'NO DISPONIBLE'}")
    print(f"📁 Directorios estáticos:")
    for d in STATIC_DIRS:
        print(f"   - {d}")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
