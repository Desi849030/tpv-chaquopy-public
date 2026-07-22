"""Developer responses keep exhaustive detail and document continuation."""
from __future__ import annotations

from ia.agent import Agent
from ia.handlers_staff import handle_dev
from ia.intent_engine import detect_intents
from ia.response_budget import BUDGET_CONFIGS, BudgetMode, ResponseBudget


def test_chaquopy_is_not_misclassified_as_farewell():
    intents = detect_intents("Chaquopy", role="desarrollador")
    assert all(item["intent"] != "FAREWELL" for item in intents)
    farewell = detect_intents("chao", role="desarrollador")
    assert farewell[0]["intent"] == "FAREWELL"
    for query in ("Chaquopy", "chacopy", "chaquopi"):
        response = Agent().process(query, role="desarrollador")["answer"]
        assert "com.chaquo.python" in response
        assert "hasta luego" not in response.lower()


def test_exhaustive_budget_is_large_and_explicit():
    config = BUDGET_CONFIGS[BudgetMode.EXHAUSTIVE]
    assert config.max_chars >= 12_000
    assert config.max_lines >= 300
    text = "linea completa\n" * 200
    result = ResponseBudget().apply(text, mode=BudgetMode.EXHAUSTIVE)
    assert "linea completa" in result
    assert "respuesta truncada" not in result


def test_agent_uses_exhaustive_budget_only_for_developer():
    agent = Agent()
    long_text = "dato verificable " * 100
    developer = agent._r(long_text, "desarrollador")["answer"]
    client = agent._r(long_text, "cliente")["answer"]
    assert len(developer) > 1000
    assert len(client) <= 610


def test_developer_can_request_unabridged_telecom_json(monkeypatch):
    from modules import telecom_diag

    monkeypatch.setattr(telecom_diag, "diagnostico_completo", lambda: {
        "ok": True, "dns": {"tiempo_ms": 5}, "latencia": {"p95": 20},
        "tls": {"version": "TLSv1.3"}, "raw_samples": [1, 2, 3],
    })
    response = handle_dev(None, "telecom sin omitir", "Developer")
    assert '"raw_samples"' in response
    assert '"TLSv1.3"' in response


def test_developer_help_lists_all_information_domains():
    response = handle_dev(None, "ayuda", "Developer")
    for section in (
        "SISTEMA Y DATOS", "TELECOMUNICACIONES", "NEGOCIO", "DOCUMENTACIÓN"
    ):
        assert section in response
    assert "sin límites funcionales" in response
    assert "siguiente" in response
