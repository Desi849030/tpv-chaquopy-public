import os, sys, json, uuid
from flask import Flask, request, jsonify, send_file, send_from_directory

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# ========== IMPORTAR IA ==========
try:
    from ia_assistant_simple import ask_llm, process_question, chat
    IA_ACTIVA = True
    print("✅ IA simple cargada")
except:
    IA_ACTIVA = False
    print("⚠️ IA no disponible")

# ========== APP ==========
app = Flask(__name__)

# ========== ENDPOINTS ==========

@app.route('/api/auth/login', methods=['POST'])
def login():
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
    return jsonify({
        "id": 1,
        "role": "admin",
        "name": "Administrador"
    })

@app.route('/api/agent/identity', methods=['GET'])
def identity():
    return jsonify({
        "id": "agent_001",
        "name": "Asistente TPV",
        "version": "13.0.0",
        "status": "active",
        "capabilities": ["chat", "sales", "inventory"]
    })

@app.route('/api/agent/chat', methods=['POST'])
@app.route('/agent/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json(silent=True) or {}
        msg = data.get('mensaje', data.get('message', data.get('text', '')))
        
        if not msg:
            return jsonify({"reply": "¿En qué puedo ayudarte?", "status": "ok"})
        
        print(f"[CHAT] {msg}")
        
        # Usar IA o respuesta simple
        if IA_ACTIVA:
            respuesta = ask_llm(msg)
        else:
            respuesta = f"Echo: {msg}"
        
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
@app.route('/api/health', methods=['GET'])
def empty():
    return jsonify([])

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(f"[CATCH] /api/{path}")
    return jsonify({"status": "ok"})

# ========== SERVIR FRONTEND ==========
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Buscar archivos en orden
    posibles_rutas = [
        f"{base_dir}/app/src/main/assets/frontend/templates/{path}",
        f"{base_dir}/app/src/main/assets/frontend/static/{path}",
        f"{base_dir}/app/src/main/assets/frontend/{path}",
        f"{base_dir}/app/src/main/static/{path}",
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta) and os.path.isfile(ruta):
            return send_file(ruta)
    
    # Si no hay archivo, servir index.html
    index_path = f"{base_dir}/app/src/main/assets/frontend/templates/index.html"
    if os.path.exists(index_path):
        return send_file(index_path)
    
    return "TPV Smart - Servidor Activo", 200

if __name__ == '__main__':
    print("="*60)
    print("🚀 TPV SMART - SERVIDOR FINAL")
    print("="*60)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"✅ IA: {'ACTIVA' if IA_ACTIVA else 'NO DISPONIBLE'}")
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=False)
