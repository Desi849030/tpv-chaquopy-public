import os, sys, threading

# Configurar rutas y variables de entorno para la IA
base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
os.environ['LLAMA_CPP_LIB'] = f"{base_dir}/agent_env/lib/python3.14/site-packages/llama_cpp/lib/libllama.so"
os.environ['LD_LIBRARY_PATH'] = f"{base_dir}/agent_env/lib/python3.14/site-packages/llama_cpp/lib/:" + os.environ.get('LD_LIBRARY_PATH', '')
os.environ['PYTHONPATH'] = f"{base_dir}/app/src/main/python"

# Añadir ruta de Python
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# Importar tu app original INTACTA
from app import app

# Importar la IA y Flask
from ia_assistant import ask_llm
from flask import request, jsonify, session, g

# Inyectar el Middleware (Bypass + Chat IA)
@app.before_request
def bypass_definitivo():
    if request.method == 'OPTIONS': 
        return '', 204
        
    # Bypass de Login y Sesión
    if request.path == '/api/auth/login':
        return jsonify({"success": True, "token": "admin_bypass", "user": {"id": 1, "role": "admin", "name": "Dev"}})
    if request.path == '/api/auth/me':
        return jsonify({"id": 1, "role": "admin", "name": "Dev"})
        
    # Inyectar sesión para evitar 401
    g.user = {"id": 1, "role": "admin"}
    session["user_id"] = 1
    session["role"] = "admin"
    
    # Interceptar Chat IA
    if '/agent/chat' in request.path:
        data = request.get_json(silent=True) or {}
        msg = data.get('mensaje', data.get('message', data.get('text', '')))
        if not msg: 
            msg = request.data.decode('utf-8')
        
        print(f"[IA] Pregunta: {msg}")
        resp = ask_llm(msg)
        print(f"[IA] Respuesta: {resp}")
        return jsonify({"reply": resp, "response": resp, "message": resp, "text": resp, "status": "ok"})

if __name__ == '__main__':
    print("Arrancando TPV con IA y Bypass inyectados (app.py intacto)...")
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=False)
