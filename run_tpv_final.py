import os, sys, json, uuid
from datetime import datetime

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

from flask import Flask, request, jsonify, send_file, send_from_directory

# ========== IMPORTAR ASISTENTE SIMPLE ==========
try:
    from ia_assistant_simple import ask_llm, process_question, chat
    IA_ACTIVA = True
    print("✅ Asistente IA simple cargado")
except Exception as e:
    print(f"⚠️ Error cargando IA: {e}")
    IA_ACTIVA = False
    def ask_llm(p):
        return f"Procesando: {p}..."
    def process_question(sid, q, r="vendedor", u=""):
        return {"answer": f"Respuesta: {q}"}
    def chat(m, sid="default", r="vendedor"):
        return {"response": f"Echo: {m}"}

# ========== CREAR APP ==========
app = Flask(__name__)

# Configurar rutas estáticas
static_dir = os.path.join(base_dir, "app/src/main/static")
templates_dir = os.path.join(base_dir, "app/src/main/assets/frontend/templates")
assets_dir = os.path.join(base_dir, "app/src/main/assets/frontend")

# ========== ENDPOINTS ==========

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json(silent=True) or {}
    username = data.get('username', data.get('email', 'admin'))
    print(f"[LOGIN] Usuario: {username}")
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
        "name": "Administrador",
        "email": "admin@tpv.com"
    })

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    return jsonify({"valid": True})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({"success": True})

@app.route('/api/agent/identity', methods=['GET', 'POST'])
def agent_identity():
    return jsonify({
        "id": "agent_tpv_001",
        "name": "Asistente TPV Smart",
        "version": "13.0.0",
        "status": "active",
        "mode": "offline_simple",
        "capabilities": ["chat", "sales", "inventory", "prices"],
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
        
        print(f"[CHAT] Pregunta: {msg}")
        
        # Usar la IA
        respuesta = ask_llm(msg)
        print(f"[CHAT] Respuesta: {respuesta[:100]}...")
        
        return jsonify({
            "reply": respuesta,
            "response": respuesta,
            "message": respuesta,
            "text": respuesta,
            "status": "ok",
            "success": True
        })
        
    except Exception as e:
        print(f"[CHAT] Error: {e}")
        return jsonify({
            "reply": "Error al procesar. Intenta de nuevo.",
            "status": "error"
        })

@app.route('/api/catalogo', methods=['GET'])
@app.route('/api/metrics', methods=['GET'])
@app.route('/api/ventas/totales', methods=['GET'])
@app.route('/api/ventas/hoy', methods=['GET'])
@app.route('/api/publico/catalogo', methods=['GET'])
@app.route('/api/state', methods=['GET'])
@app.route('/api/i18n/dict', methods=['GET'])
def datos_vacios():
    return jsonify([])

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "13.0.0"})

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    print(f"[CATCH] /api/{path}")
    return jsonify({"status": "ok", "success": True})

# ========== SERVIR FRONTEND ==========
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    # Si es un archivo estático
    if path and '.' in path:
        # Buscar en varias ubicaciones
        search_paths = [
            os.path.join(static_dir, path),
            os.path.join(assets_dir, 'static', path),
            os.path.join(assets_dir, path),
            os.path.join(templates_dir, path)
        ]
        for file_path in search_paths:
            if os.path.exists(file_path):
                print(f"[STATIC] Sirviendo: {file_path}")
                return send_file(file_path)
        return "Archivo no encontrado", 404
    
    # Buscar index.html
    index_paths = [
        os.path.join(templates_dir, "index.html"),
        os.path.join(assets_dir, "index.html"),
        os.path.join(static_dir, "index.html"),
    ]
    for idx_path in index_paths:
        if os.path.exists(idx_path):
            print(f"[INDEX] Sirviendo: {idx_path}")
            return send_file(idx_path)
    
    # Si no hay index, mostrar estado
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TPV Smart v13.0</title>
        <meta charset="UTF-8">
        <style>
            body {{font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;}}
            .card {{background: rgba(255,255,255,0.05); border-radius: 20px; padding: 40px; text-align: center; border: 1px solid rgba(255,255,255,0.1); max-width: 500px;}}
            h1 {{color: #00d4ff; font-size: 2.5em;}}
            .status {{color: #00ff88; font-size: 1.2em; margin: 20px 0;}}
            .badge {{display: inline-block; padding: 5px 15px; border-radius: 20px; background: #00ff88; color: #1a1a2e; margin: 5px;}}
            .badge.ia {{background: #ff6b6b; color: white;}}
            .info {{background: rgba(0,0,0,0.3); border-radius: 10px; padding: 15px; margin: 20px 0; text-align: left;}}
            .info-item {{padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05);}}
            .label {{color: #888;}}
            .value {{color: #00d4ff; float: right;}}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 TPV Smart v13.0</h1>
            <div class="status">✅ Servidor Funcionando</div>
            <div>
                <span class="badge">🔓 BYPASS</span>
                <span class="badge ia">IA: {'✅' if IA_ACTIVA else '❌'}</span>
            </div>
            <div class="info">
                <div class="info-item"><span class="label">📱 Usuario:</span> <span class="value">CUALQUIERA</span></div>
                <div class="info-item"><span class="label">🔑 Contraseña:</span> <span class="value">CUALQUIERA</span></div>
                <div class="info-item"><span class="label">🌐 Puerto:</span> <span class="value">5050</span></div>
                <div class="info-item"><span class="label">🤖 IA:</span> <span class="value">{'Activa' if IA_ACTIVA else 'No disponible'}</span></div>
            </div>
            <p style="color: #666; font-size: 0.9em;">Servidor TPV - Modo Offline</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("="*60)
    print("🤖 TPV SMART v13.0 - SERVIDOR FINAL")
    print("="*60)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"✅ IA Activa: {IA_ACTIVA}")
    print("="*60)
    print(f"🌐 http://127.0.0.1:5050")
    print(f"📁 Directorio: {base_dir}")
    print("="*60)
    
    # Ejecutar en modo debug
    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)
