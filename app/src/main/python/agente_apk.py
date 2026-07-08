import json
import os
import re
import platform
import threading

try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

llm_model = None
ia_lock = threading.Lock() # Candado para evitar Segmentation Fault

def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE: return f"Error: {ERROR_IMPORT}"
    try:
        # Configuración ultra ligera para móvil (Rápida y sin crash)
        llm_model = Llama(model_path=ruta_modelo, n_ctx=256, n_threads=2, use_mmap=False, use_mlock=False, verbose=False)
        return "IA Lista"
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model: return "Error: IA no inicializada."
    
    # Si el input es un JSON (como envía tu frontend), lo parseamos
    try:
        data = json.loads(user_input)
        user_input = data.get('mensaje', data.get('message', data.get('query', str(data))))
    except:
        pass # Si no es JSON, usamos el texto normal

    system_prompt = "Eres un asistente útil. Responde muy breve en 1 o 2 frases."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    # Usamos el candado para que solo un hilo use la IA a la vez
    with ia_lock:
        try:
            response = llm_model.create_chat_completion(messages=messages, temperature=0.7, max_tokens=64)
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error: {str(e)}"
