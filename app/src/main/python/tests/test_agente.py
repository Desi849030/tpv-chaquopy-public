import pytest
from react_engine import procesar_respuesta_agentic

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
    output = '<accion>{nombre: "leer_archivo"}</accion>'
    tipo, resultado = procesar_respuesta_agentic(output)
    assert tipo == "ERROR_FORMATO"
