import json
import os
import re
import platform
import threading
import sqlite3

try:
    from llama_cpp import Llama
    IA_DISPONIBLE = True
except Exception as e:
    IA_DISPONIBLE = False
    ERROR_IMPORT = str(e)

llm_model = None
ia_lock = threading.Lock()

# HERRAMIENTA PRO: Consultar la base de datos del TPV
def tool_consultar_db(query="SELECT name FROM sqlite_master WHERE type='table'"):
    try:
        conn = sqlite3.connect('tpv_datos.db')
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
        conn.close()
        return str(rows[:10]) # Limitamos a 10 resultados para no saturar
    except Exception as e:
        return f"Error SQL: {str(e)}"

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
    
    try:
        data = json.loads(user_input)
        user_input = data.get('mensaje', data.get('message', data.get('query', str(data))))
    except:
        pass

    system_prompt = """Eres el asistente del TPV Ultra Smart. Tienes acceso a una base de datos SQLite local.
Si te preguntan por productos, tiendas o categorías, usa la herramienta para consultar la BD.
Para usar la herramienta responde: <accion>{"nombre": "consultar_db", "argumentos": {"query": "SELECT * FROM productos LIMIT 5"}}</accion>
Si ya tienes la info, responde muy breve."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    with ia_lock:
        for _ in range(3):
            try:
                response = llm_model.create_chat_completion(messages=messages, temperature=0.1, max_tokens=128)
                ia_output = response["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Error: {str(e)}"
                
            messages.append({"role": "assistant", "content": ia_output})
            
            # Comprobar si la IA quiere usar la BD
            match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
            if not match:
                return ia_output.strip()
            
            try:
                accion = json.loads(match.group(1).strip())
                if accion.get("nombre") == "consultar_db":
                    obs = tool_consultar_db(accion.get("argumentos", {}).get("query", ""))
                    messages.append({"role": "user", "content": f"<obs>{obs}</obs>\nResponde breve al usuario."})
                else:
                    return "Herramienta no soportada."
            except:
                return "Error de formato."
        return "La IA tardó demasiado."
