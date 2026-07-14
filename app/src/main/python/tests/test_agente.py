import pytest
from agente_apk import procesar_pregunta


def test_agente_modulo_importable():
    """Verifica que el modulo agente_apk carga correctamente."""
    assert callable(procesar_pregunta)


def test_agente_respuesta_normal():
    """Una pregunta normal debe devolver un string no vacio."""
    output = procesar_pregunta("Hola, ¿que puedes hacer?")
    assert isinstance(output, str)
    assert len(output) > 0


def test_agente_pregunta_vacia():
    """Pregunta vacia no debe crashear."""
    output = procesar_pregunta("")
    assert output is not None


def test_agente_pregunta_larga():
    """Pregunta larga no debe crashear."""
    output = procesar_pregunta("dame un diagnostico completo del sistema")
    assert output is not None
