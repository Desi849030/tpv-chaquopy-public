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

# HERRAMIENTAS
def tool_listar_directorio(ruta="."):
    try: return "\n".join(os.listdir(ruta))
    except Exception as e: return f"Error: {str(e)}"

def tool_leer_archivo(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f: return f.read()[:2000]
    except Exception as e: return f"Error: {str(e)}"

def tool_escribir_archivo(ruta, contenido):
    try:
        with open(ruta, 'w', encoding='utf-8') as f: f.write(contenido)
        return f"Éxito: Archivo guardado en {ruta}."
    except Exception as e: return f"Error: {str(e)}"

def tool_info_sistema():
    try:
        return f"Sistema: {platform.system()} {platform.machine()}\nPython: {platform.python_version()}\nDir: {os.getcwd()}\n"
    except Exception as e: return f"Error: {str(e)}"

TOOLS_MAP = {
    "listar_directorio": tool_listar_directorio,
    "leer_archivo": tool_leer_archivo,
    "escribir_archivo": tool_escribir_archivo,
    "info_sistema": tool_info_sistema
}

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
    if not IA_DISPONIBLE: return f"Error de librería: {ERROR_IMPORT}"
    try:
        llm_model = Llama(model_path=ruta_modelo, n_ctx=2048, n_threads=4, use_mmap=False, use_mlock=False, verbose=False)
        return "IA Agentic Lista"
    except Exception as e:
        return f"Error modelo: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model: return "Error: IA no inicializada."

    # PROMPT HUMANIZADO Y CONVERSACIONAL
    system_prompt = """Eres un Asistente IA conversacional, amigable y muy útil. Operas offline en un Android.
Tu objetivo principal es charlar con el usuario de forma natural y ayudarle.
Solo si el usuario te pide EXPLÍCITAMENTE leer archivos, listar carpetas o crear código, debes usar herramientas.
Para usar una herramienta, responde EXACTAMENTE con este formato:

<pensamiento>Explica qué vas a hacer</pensamiento>
<accion>{"nombre": "nombre_herramienta", "argumentos": {"parametro": "valor"}}</accion>

Herramientas:
1. listar_directorio(ruta)
2. leer_archivo(ruta)
3. escribir_archivo(ruta, contenido)
4. info_sistema()

Reglas:
- Si es una charla normal (saludos, preguntas generales), responde con texto normal SIN usar etiquetas XML.
- Sé cálido, directo y profesional."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    for _ in range(5):
        try:
            response = llm_model.create_chat_completion(messages=messages, temperature=0.6, max_tokens=512)
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
            if tool_name in TOOLS_MAP:
                try: obs = TOOLS_MAP[tool_name](**tool_args)
                except TypeError: obs = "Error: Argumentos incorrectos."
            else:
                obs = f"Error: La herramienta '{tool_name}' no existe."
            messages.append({"role": "user", "content": f"<observacion>{obs}</observacion>\nContinúa."})
        else:
            messages.append({"role": "user", "content": "Error: JSON mal formateado."})

    return "El agente excedió el límite de pasos."
