import os
import threading

try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

llm_model = None
ia_lock = threading.Lock()

def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE: return f"Error: {ERROR_IMPORT}"
    try:
        # Contexto bajísimo para máxima velocidad en móvil
        llm_model = Llama(model_path=ruta_modelo, n_ctx=256, n_threads=4, use_mmap=False, use_mlock=False, verbose=False)
        return "IA Lista"
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model: return "Error: IA no inicializada."
    
    system_prompt = "Eres un asistente útil del TPV. Responde muy breve en 1 frase."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    with ia_lock:
        try:
            # Max tokens 32 para que responda en 1-2 segundos
            response = llm_model.create_chat_completion(messages=messages, temperature=0.7, max_tokens=32)
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error: {str(e)}"
