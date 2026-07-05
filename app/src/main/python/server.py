from flask import Flask, request, jsonify
import threading
import os

# Importamos el agente IA que creamos
from agente_apk import inicializar_ia, procesar_pregunta

app = Flask(__name__)
ia_activada = False

@app.route('/')
def index():
    # Aquí iría tu login original o página principal
    return '''
    <h1>TPV Ultra Smart</h1>
    <p>Servidor Flask corriendo localmente.</p>
    <button onclick="activarIA()">Descargar/Activar IA</button>
    <div id="chat" style="display:none;">
        <input type="text" id="msg" placeholder="Escribe...">
        <button onclick="enviar()">Enviar</button>
        <div id="resp"></div>
    </div>
    <script>
        function activarIA() {
            fetch('/activar_ia').then(r => r.text()).then(t => {
                alert(t);
                document.getElementById('chat').style.display = 'block';
            });
        }
        function enviar() {
            var msg = document.getElementById('msg').value;
            fetch('/chat', {method: 'POST', body: msg}).then(r => r.text()).then(t => {
                document.getElementById('resp').innerHTML = t;
            });
        }
    </script>
    '''

@app.route('/activar_ia')
def activar_ia():
    global ia_activada
    if not ia_activada:
        # Ruta donde Android guarda los archivos
        ruta_modelo = os.path.join(os.environ.get('FILES_DIR', ''), 'qwen-coder.gguf')
        if not os.path.exists(ruta_modelo):
            ruta_modelo = 'qwen-coder.gguf' # Fallback
            
        resultado = inicializar_ia(ruta_modelo)
        if "Lista" in resultado:
            ia_activada = True
        return resultado
    return "IA ya está activa"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.data.decode('utf-8')
    if ia_activada:
        respuesta = procesar_pregunta(user_input)
        return respuesta
    return "Error: IA no activada."

def iniciar_servidor():
    # Flask corre en el puerto 5000 de forma local
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    iniciar_servidor()
