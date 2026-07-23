"""Non-technical jury explanations remain clear, honest and evidence-based."""
from ia.handlers_staff import handle_dev
from plain_language_explainer import detect_topic, explain_for_general_audience


def test_topic_detection_covers_project_domains():
    assert detect_topic("explica Chaquopy") == "chaquopy"
    assert detect_topic("latencia de red") == "telecom"
    assert detect_topic("capas OSI") == "osi"
    assert detect_topic("inteligencia artificial") == "ia"
    assert detect_topic("seguridad") == "seguridad"
    assert detect_topic("modo avión") == "offline"
    assert detect_topic("pruebas y cobertura") == "pruebas"
    assert detect_topic("qué es esto") == "proyecto"


def test_every_plain_explanation_has_benefit_analogy_and_evidence():
    for question in (
        "proyecto", "Chaquopy", "Telecom", "OSI", "IA", "seguridad", "offline", "pruebas"
    ):
        response = explain_for_general_audience(question)
        assert "En palabras sencillas" in response
        assert "Ejemplo para entenderlo" in response
        assert "Cómo se demuestra" in response
        assert "detalle técnico" in response


def test_developer_dispatches_plain_language_mode():
    response = handle_dev(None, "explica telecom para el jurado", "Developer")
    assert "¿Cuál es el aporte de Telecomunicaciones?" in response
    assert "En palabras sencillas" in response
    assert "Cómo se demuestra" in response
