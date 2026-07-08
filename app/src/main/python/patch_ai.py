import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from agente_apk import inicializar_ia, procesar_pregunta
from flask import request, jsonify

ia_estado = "inactiva"

@app.before_request
def interceptor_total():
    global ia_estado
    
    # 1. BYPASS DE LOGIN (Devuelve todo en el formato que el frontend espera)
    if request.path == '/api/auth/login':
        return jsonify({
            "success": True, 
            "status": "ok",
            "token": "admin_bypass_token", 
            "user": {"id": 1, "role": "admin", "name": "Desarrollador", "username": "admin"}
        })
    
    # 2. BYPASS DE SESIÓN
    if request.path == '/api/auth/me':
        return jsonify({"id": 1, "role": "admin", "name": "Desarrollador", "username": "admin"})
        
    # 3. INTERCEPTOR DE CHAT
    if '/agent/chat' in request.path:
        if ia_estado != "lista":
            return jsonify({"reply": "Cargando IA. Espera 15 seg.", "response": "Cargando..."})
        
        data = request.get_json(silent=True) or {}
        # Capturamos el mensaje venga de donde venga
        msg = data.get('mensaje', data.get('message', data.get('msg', data.get('query', data.get('text', '')))))
        if not msg: 
            msg = request.data.decode('utf-8')
            
        print(f"[IA] Pregunta limpia: {msg}")
        respuesta = procesar_pregunta(msg)
        print(f"[IA] Respuesta: {respuesta}")
        
        # Devolvemos en el formato que tu frontend espera
        return jsonify({
            "reply": respuesta, 
            "response": respuesta, 
            "message": respuesta,
            "text": respuesta,
            "status": "ok"
        })

def preload_ia():
    global ia_estado
    ia_estado = "cargando"
    print("\n[IA] Cargando modelo local (15 seg)...")
    ruta = os.path.expanduser('~/tpv-chaquopy-public/models/qwen-coder.gguf')
    
    if os.path.exists(ruta):
        res = inicializar_ia(ruta)
        ia_estado = "lista" if "Lista" in res else "error"
        print(f"[IA] Estado: {ia_estado}")
    else:
        ia_estado = "error"
        print("[IA] ERROR: Modelo no encontrado.")

threading.Thread(target=preload_ia).start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=True)
