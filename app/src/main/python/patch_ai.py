import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from agente_apk import inicializar_ia, procesar_pregunta
from flask import request, jsonify

ia_estado = "inactiva"

@app.before_request
def interceptor_total():
    global ia_estado
    
    # SOLUCIÓN AL LOGIN: Dejar pasar las peticiones CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    # 1. BYPASS DE LOGIN
    if request.path == '/api/auth/login':
        return jsonify({"success": True, "token": "admin_bypass", "user": {"id": 1, "role": "admin", "name": "Dev"}})
    if request.path == '/api/auth/me':
        return jsonify({"id": 1, "role": "admin", "name": "Dev"})
        
    # 2. CHAT RÁPIDO
    if '/agent/chat' in request.path:
        if ia_estado != "lista":
            return jsonify({"reply": "Cargando IA. Espera 15 seg.", "response": "Cargando..."})
        
        data = request.get_json(silent=True) or {}
        msg = data.get('mensaje', data.get('message', data.get('msg', data.get('query', data.get('text', '')))))
        if not msg: msg = request.data.decode('utf-8')
            
        print(f"[IA] Pregunta: {msg}")
        respuesta = procesar_pregunta(msg)
        print(f"[IA] Respuesta: {respuesta}")
        
        return jsonify({
            "reply": respuesta, 
            "response": respuesta, 
            "message": respuesta,
            "text": respuesta,
            "respuesta": respuesta,
            "status": "ok"
        })

def preload_ia():
    global ia_estado
    ia_estado = "cargando"
    print("\n[IA] Buscando modelo...")
    ruta = os.path.expanduser('~/tpv-chaquopy-public/models/qwen-coder.gguf')
    if os.path.exists(ruta):
        res = inicializar_ia(ruta)
        ia_estado = "lista" if "Lista" in res else "error"
        print(f"[IA] Estado: {ia_estado}")
    else:
        ia_estado = "error"

threading.Thread(target=preload_ia).start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=False)
