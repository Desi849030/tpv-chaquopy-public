import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from agente_apk import inicializar_ia, procesar_pregunta
from flask import request, jsonify, session, g

ia_estado = "inactiva"

@app.before_request
def bypass_total():
    global ia_estado
    
    # 1. INYECTAR SESIÓN DE ADMIN EN TODAS LAS PETICIONES (Adiós 401)
    g.user = {'id': 1, 'role': 'admin', 'name': 'Desarrollador', 'username': 'admin'}
    session['user_id'] = 1
    session['role'] = 'admin'
    
    # Dejar pasar peticiones CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    # 2. LOGIN BYPASS (Devuelve éxito sí o sí)
    if request.path == '/api/auth/login':
        return jsonify({
            "success": True,
            "status": "success",
            "token": "admin_bypass_token",
            "access_token": "admin_bypass_token",
            "user": g.user
        })
        
    if request.path == '/api/auth/me':
        return jsonify(g.user)
        
    # 3. CHAT IA
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
            "status": "ok"
        })

def preload_ia():
    global ia_estado
    ia_estado = "cargando"
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
