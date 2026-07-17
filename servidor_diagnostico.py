#!/usr/bin/env python3
import os
import sys
import json
import uuid
import socket
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory, Response

base_dir = "/data/data/com.termux/files/home/tpv-chaquopy-public"
sys.path.insert(0, f"{base_dir}/app/src/main/python")

# Intentar importar todo lo necesario
try:
    from app import app as app_original
except:
    app_original = None

try:
    from ia_assistant import chat, process_question
    IA_AVAILABLE = True
except:
    IA_AVAILABLE = False

# Crear app Flask
app = Flask(__name__)

# Logging detallado
def log_request():
    print("\n" + "="*80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📨 {request.method} {request.path}")
    print(f"🌐 IP: {request.remote_addr}")
    print(f"📱 User-Agent: {request.headers.get('User-Agent', 'N/A')}")
    print(f"📋 Headers: {dict(request.headers)}")
    
    if request.data:
        try:
            print(f"📦 Body: {request.data.decode('utf-8')[:1000]}")
        except:
            print(f"📦 Body (binario): {request.data[:200]}")
    
    if request.args:
        print(f"🔗 Query Params: {dict(request.args)}")
    
    if request.form:
        print(f"📝 Form: {dict(request.form)}")
    
    if request.files:
        print(f"📎 Files: {list(request.files.keys())}")
    
    print("="*80)

@app.before_request
def before_request():
    log_request()

@app.after_request
def after_request(response):
    print(f"✅ Response Status: {response.status}")
    print(f"📤 Response Headers: {dict(response.headers)}")
    if response.data and len(response.data) < 500:
        try:
            print(f"📤 Response Body: {response.data.decode('utf-8')}")
        except:
            pass
    return response

# ============= ENDPOINTS DE AUTENTICACIÓN =============
@app.route('/api/auth/login', methods=['POST', 'GET', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json(silent=True) or {}
    username = data.get('username', data.get('email', data.get('user', 'admin')))
    password = data.get('password', data.get('pass', '1234'))
    
    print(f"🔑 INTENTO DE LOGIN: usuario={username}, password={password}")
    
    # Responder con todos los formatos posibles
    return jsonify({
        "success": True,
        "token": f"token_{uuid.uuid4().hex[:16]}",
        "access_token": f"access_{uuid.uuid4().hex[:16]}",
        "user": {
            "id": 1,
            "role": "admin",
            "name": "Administrador",
            "email": "admin@tpv.com",
            "username": username,
            "permissions": ["all"]
        },
        "status": "ok",
        "message": "Login exitoso"
    })

@app.route('/api/auth/me', methods=['GET', 'POST'])
def me():
    return jsonify({
        "id": 1,
        "role": "admin",
        "name": "Administrador",
        "email": "admin@tpv.com",
        "permissions": ["all"],
        "status": "active"
    })

@app.route('/api/auth/verify', methods=['GET', 'POST'])
def verify():
    return jsonify({
        "valid": True,
        "user": {"id": 1, "role": "admin"}
    })

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    return jsonify({"success": True})

@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({"success": True, "message": "Usuario registrado"})

@app.route('/api/auth/change-password', methods=['POST', 'PUT'])
def change_password():
    return jsonify({"success": True})

# ============= AGENTE IA =============
@app.route('/api/agent/identity', methods=['GET', 'POST', 'OPTIONS'])
def agent_identity():
    return jsonify({
        "id": "agent_tpv_001",
        "name": "Asistente TPV Smart",
        "version": "13.0.0",
        "status": "active",
        "mode": "bypass",
        "capabilities": [
            "chat", "sales", "inventory", "analytics", 
            "predictions", "cross_selling", "abc_analysis"
        ],
        "features": {
            "chat": True,
            "analytics": True,
            "inventory": True,
            "sales": True,
            "predictions": True,
            "fraud_detection": True
        },
        "role": "admin"
    })

@app.route('/api/agent/chat', methods=['POST'])
@app.route('/agent/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        # Obtener mensaje en cualquier formato
        data = request.get_json(silent=True) or {}
        msg = None
        
        # Probar todos los campos posibles
        for field in ['mensaje', 'message', 'text', 'question', 'query', 
                      'input', 'content', 'prompt', 'pregunta']:
            if field in data and data[field]:
                msg = data[field]
                break
        
        # Si no hay mensaje en JSON, probar con form data
        if not msg:
            for field in ['mensaje', 'message', 'text', 'question']:
                if field in request.form and request.form[field]:
                    msg = request.form[field]
                    break
        
        # Si aún no hay mensaje, probar con raw data
        if not msg and request.data:
            try:
                raw_data = json.loads(request.data.decode('utf-8'))
                for field in ['mensaje', 'message', 'text', 'question']:
                    if field in raw_data and raw_data[field]:
                        msg = raw_data[field]
                        break
            except:
                msg = request.data.decode('utf-8')
        
        print(f"💬 MENSAJE RECIBIDO: '{msg}'")
        
        if not msg:
            return jsonify({
                "reply": "¿En qué puedo ayudarte?",
                "response": "¿En qué puedo ayudarte?",
                "message": "¿En qué puedo ayudarte?",
                "status": "ok"
            })
        
        # Procesar con IA o simular
        if IA_AVAILABLE:
            try:
                session_id = data.get('session_id', data.get('sid', 'default'))
                role = data.get('role', 'admin')
                
                result = process_question(session_id, msg, role, "Usuario")
                answer = result.get('answer', '')
                print(f"🤖 RESPUESTA IA: {answer[:100]}...")
            except Exception as e:
                print(f"⚠️ Error en IA: {e}")
                answer = f"Procesando: {msg}"
        else:
            answer = f"Modo demo: {msg}"
        
        # Responder en todos los formatos posibles
        return jsonify({
            "reply": answer,
            "response": answer,
            "message": answer,
            "text": answer,
            "answer": answer,
            "status": "ok",
            "success": True,
            "session_id": data.get('session_id', 'default')
        })
        
    except Exception as e:
        print(f"❌ ERROR en chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "reply": "Error al procesar tu pregunta. Intenta de nuevo.",
            "response": "Error al procesar tu pregunta.",
            "status": "error"
        })

# ============= DATOS PARA EL FRONTEND =============
@app.route('/api/catalogo', methods=['GET'])
def catalogo():
    return jsonify([])

@app.route('/api/ventas/totales', methods=['GET'])
def ventas_totales():
    return jsonify({"total": 0, "count": 0})

@app.route('/api/ventas/hoy', methods=['GET'])
def ventas_hoy():
    return jsonify({"total": 0, "count": 0})

@app.route('/api/metrics', methods=['GET'])
def metrics():
    return jsonify({})

@app.route('/api/publico/catalogo', methods=['GET'])
def publico_catalogo():
    return jsonify([])

@app.route('/api/state', methods=['GET'])
def state():
    return jsonify({})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "13.0.0"})

@app.route('/api/i18n/dict', methods=['GET'])
def i18n_dict():
    return jsonify({})

@app.route('/api/analytics/daily', methods=['GET'])
def analytics_daily():
    return jsonify([])

@app.route('/api/analytics/monthly', methods=['GET'])
def analytics_monthly():
    return jsonify([])

@app.route('/api/products', methods=['GET'])
def products():
    return jsonify([])

@app.route('/api/products/all', methods=['GET'])
def products_all():
    return jsonify([])

# ============= CATCH-ALL PARA CUALQUIER OTRA RUTA =============
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all_api(path):
    print(f"🔄 CATCH-ALL: /api/{path}")
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({"status": "ok", "success": True})

# ============= ARCHIVOS ESTÁTICOS =============
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    # Servir archivos estáticos
    static_paths = [
        os.path.join(base_dir, "app/src/main/static"),
        os.path.join(base_dir, "app/src/main/assets/frontend"),
        os.path.join(base_dir, "app/src/main/assets/frontend/static"),
        os.path.join(base_dir, "app/src/main/templates"),
    ]
    
    # Si es un archivo con extensión
    if path and '.' in path:
        for base in static_paths:
            file_path = os.path.join(base, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                print(f"📄 Sirviendo archivo: {file_path}")
                return send_file(file_path)
        
        # Intentar en el directorio raíz
        file_path = os.path.join(base_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"📄 Sirviendo archivo raíz: {file_path}")
            return send_file(file_path)
    
    # Buscar index.html
    index_paths = [
        os.path.join(base_dir, "app/src/main/assets/frontend/templates/index.html"),
        os.path.join(base_dir, "app/src/main/assets/frontend/index.html"),
        os.path.join(base_dir, "app/src/main/static/index.html"),
        os.path.join(base_dir, "app/src/main/templates/index.html"),
        os.path.join(base_dir, "static/index.html"),
        os.path.join(base_dir, "index.html"),
    ]
    
    for idx_path in index_paths:
        if os.path.exists(idx_path) and os.path.isfile(idx_path):
            print(f"📄 Sirviendo index: {idx_path}")
            return send_file(idx_path)
    
    # Si no hay archivos, mostrar página de estado
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TPV Smart v13.0 - Servidor Activo</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: white;
                margin: 0;
                padding: 40px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                border: 1px solid rgba(255,255,255,0.1);
                max-width: 600px;
                width: 100%;
                text-align: center;
            }}
            h1 {{ color: #00d4ff; font-size: 2.5em; margin-bottom: 10px; }}
            .status {{ color: #00ff88; font-size: 1.2em; margin: 20px 0; }}
            .info {{ background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; margin: 20px 0; text-align: left; }}
            .info-item {{ padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .label {{ color: #888; }}
            .value {{ color: #00d4ff; float: right; }}
            .badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                margin: 5px;
                background: #00ff88;
                color: #1a1a2e;
            }}
            .badge.ia {{ background: #ff6b6b; color: white; }}
            .footer {{ margin-top: 30px; color: #666; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 TPV Smart v13.0</h1>
            <div class="status">✅ Servidor Funcionando</div>
            <div style="margin: 20px 0;">
                <span class="badge">🔓 BYPASS ACTIVO</span>
                <span class="badge ia">IA: {'✅ Disponible' if IA_AVAILABLE else '❌ No Disponible'}</span>
            </div>
            <div class="info">
                <div class="info-item"><span class="label">📱 Usuario:</span> <span class="value">CUALQUIERA</span></div>
                <div class="info-item"><span class="label">🔑 Contraseña:</span> <span class="value">CUALQUIERA</span></div>
                <div class="info-item"><span class="label">🌐 Puerto:</span> <span class="value">5050</span></div>
                <div class="info-item"><span class="label">🔄 Modo:</span> <span class="value">Diagnóstico Completo</span></div>
            </div>
            <div style="margin: 20px 0;">
                <p style="color: #ffd700; font-size: 0.9em;">
                    📊 Todos los endpoints están activos y loggeando
                </p>
            </div>
            <div class="footer">
                Servidor de diagnóstico | TPV Smart v13.0
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("="*80)
    print("🔧 SERVIDOR DE DIAGNÓSTICO COMPLETO")
    print("="*80)
    print(f"📱 Usuario: CUALQUIERA")
    print(f"🔑 Contraseña: CUALQUIERA")
    print(f"="*80)
    print(f"✅ IA disponible: {IA_AVAILABLE}")
    print(f"📂 Directorio: {base_dir}")
    print(f"="*80)
    print(f"🌐 Servidor: http://0.0.0.0:5050")
    print(f"📋 TODAS las peticiones se registran aquí")
    print(f"="*80)
    print("Presiona Ctrl+C para detener")
    print("="*80)
    
    # Escuchar en todas las interfaces
    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)
