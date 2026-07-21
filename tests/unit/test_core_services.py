"""Focused tests for security, validation, metrics, and licensing services."""
from __future__ import annotations

import os


def test_security_validation_and_calculations(monkeypatch):
    from security import validation as v

    assert v.sanitize_string(" <b>hola</b> ") == "hola"
    assert v.sanitize_data({"x": ["<i>ok</i>", 2]}) == {"x": ["ok", 2]}
    for payload in ("UNION SELECT x", "' OR '1'='1", {"q": "DROP"}, ["SLEEP(2)"]):
        assert v.check_sql_injection(payload)
    assert not v.check_sql_injection("producto normal")
    assert v.generar_id("p").startswith("p-")

    sale = v.calcular_venta([{"precio": 100, "cantidad": 2}], 10, 5)
    assert sale["total"] == 189.0
    assert v.validar_totales({"items": [{"precio": 10}], "total": 10})["valido"]
    assert not v.validar_totales({"items": [{"precio": 10}], "total": 12})["valido"]

    assert v.sanitize_input("<script onclick='x'>")
    assert v.sanitize_input(10) == "10"
    assert v.validate_email("a@example.com")
    assert not v.validate_email("incorrecto")


def test_response_validators_cover_valid_and_invalid_paths():
    from response_validators import checks

    samples = [
        checks.validate_financial_response({"total": -1, "ganancia": -999999, "descuento": 150}),
        checks.validate_financial_response({"total": "bad"}),
        checks.validate_inventory_response({"stock": -2, "precio": -1, "producto_id": ""}),
        checks.validate_inventory_response({"stock": 999999, "precio": "bad"}),
        checks.validate_text_response("<script>alert(1)</script>"),
        checks.validate_text_response("Traceback (most recent call last): File /app/src/x.py"),
        checks.validate_text_response("no"),
        checks.validate_response({"total": 10}),
        checks.validate_response({"stock": 10}, "inventory"),
        checks.validate_response("respuesta normal suficientemente larga"),
    ]
    assert any(not result.is_valid for result in samples)
    assert checks.format_validation_message(samples[0])
    assert checks.format_validation_message(checks.validate_text_response("respuesta valida")) == ""


def test_real_system_metrics_and_database_formulas():
    import database
    from metrics import helpers

    database.crear_tablas()
    path = helpers._get_db_path()
    assert os.path.exists(path)
    assert helpers._ram_info()["proceso_mb"] >= 0
    assert helpers._storage_info(path)["db_size_kb"] >= 0
    formulas = helpers._inventario_formulas(path)
    assert formulas["error"] is None
    assert helpers._inventario_formulas("/missing/database.db")["error"]
    tables = helpers._tablas_info(path)
    assert tables["total_tablas"] > 0
    metrics = helpers.get_system_metrics()
    assert "ram" in metrics and "storage" in metrics


def test_license_lifecycle():
    from license import core

    generated = core.generar_licencia("device-a", tipo="trial", valor=1, unidad="dias")
    license_id = generated["licencia_id"]
    assert core.validar_licencia("device-a")["valida"]
    assert core.activar_licencia(license_id, "device-b")["ok"]
    assert core.validar_licencia("device-b")["valida"]
    assert any(item["licencia_id"] == license_id for item in core.listar_licencias())
    assert core.desactivar_licencia(license_id)["ok"]
    assert not core.validar_licencia("device-b")["valida"]
    assert core.generar_device_id()
