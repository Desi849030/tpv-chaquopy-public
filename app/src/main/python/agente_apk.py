import json
import os
import re
import platform

# 1. Importación del cerebro de IA (Manejo seguro de errores)
try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

llm_model = None

# ==========================================
# 2. HERRAMIENTAS OFFLINE DEL SISTEMA
# ==========================================
def tool_listar_directorio(ruta="."):
    """Lista archivos y carpetas en un directorio."""
    try:
        archivos = os.listdir(ruta)
        return "\n".join(archivos)
    except Exception as e:
        return f"Error: {str(e)}"

def tool_leer_archivo(ruta):
    """Lee el contenido de un archivo."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()[:2000]
    except Exception as e:
        return f"Error: {str(e)}"

def tool_escribir_archivo(ruta, contenido):
    """Crea o sobrescribe un archivo."""
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return f"Éxito: Archivo guardado en {ruta}."
    except Exception as e:
        return f"Error: {str(e)}"

def tool_info_sistema():
    """Obtiene información del dispositivo."""
    try:
        info = f"Sistema: {platform.system()} {platform.machine()}\n"
        info += f"Python: {platform.python_version()}\n"
        info += f"Directorio actual: {os.getcwd()}\n"
        return info
    except Exception as e:
        return f"Error: {str(e)}"

TOOLS_MAP = {
    "listar_directorio": tool_listar_directorio,
    "leer_archivo": tool_leer_archivo,
    "escribir_archivo": tool_escribir_archivo,
    "info_sistema": tool_info_sistema
}

# ==========================================
# 3. MOTOR REACT FUSIONADO (Lógica de parseo)
# ==========================================
def procesar_respuesta_agentic(ia_output):
    """Extrae la acción de la IA o devuelve la respuesta final."""
    match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
    if not match:
        return "RESPUESTA_FINAL", ia_output.strip()
    
    try:
        accion_json = json.loads(match.group(1).strip())
        return "ACCION", accion_json
    except json.JSONDecodeError:
        return "ERROR_FORMATO", None

# ==========================================
# 4. INICIALIZACIÓN Y BUCLE DEL AGENTE
# ==========================================
def inicializar_ia(ruta_modelo):
    global llm_model
    if not IA_DISPONIBLE:
        return f"Error de librería: {ERROR_IMPORT}"
        
    try:
        llm_model = Llama(
            model_path=ruta_modelo,
            n_ctx=2048,
            n_threads=4,
            use_mmap=False,
            use_mlock=False,
            verbose=False
        )
        return "IA Agentic Lista (Nivel Pro)"
    except Exception as e:
        return f"Error modelo: {str(e)}"

def procesar_pregunta(user_input):
    if not llm_model:
        return "Error: IA no inicializada."

    system_prompt = """Eres un Asistente IA Profesional. Operas offline en un dispositivo Android y ayudas al usuario con programación y análisis de archivos.
Tienes acceso a herramientas para interactuar con el sistema de archivos. 
Para usar una herramienta, debes responder EXACTAMENTE con este formato XML:

<pensamiento>Explica qué vas a hacer y por qué</pensamiento>
<accion>{"nombre": "nombre_herramienta", "argumentos": {"parametro": "valor"}}</accion>

Herramientas disponibles:
1. listar_directorio(ruta: str): Lista los archivos y carpetas.
2. leer_archivo(ruta: str): Lee el contenido de un archivo.
3. escribir_archivo(ruta: str, contenido: str): Crea o sobrescribe un archivo.
4. info_sistema(): Obtiene información del sistema operativo y directorio actual.

Reglas:
- Usa info_sistema() si no sabes dónde estás.
- Si ya tienes la información necesaria para responder al usuario, responde con texto normal SIN usar las etiquetas XML.
- Sé preciso, autónomo y profesional."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    # Bucle ReAct (Máximo 5 pasos de razonamiento)
    for _ in range(5):
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
            
            if tool_name in TOOLS_MAP:
                func = TOOLS_MAP[tool_name]
                try:
                    obs = func(**tool_args)
                except TypeError:
                    obs = "Error: Faltan argumentos o son incorrectos para esta herramienta."
            else:
                obs = f"Error: La herramienta '{tool_name}' no existe."
                
            messages.append({"role": "user", "content": f"<observacion>{obs}</observacion>\nContinúa tu tarea basándote en esta información."})
        else:
            messages.append({"role": "user", "content": "Error: El JSON en <accion> está mal formateado. Asegúrate de usar comillas dobles."})

    return "El agente excedió el límite de pasos de razonamiento."
