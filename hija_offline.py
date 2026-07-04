import os
import re
import json
from llama_cpp import Llama
from rich.console import Console
from rich.panel import Panel

console = Console()

# ==========================================
# 1. CARGAR EL MODELO LOCAL (100% OFFLINE)
# ==========================================
console.print("[bold yellow]Cargando el cerebro de la IA en la RAM de tu dispositivo...[/bold yellow]")
try:
    llm = Llama(
        model_path="./models/qwen-coder.gguf",
        n_ctx=1024,       # Ventana de contexto (memoria a corto plazo)
        n_threads=4,      # Número de núcleos de tu CPU a usar
        use_mmap=False,
        use_mlock=False,
        verbose=False     # Ocultar logs técnicos de carga
    )
    console.print("[bold green]¡IA cargada y lista para operar offline![/bold green]")
except Exception as e:
    console.print(f"[bold red]Error cargando el modelo: {e}[/bold red]")
    exit()

# ==========================================
# 2. HERRAMIENTAS OFFLINE (Manos de la IA)
# ==========================================
def leer_archivo(ruta: str) -> str:
    """Lee un archivo local."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()[:2000] # Limitamos a 2000 chars para no saturar la RAM
    except FileNotFoundError:
        return f"Error: Archivo {ruta} no encontrado."

def escribir_archivo(ruta: str, contenido: str) -> str:
    """Escribe en un archivo local."""
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    return f"Éxito: Escrito en {ruta}."

def listar_directorio(ruta: str = ".") -> str:
    """Lista archivos de una carpeta."""
    try:
        return "\n".join(os.listdir(ruta))
    except Exception as e:
        return str(e)

tools_mapping = {
    "leer_archivo": leer_archivo,
    "escribir_archivo": escribir_archivo,
    "listar_directorio": listar_directorio
}

# ==========================================
# 3. PROMPT DEL SISTEMA (Entrenamiento Agentic)
# ==========================================
SYSTEM_PROMPT = """Eres una IA Agentic de nivel Senior operando 100% offline en un dispositivo Android.
Tu objetivo es ayudar a programar y analizar archivos locales.

Tienes acceso a herramientas. Debes usar el siguiente formato EXACTO para usarlas:

<pensamiento>Explica qué vas a hacer y por qué</pensamiento>
<accion>{"nombre": "nombre_de_herramienta", "argumentos": {"parametro": "valor"}}</accion>

Herramientas disponibles:
- listar_directorio(ruta: str): Lista archivos en un directorio.
- leer_archivo(ruta: str): Lee el contenido de un archivo.
- escribir_archivo(ruta: str, contenido: str): Crea o sobrescribe un archivo.

Cuando tengas la información necesaria y quieras dar la respuesta final al usuario, NO uses la etiqueta <accion>, simplemente responde normalmente con texto plano.
"""

# ==========================================
# 4. MOTOR REACT (El Bucle del Agente)
# ==========================================
def run_agent(user_input: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
    
    console.print(Panel(f"[bold cyan]{user_input}[/bold cyan]", title="Tú"))

    # Bucle de Pensamiento -> Acción -> Observación
    for paso in range(5): # Máximo 5 iteraciones para evitar bucles infinitos
        # Generar respuesta localmente
        response = llm.create_chat_completion(
            messages=messages,
            temperature=0.1, # Baja temperatura para que sea lógica y estricta con el formato
            max_tokens=1024
        )
        
        ia_output = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": ia_output})

        # Buscar si la IA decidió usar una herramienta (parsear XML)
        match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
        
        if not match:
            # Si no hay <accion>, la IA decidió dar la respuesta final
            console.print(Panel(f"[bold green]{ia_output}[/bold green]", title="Respuesta Final"))
            break
        
        # Extraer el JSON de la acción
        try:
            accion_json = json.loads(match.group(1).strip())
            tool_name = accion_json.get("nombre")
            tool_args = accion_json.get("argumentos", {})
            
            console.print(f"[bold yellow]⚙️ PASO {paso+1}: Ejecutando {tool_name} con {tool_args}[/bold yellow]")
            
            # Ejecutar herramienta offline
            tool_func = tools_mapping.get(tool_name)
            if tool_func:
                observation = tool_func(**tool_args)
            else:
                observation = f"Error: Herramienta '{tool_name}' no existe."

            # Darle la observación a la IA para que siga pensando
            messages.append({"role": "user", "content": f"<observacion>{observation}</observacion>\nContinúa basándote en esta observación."})
            console.print(f"[bold blue]👀 Observación obtenida (primeros 200 chars): {str(observation)[:200]}...[/bold blue]")

        except json.JSONDecodeError:
            messages.append({"role": "user", "content": "Error: El JSON en <accion> está mal formateado. Intenta de nuevo."})
        except Exception as e:
            messages.append({"role": "user", "content": f"Error al ejecutar herramienta: {str(e)}"})

# ==========================================
# 5. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    console.print("[bold magenta]🤖 Hija Agentic Offline (10/10) Inicializada. Escribe 'salir' para terminar.[/bold magenta]")
    while True:
        user_input = input("\nTú: ")
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
        if user_input.strip():
            run_agent(user_input)
