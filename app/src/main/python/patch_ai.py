import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from agente_apk import inicializar_ia, procesar_pregunta
from flask import request, jsonify, session

ia_estado = "inactiva"

@app.before_request
def bypass_and_intercept():
    global ia_estado
    
    # 1. BYPASS DE LOGIN Y SESIÓN
    if request.path == '/api/auth/login':
        return jsonify({"success": True, "token": "admin_token", "user": {"id": 1, "role": "admin", "name": "Admin"}})
    if request.path == '/api/auth/me':
        return jsonify({"id": 1, "role": "admin", "name": "Admin"})
    
    # Inyectamos sesión de admin para todas las demás rutas
    session['user_id'] = 1
    session['role'] = 'admin'

    # 2. INTERCEPTOR DE CHAT (Evita el error 405)
    if '/agent/chat' in request.path:
        if ia_estado != "lista":
            return jsonify({"reply": "La IA está cargando. Espera 15 segundos."})
        
        data = request.get_json(silent=True) or {}
        msg = data.get('message', data.get('msg', data.get('query', data.get('text', ''))))
        if not msg:
            msg = request.data.decode('utf-8')
            
        print(f"[IA] Pregunta: {msg}")
        respuesta = procesar_pregunta(msg)
        print(f"[IA] Respuesta: {respuesta}")
        return jsonify({"reply": respuesta, "response": respuesta, "message": respuesta})

def preload_ia():
    global ia_estado
    ia_estado = "cargando"
    print("\n[IA] Cargando modelo local (15 seg)...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    ruta = os.path.join(base_dir, 'models', 'qwen-coder.gguf')
    if not os.path.exists(ruta):
        ruta = os.path.join(os.environ.get('FILES_DIR', ''), 'qwen-coder.gguf')
        
    res = inicializar_ia(ruta)
    ia_estado = "lista" if "Lista" in res else "error"
    print(f"\n[IA] Estado: {ia_estado}\n")

threading.Thread(target=preload_ia).start()

def iniciar_servidor():
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=True)

if __name__ == '__main__':
    iniciar_servidor()
