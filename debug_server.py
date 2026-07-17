import os, sys, json, uuid
from flask import Flask, request, jsonify, send_file, send_from_directory

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# Crear app Flask directamente
app = Flask(__name__, 
    static_folder=os.path.join(base_dir, "app/src/main/static"),
    static_url_path='/static')

# Importar ia_assistant
try:
    from ia_assistant import chat, process_question
    IA_AVAILABLE = True
    print("[OK] IA disponible")
except Exception as e:
    print(f"[ERROR] IA no disponible: {e}")
    IA_AVAILABLE = False
    def chat(msg, sid="default", role="admin"):
        return {"response": f"Echo: {msg}"}

@app.before_request
def log_request():
    print(f"\n{'='*60}")
    print(f"[REQUEST] {request.method} {request.path}")
    print(f"[HEADERS] {dict(request.headers)}")
    if request.data:
        try:
            print(f"[BODY] {request.data.decode('utf-8')[:500]}")
        except:
            print(f"[BODY] {request.data[:500]}")
    print(f"{'='*60}")

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    print(f"[LOGIN] Datos: {data}")
    return jsonify({
        "success": True,
        "token": "admin_bypass_token",
        "user": {
            "id": 1,
            "role": "admin",
            "name": "Administrador",
            "email": "admin@tpv.com"
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

@app.route('/api/auth/verify', methods=['GET', 'POST'])
def verify():
    return jsonify({"valid": True})

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    return jsonify({"success": True})

@app.route('/api/agent/identity', methods=['GET', 'POST'])
def agent_identity():
    return jsonify({
        "id": "agent_001",
        "name": "Asistente TPV",
        "version": "13.0.0",
        "status": "active",
        "capabilities": ["chat", "sales", "inventory", "analytics"],
        "role": "admin",
        "features": {
            "chat": True,
            "analytics": True,
            "inventory": True,
            "sales": True
        }
    })

@app.route('/api/agent/chat', methods=['POST'])
@app.route('/agent/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
@app.route('/chat', methods=['POST'])
def agent_chat():
    try:
        # Intentar obtener el mensaje en cualquier formato
        data = request.get_json(silent=True) or {}
        
        # Probar diferentes campos de mensaje
        msg = (
            data.get('mensaje') or 
            data.get('message') or 
            data.get('text') or 
            data.get('question') or 
            data.get('query') or
            data.get('input') or
            data.get('content')
        )
        
        # Si no hay mensaje en JSON, intentar con datos de formulario
        if not msg:
            msg = request.form.get('message', request.form.get('mensaje', ''))
        
        # Si aún no hay mensaje, intentar con datos planos
        if not msg and request.data:
            try:
                data = json.loads(request.data.decode('utf-8'))
                msg = data.get('message', data.get('mensaje', ''))
            except:
                msg = request.data.decode('utf-8')
        
        print(f"[CHAT] Mensaje recibido: '{msg}'")
        
        if not msg:
            return jsonify({
                "reply": "¿En qué puedo ayudarte?",
                "response": "¿En qué puedo ayudarte?",
                "status": "ok"
            })
        
        # Obtener sesión y rol
        session_id = data.get('session_id', data.get('sid', 'default'))
        role = data.get('role', 'admin')
        
        print(f"[CHAT] Session: {session_id}, Role: {role}")
        
        # Usar la IA
        if IA_AVAILABLE:
            try:
                # Intentar con process_question primero
                result = process_question(session_id, msg, role, "Usuario")
                answer = result.get('answer', '')
                print(f"[CHAT] Respuesta IA: {answer[:100]}...")
            except:
                # Fallback a chat
                result = chat(msg, session_id, role)
                answer = result.get('response', result.get('answer', ''))
                print(f"[CHAT] Respuesta chat: {answer[:100]}...")
        else:
            answer = f"Echo: {msg}"
            print(f"[CHAT] Modo echo: {answer}")
        
        # Devolver en el formato que espere el APK
        return jsonify({
            "reply": answer,
            "response": answer,
            "message": answer,
            "text": answer,
            "answer": answer,
            "status": "ok",
            "success": True
        })
        
    except Exception as e:
        print(f"[CHAT] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "reply": "Error al procesar tu pregunta. Intenta de nuevo.",
            "response": "Error al procesar tu pregunta.",
            "status": "error"
        })

@app.route('/api/assistant/status', methods=['GET'])
def assistant_status():
    return jsonify({
        "status": "active",
        "version": "13.0.0",
        "ia_available": IA_AVAILABLE,
        "mode": "bypass"
    })

@app.route('/api/assistant/chat', methods=['POST'])
def assistant_chat():
    data = request.get_json(silent=True) or {}
    msg = data.get('message', data.get('text', ''))
    if msg:
        result = chat(msg, 'default', 'admin')
        return jsonify({
            "response": result.get('response', ''),
            "status": "ok"
        })
    return jsonify({"response": "¿Qué necesitas?", "status": "ok"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "13.0.0"})

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_catchall(path):
    print(f"[CATCHALL] /api/{path}")
    if request.method == 'GET':
        return jsonify([])
    return jsonify({"success": True})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Servir archivos estáticos
    static_dir = os.path.join(base_dir, "app/src/main/static")
    assets_dir = os.path.join(base_dir, "app/src/main/assets/frontend")
    
    # Si es un archivo estático
    if path and '.' in path:
        for base in [static_dir, assets_dir, os.path.join(assets_dir, 'static')]:
            file_path = os.path.join(base, path)
            if os.path.exists(file_path):
                return send_file(file_path)
    
    # Buscar index.html
    index_paths = [
        os.path.join(assets_dir, "templates/index.html"),
        os.path.join(assets_dir, "index.html"),
        os.path.join(static_dir, "index.html"),
        os.path.join(base_dir, "app/src/main/templates/index.html"),
    ]
    for idx_path in index_paths:
        if os.path.exists(idx_path):
            print(f"[INDEX] Sirviendo: {idx_path}")
            return send_file(idx_path)
    
    # Si no hay index, mostrar estado
    return """
    <html>
    <head><title>TPV Smart v13.0</title></head>
    <body style="font-family: sans-serif; padding: 40px; text-align: center; background: #1a1a2e; color: white;">
        <h1 style="color: #00d4ff;">🤖 TPV Smart v13.0</h1>
        <p style="color: #00ff88;">✅ Servidor funcionando</p>
        <p style="color: #ffd700;">🔓 Modo Bypass Activo</p>
        <div style="margin-top: 30px; padding: 20px; background: #16213e; border-radius: 10px; display: inline-block;">
            <p>📱 Usuario: <strong style="color: #00ff88;">CUALQUIERA</strong></p>
            <p>🔑 Contraseña: <strong style="color: #00ff88;">CUALQUIERA</strong></p>
            <p style="margin-top: 10px; color: #00d4ff;">IA: %s</p>
        </div>
    </body>
    </html>
    """ % ("Disponible" if IA_AVAILABLE else "No disponible")

if __name__ == '__main__':
    print("="*60)
    print("🔧 SERVIDOR TPV - MODO BYPASS COMPLETO")
    print("="*60)
    print("📱 Usuario: CUALQUIERA")
    print("🔑 Contraseña: CUALQUIERA")
    print("="*60)
    print("✅ IA disponible:", IA_AVAILABLE)
    print("="*60)
    print("🌐 http://127.0.0.1:5050")
    print("📋 Logs en tiempo real")
    print("="*60)
    app.run(host='0.0.0.0', port=5050, debug=True, threaded=True)
