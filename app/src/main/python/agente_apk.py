import json
import os
import re
import platform

try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

llm_model = None

def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE: return f"Error: {ERROR_IMPORT}"
    try:
        # Contexto bajo y 4 hilos para máxima velocidad en móvil
        llm_model = Llama(model_path=ruta_modelo, n_ctx=256, n_threads=4, use_mmap=False, use_mlock=False, verbose=False)
        return "IA Lista"
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_pregunta_stream(user_input):
    """Genera la respuesta en streaming (palabra por palabra) para que el usuario la vea al instante."""
    if not llm_model: 
        yield "Error: IA no inicializada."
        return
    
    system_prompt = "Eres un asistente útil. Responde muy breve y directo."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        # stream=True envía las palabras a medida que se generan
        for chunk in llm_model.create_chat_completion(messages=messages, temperature=0.7, max_tokens=64, stream=True):
            if 'content' in chunk['choices'][0]['delta']:
                yield chunk['choices'][0]['delta']['content']
    except Exception as e:
        yield f"Error: {str(e)}"
