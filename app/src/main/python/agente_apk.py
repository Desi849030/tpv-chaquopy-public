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

# ==========================================
# HERRAMIENTAS OFFLINE NIVEL PRO
# ==========================================
def tool_listar_directorio(ruta="."):
    try: return "\n".join(os.listdir(ruta))
    except Exception as e: return f"Error: {str(e)}"

def tool_leer_archivo(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f: return f.read()[:1000]
    except Exception as e: return f"Error: {str(e)}"

def tool_escribir_archivo(ruta, contenido):
    try:
        with open(ruta, 'w', encoding='utf-8') as f: f.write(contenido)
        return "Éxito: Archivo guardado."
    except Exception as e: return f"Error: {str(e)}"

def tool_info_sistema():
    try: return f"SO: {platform.system()} {platform.machine()}\nDir: {os.getcwd()}"
    except Exception as e: return f"Error: {str(e)}"

TOOLS_MAP = {
    "listar_directorio": tool_listar_directorio,
    "leer_archivo": tool_leer_archivo,
    "escribir_archivo": tool_escribir_archivo,
    "info_sistema": tool_info_sistema
}

# ==========================================
# MOTOR REACT FUSIONADO
# ==========================================
def procesar_respuesta_agentic(ia_output):
    match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
    if not match: return "RESPUESTA_FINAL", ia_output.strip()
    try:
        accion_json = json.loads(match.group(1).strip())
        return "ACCION", accion_json
    except json.JSONDecodeError:
        return "ERROR_FORMATO", None

def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE: return f"Error: {ERROR_IMPORT}"
    try:
        llm_model = Llama(model_path=ruta_modelo, n_ctx=512, n_threads=4, use_mmap=False, use_mlock=False, verbose=False)
        return "IA Lista"
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model: return "Error: IA no inicializada."
    
    system_prompt = """Eres un asistente útil. Tienes herramientas offline.
Solo si el usuario pide ver archivos, crear código o ver info del sistema, usa este formato:
<pensamiento>Qué vas a hacer</pensamiento>
<accion>{"nombre": "leer_archivo", "argumentos": {"ruta": "valor"}}</accion>
Herramientas: listar_directorio(ruta), leer_archivo(ruta), escribir_archivo(ruta, contenido), info_sistema().
Si es charla normal, responde muy breve en 1 o 2 frases."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    for _ in range(3):
        try:
            response = llm_model.create_chat_completion(messages=messages, temperature=0.7, max_tokens=128)
            ia_output = response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"
            
        messages.append({"role": "assistant", "content": ia_output})
        tipo, resultado = procesar_respuesta_agentic(ia_output)

        if tipo == "RESPUESTA_FINAL":
            return resultado
        elif tipo == "ACCION":
            tool_name = resultado.get("nombre")
            tool_args = resultado.get("argumentos", {})
            if tool_name in TOOLS_MAP:
                try: obs = TOOLS_MAP[tool_name](**tool_args)
                except: obs = "Error en argumentos."
                messages.append({"role": "user", "content": f"<obs>{obs}</obs>\nResumen breve:"})
            else:
                return "Herramienta no existe."
        else:
            return "Formato incorrecto."
    return "La IA tardó demasiado."
