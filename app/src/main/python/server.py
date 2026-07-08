import os
import sys
import threading
import traceback
from flask import Flask, request, render_template

# Asegurar que Python encuentre el agente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agente_apk import inicializar_ia, procesar_pregunta, procesar_pregunta_stream

# CONFIGURACIÓN FLASK: Apuntar a tu carpeta de HTML original
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'frontend', 'templates'))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'frontend', 'static'))
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

ia_estado = "inactiva"
ia_error_msg = ""

# RUTA PRINCIPAL: Carga tu index.html original
@app.route('/')
def index():
    try:
        # Esto carga tu login y splash original
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Error cargando index.html</h1><p>{e}</p>"

# RUTAS DE LA IA (Integradas)
@app.route('/activar_ia')
def activar_ia():
    global ia_estado
    if ia_estado in ["inactiva", "error"]:
        ia_estado = "cargando"
        thread = threading.Thread(target=cargar_ia_background)
        thread.start()
    return "Iniciando"

def cargar_ia_background():
    global ia_estado, ia_error_msg
    try:
        if os.path.exists('models/qwen-coder.gguf'): ruta = 'models/qwen-coder.gguf'
        else: ruta = 'qwen-coder.gguf'
        
        resultado = inicializar_ia(ruta)
        ia_estado = "lista" if "Lista" in resultado else "error"
        if ia_estado == "error": ia_error_msg = resultado
    except Exception as e:
        ia_error_msg = traceback.format_exc()
        ia_estado = "error"

@app.route('/estado_ia')
def estado_ia(): return ia_estado

@app.route('/chat', methods=['POST'])
def chat():
    if ia_estado == "lista":
        return procesar_pregunta(request.data.decode('utf-8'))
    return "Error: IA no lista."

@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    if ia_estado == "lista":
        from flask import Response, stream_with_context
        return Response(stream_with_context(procesar_pregunta_stream(request.data.decode('utf-8'))), content_type='text/plain')
    return "Error: IA no lista."

def iniciar_servidor():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    iniciar_servidor()
