import json
import re

def procesar_respuesta_agentic(ia_output):
    """Esta es la función central que será probada por los tests."""
    match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
    if not match:
        return "RESPUESTA_FINAL", ia_output.strip()
    
    try:
        accion_json = json.loads(match.group(1).strip())
        return "ACCION", accion_json
    except json.JSONDecodeError:
        return "ERROR_FORMATO", None
