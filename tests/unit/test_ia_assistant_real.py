"""Behaviour tests for the offline assistant using its real intent pipeline."""
from __future__ import annotations

import ia_assistant as assistant


def test_session_roles_permissions_and_status():
    sid = "coverage-session"
    assert assistant._clean_text("café")
    assert assistant.set_session_role(sid, "administrador", "Ana") == "administrador"
    info = assistant.get_session_info(sid)
    assert info["role"] == "administrador"
    assert info["user_name"] == "Ana"
    assert assistant._has_access("desarrollador", "anything") is True
    assert assistant._has_access("cliente", "seguridad") is False
    assert assistant._get_role_perms("desconocido") == assistant.ROLES["vendedor"]
    assert len(assistant._time_context()) == 2
    assert assistant._time_recommendation("administrador")
    status = assistant.get_status()
    assert isinstance(status, dict)
    assert status["offline_engine"] == "rules-react-memory"
    assert status["local_llm"] in {"loaded", "available_not_loaded", "optional_not_installed"}


def test_database_helpers_without_database(monkeypatch):
    monkeypatch.setattr(assistant, "_db_conn", None)
    monkeypatch.setattr(assistant, "_get_db_paths", lambda: ["/does/not/exist.db"])
    assert assistant._db() is None
    assert assistant._q("SELECT 1") is None
    assert assistant._safe_q("bad sql") is None
    assert assistant._exec("bad sql") is False


def test_product_parsing_and_intents(monkeypatch):
    products = [
        {"producto_id": "p1", "nombre": "Cafe Cubano", "precio": 12.5,
         "stock": 8, "categoria": "Bebidas", "costo": 7.0},
        {"producto_id": "p2", "nombre": "Pan Integral", "precio": 3.0,
         "stock": 0, "categoria": "Alimentos", "costo": 1.0},
    ]

    def fake_safe_q(sql, params=(), one=False):
        low = sql.lower()
        if "sqlite_master" in low:
            return []
        if "count(" in low or "sum(" in low or "avg(" in low:
            row = {"total": 100.0, "cantidad": 4, "conteo": 4, "promedio": 25.0,
                   "ganancia": 30.0, "stock_bajo": 1, "agotados": 1}
            return row if one else [row]
        return products[0] if one else products

    monkeypatch.setattr(assistant, "_safe_q", fake_safe_q)
    monkeypatch.setattr(assistant, "_q", fake_safe_q)
    monkeypatch.setattr(assistant, "_search_products", lambda query, limit=8: products)
    monkeypatch.setattr(assistant, "_learn", lambda *args, **kwargs: None)
    monkeypatch.setattr(assistant, "_recall", lambda *args, **kwargs: None)

    assert assistant._extract_product_name("precio del cafe")
    assert assistant._fmt(1234.5)
    assert assistant._detect_role_from_text("finanzas seguridad usuarios") == "administrador"

    prompts = [
        "hola buenos dias", "gracias", "adios", "ayuda que puedes hacer",
        "precio del cafe", "buscar cafe", "informacion de la aplicacion",
        "ventas de hoy", "estado del inventario y stock", "auditoria de seguridad",
        "recomendaciones para vender", "resumen del negocio", "ganancias y margen",
        "puntos de lealtad", "prediccion de ventas", "dashboard edge",
        "kpis del negocio", "analisis abc", "venta cruzada", "lista de precios",
        "una pregunta completamente desconocida",
    ]
    for index, prompt in enumerate(prompts):
        result = assistant.process_question(f"sid-{index}", prompt, role="administrador")
        assert isinstance(result, dict)
        assert result.get("answer")


def test_proactive_and_cleanup(monkeypatch):
    monkeypatch.setattr(assistant, "_generate_proactive_alerts", lambda role: [
        {"type": "stock", "message": "Stock bajo"}
    ])
    assistant.set_session_role("sid-alert", "administrador")
    alerts = assistant.get_proactive_alerts("sid-alert")
    assert isinstance(alerts["alerts"], list)
    assistant._sessions["old"] = {"ts": "2000-01-01T00:00:00", "history": []}
    assistant.cleanup_old_sessions()
    assert isinstance(assistant.get_conversation_history("sid-alert"), list)
