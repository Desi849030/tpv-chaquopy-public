import json
import re
import pytest

# Simulamos la lógica del agente ReAct para medir su cobertura
def procesar_respuesta_agentic(ia_output):
    match = re.search(r"<accion>(.*?)</accion>", ia_output, re.DOTALL)
    if not match:
        return "RESPUESTA_FINAL", ia_output.strip()
    
    try:
        accion_json = json.loads(match.group(1).strip())
        return "ACCION", accion_json
    except json.JSONDecodeError:
        return "ERROR_FORMATO", None

def test_agente_respuesta_normal():
    output = "Hola, soy una IA y estoy aquí para ayudarte."
    tipo, resultado = procesar_respuesta_agentic(output)
    assert tipo == "RESPUESTA_FINAL"
    assert "ayudarte" in resultado

def test_agente_usa_herramienta_correcta():
    output = '<pensamiento>Voy a leer</pensamiento><accion>{"nombre": "leer_archivo", "argumentos": {"ruta": "main.py"}}</accion>'
    tipo, resultado = procesar_respuesta_agentic(output)
    assert tipo == "ACCION"
    assert resultado["nombre"] == "leer_archivo"
    assert resultado["argumentos"]["ruta"] == "main.py"

def test_agente_json_roto():
    output = '<accion>{nombre: "leer_archivo"}</accion>' # JSON inválido (sin comillas)
    tipo, resultado = procesar_respuesta_agentic(output)
    assert tipo == "ERROR_FORMATO"
