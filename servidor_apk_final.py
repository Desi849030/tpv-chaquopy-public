import os
import sys
import uuid
from flask import Flask, send_file, jsonify, request

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

app = Flask(__name__, 
    static_folder=f"{base_dir}/app/src/main/static",
    static_url_path='/static'
)

# ========== IA ==========
def ask_llm(msg):
    msg = msg.lower().strip()
    if 'ventas' in msg:
        return "📊 Las ventas de hoy son $1,234.56 en 15 transacciones."
    if 'stock' in msg:
        return "📦 Hay 1,523 productos en inventario."
    if 'precio' in msg or 'cuesta' in msg:
        return "💰 El café cuesta $2.50, el pan $1.50."
    if 'hola' in msg:
        return "👋 ¡Hola! Soy tu asistente TPV."
    return "🤔 Prueba con 'ventas', 'stock' o 'ayuda'."

# ========== LOGIN ==========
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json() or {}
    username = data.get('username', data.get('email', 'admin'))
    password = data.get('password', '')
    
    print(f"🔑 LOGIN: {username} / {password}")
    
    # Devolver respuesta con token y usuario
    return jsonify({
        "success": True,
        "status": "ok",
        "message": "Login exitoso",
        "access_token": f"access_{uuid.uuid4().hex[:16]}",
        "token": f"token_{uuid.uuid4().hex[:16]}",
        "refresh_token": f"refresh_{uuid.uuid4().hex[:16]}",
        "user": {
            "id": 1,
            "role": "admin",
            "name": "Administrador",
            "email": "admin@tpv.com",
            "username": username,
            "permissions": ["*"]
        }
    })

# ========== OTRAS RUTAS DE AUTENTICACIÓN ==========
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
    return jsonify({"valid": True, "authenticated": True})

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    return jsonify({"success": True, "message": "Logout exitoso"})

# ========== AGENTE ==========
@app.route('/api/agent/identity', methods=['GET', 'POST'])
def identity():
    return jsonify({
        "id": "agent_tpv_001",
        "name": "Asistente TPV",
        "version": "13.0.0",
        "status": "active",
        "mode": "bypass",
        "capabilities": ["chat", "sales", "inventory", "prices"]
    })

@app.route('/api/agent/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message', data.get('mensaje', ''))
    if not msg:
        return jsonify({"reply": "¿En qué puedo ayudarte?"})
    print(f"💬 {msg}")
    respuesta = ask_llm(msg)
    return jsonify({
        "reply": respuesta,
        "response": respuesta,
        "message": respuesta,
        "status": "ok",
        "success": True
    })

# ========== DATOS DE EJEMPLO CON FORMATO PARA APK ==========
@app.route('/api/catalogo', methods=['GET'])
def catalogo():
    # Envolver en un objeto con "data" y "success"
    return jsonify({
        "success": True,
        "data": [
            {"id": 1, "nombre": "Café Americano", "precio": 2.50, "stock": 50, "categoria": "Bebidas"},
            {"id": 2, "nombre": "Café con Leche", "precio": 3.00, "stock": 40, "categoria": "Bebidas"},
            {"id": 3, "nombre": "Capuchino", "precio": 3.50, "stock": 30, "categoria": "Bebidas"},
            {"id": 4, "nombre": "Té Verde", "precio": 2.00, "stock": 60, "categoria": "Bebidas"},
            {"id": 5, "nombre": "Jugo de Naranja", "precio": 3.00, "stock": 25, "categoria": "Bebidas"}
        ]
    })

@app.route('/api/publico/catalogo', methods=['GET'])
def publico_catalogo():
    return jsonify({
        "success": True,
        "data": [
            {"id": 1, "nombre": "Café Americano", "precio": 2.50},
            {"id": 2, "nombre": "Café con Leche", "precio": 3.00},
            {"id": 3, "nombre": "Capuchino", "precio": 3.50}
        ]
    })

@app.route('/api/ventas/totales', methods=['GET'])
def ventas_totales():
    return jsonify({
        "success": True,
        "data": {"total": 1234.56, "count": 15, "transacciones": 15}
    })

@app.route('/api/ventas/hoy', methods=['GET'])
def ventas_hoy():
    return jsonify({
        "success": True,
        "data": {"total": 1234.56, "count": 15, "transacciones": 15}
    })

@app.route('/api/metrics', methods=['GET'])
def metrics():
    return jsonify({
        "success": True,
        "data": {
            "ventas_hoy": 1234.56,
            "productos_vendidos": 45,
            "clientes_activos": 8,
            "stock_critico": 3
        }
    })

@app.route('/api/state', methods=['GET'])
def state():
    return jsonify({
        "success": True,
        "data": {
            "status": "online",
            "version": "13.0.0",
            "modo": "bypass"
        }
    })

@app.route('/api/i18n/dict', methods=['GET'])
def i18n():
    return jsonify({
        "success": True,
        "data": {}
    })

@app.route('/api/analytics/daily', methods=['GET'])
def analytics_daily():
    return jsonify({"success": True, "data": []})

@app.route('/api/analytics/monthly', methods=['GET'])
def analytics_monthly():
    return jsonify({"success": True, "data": []})

@app.route('/api/products', methods=['GET'])
def products():
    return jsonify({"success": True, "data": []})

@app.route('/api/products/all', methods=['GET'])
def products_all():
    return jsonify({"success": True, "data": []})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "13.0.0", "mode": "bypass"})

# ========== CATCH-ALL ==========
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all_api(path):
    print(f"🔄 CATCH-ALL: /api/{path}")
    return jsonify({"success": True, "status": "ok", "data": []})

# ========== SERVIR FRONTEND ==========
@app.route('/')
@app.route('/<path:path>')
def serve_static(path=''):
    if path and '.' in path:
        static_dir = f"{base_dir}/app/src/main/assets/frontend/static"
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path):
            return send_file(file_path)
        return "Archivo no encontrado", 404
    
    index_path = f"{base_dir}/app/src/main/assets/frontend/templates/index.html"
    if os.path.exists(index_path):
        return send_file(index_path)
    return "TPV Smart - Servidor Activo", 200

if __name__ == '__main__':
    print("="*70)
    print("🔓 TPV - SERVIDOR PARA APK (FORMATO DATA)")
    print("="*70)
    print("📱 Usuario: CUALQUIERA")
    print("🔑 Contraseña: CUALQUIERA")
    print("📌 Respuestas envueltas en 'data' y 'success'")
    print("="*70)
    print("🌐 Servidor: http://127.0.0.1:5050")
    print("🌐 También en: http://10.36.206.30:5050")
    print("="*70)
    app.run(host='0.0.0.0', port=5050, debug=False)
