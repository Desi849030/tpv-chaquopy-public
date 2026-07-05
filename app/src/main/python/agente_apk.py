import json
import os

try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

from react_engine import procesar_respuesta_agentic

llm_model = None

def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE:
        return f"Error de librería: {ERROR_IMPORT}"
        
    try:
        llm_model = Llama(
            model_path=ruta_modelo,
            n_ctx=1024,
            n_threads=4,
            use_mmap=False,
            use_mlock=False,
            verbose=False
        )
        return "IA Agentic lista"
    except Exception as e:
        return f"Error modelo: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model:
        return "Error: IA no inicializada."

    system_prompt = """Eres una IA Agentic offline en Android. Usa este formato para herramientas:
<pensamiento>Razona aquí</pensamiento>
<accion>{"nombre": "leer_archivo", "argumentos": {"ruta": "valor"}}</accion>
Si no necesitas herramientas, responde normalmente."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    for _ in range(3):
        try:
            response = llm_model.create_chat_completion(messages=messages, temperature=0.1, max_tokens=512)
            ia_output = response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error generando: {str(e)}"
            
        messages.append({"role": "assistant", "content": ia_output})
        tipo, resultado = procesar_respuesta_agentic(ia_output)

        if tipo == "RESPUESTA_FINAL":
            return resultado
        elif tipo == "ACCION":
            tool_name = resultado.get("nombre")
            tool_args = resultado.get("argumentos", {})
            if tool_name == "leer_archivo":
                try:
                    with open(tool_args.get("ruta", ""), "r") as f:
                        obs = f.read()[:1500]
                except Exception as e:
                    obs = f"Error leyendo: {str(e)}"
                messages.append({"role": "user", "content": f"<observacion>{obs}</observacion>"})
            else:
                messages.append({"role": "user", "content": "Error: herramienta no existe."})
        else:
            messages.append({"role": "user", "content": "Error de formato JSON."})

    return "La IA tomó demasiado tiempo procesando."
