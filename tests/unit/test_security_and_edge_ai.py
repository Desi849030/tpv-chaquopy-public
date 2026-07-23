"""Behaviour coverage for active payment security, HET and Edge AI services."""
from __future__ import annotations

from datetime import datetime

import database


def test_pci_tokenization_luhn_brand_mask_and_audit():
    import security_pci as pci

    pci._AUDIT_LOG.clear()
    assert pci.validate_luhn("4111111111111111")
    assert not pci.validate_luhn("4111111111111112")
    assert pci.detect_card_brand("4111111111111111") == "visa"
    assert pci.detect_card_brand("5555555555554444") == "mastercard"
    assert pci.detect_card_brand("378282246310005") == "amex"
    assert pci.detect_card_brand("6011111111111117") == "discover"
    assert pci.mask_pan("4111111111111111").endswith("1111")
    assert "411111" not in pci.mask_pan("4111111111111111")
    result = pci.process_payment_token("4111111111111111", 25.5)
    assert result["valid"] and result["token"]
    assert "4111111111111111" not in str(result)
    invalid = pci.process_payment_token("1234", 10)
    assert not invalid["valid"] and invalid["error"]
    assert len(pci.get_audit_log()) >= 2


def test_generic_payment_token_roundtrip_and_record():
    import payment_tokenizer as tokenizer

    token = tokenizer.tokenize("1111")
    assert tokenizer.verify_token(token["token"], token["signature"])
    assert not tokenizer.verify_token(token["token"] + "x", token["signature"])
    assert tokenizer.mask_card("123") == "****"
    assert tokenizer.mask_card("4111111111111111").endswith("1111")
    record = tokenizer.create_payment_record(30.0, "card", "4111111111111111")
    assert record["payment_id"].startswith("pay-")
    assert record["card_masked"].endswith("1111")
    assert "4111111111111111" not in str(record)


def test_het_detection_lockout_rate_limit_and_summary(monkeypatch):
    import security_het as het

    het._request_log.clear()
    het._login_attempts.clear()
    het._login_lockouts.clear()
    het._threat_alerts.clear()
    monkeypatch.setitem(het._HET_CONFIG, "max_rpm", 2)
    assert het.check_rate_limit("127.0.0.1")[0]
    assert het.check_rate_limit("127.0.0.1")[0]
    assert not het.check_rate_limit("127.0.0.1")[0]
    assert not het.detect_sql_injection("1 OR 1=1")[0]
    assert not het.detect_xss("<script>alert(1)</script>")[0]
    assert het.detect_sql_injection("producto normal")[0]
    sanitized = het.sanitize_input("<b>DROP table</b>\x00")
    assert "<" not in sanitized and "DROP" not in sanitized.upper()
    for _ in range(het._HET_CONFIG["max_login"]):
        het.record_login_result("198.51.100.1", False)
    assert not het.check_login("198.51.100.1")[0]
    het.record_login_result("198.51.100.1", True)
    assert het.check_login("198.51.100.1")[0]
    summary = het.get_threat_summary()
    assert summary["warnings"] >= 1
    assert het.get_alerts(limit=5)


def test_attestation_and_payment_authorization():
    import security_attestation as attestation

    before = attestation.get_attestation_status()["total_checks"]
    result = attestation.run_full_attestation({"platform": "android"})
    assert result["integrity"] == "PASS"
    assert len(result["device_fingerprint"]) == 16
    small = attestation.authorize_payment(10)
    large = attestation.authorize_payment(150)
    assert small["authorized"] and not small["token_required"]
    assert large["authorized"] and large["token_required"]
    assert attestation.get_attestation_status()["total_checks"] >= before + 3


def _seed_edge_ai_data():
    prefix = "edge-test-"
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = database.obtener_conexion()
    try:
        conn.execute("DELETE FROM historial_ventas WHERE venta_id LIKE ?", (prefix + "%",))
        conn.execute("DELETE FROM inventario_general WHERE producto_id LIKE ?", (prefix + "%",))
        conn.execute("DELETE FROM productos WHERE producto_id LIKE ?", (prefix + "%",))
        products = [
            (prefix + "critical", "Edge Critical", 20.0, 10.0, 2.0),
            (prefix + "high", "Edge High", 15.0, 7.0, 10.0),
            (prefix + "medium", "Edge Medium", 12.0, 6.0, 20.0),
            (prefix + "low", "Edge Low", 8.0, 4.0, 100.0),
        ]
        for product_id, name, price, cost, stock in products:
            conn.execute(
                "INSERT INTO productos (producto_id,nombre,precio,costo,categoria,activo) VALUES (?,?,?,?,?,1)",
                (product_id, name, price, cost, "EdgeTest"),
            )
            conn.execute(
                "INSERT INTO inventario_general (producto_id,nombre,stock_actual,precio_compra,precio_venta) VALUES (?,?,?,?,?)",
                (product_id, name, stock, cost, price),
            )
        # Weekly velocity: critical 14/day equivalent, high 14/week, medium 14/week, low 7/week.
        quantities = {"critical": 14, "high": 14, "medium": 14, "low": 7}
        counter = 0
        for suffix, quantity in quantities.items():
            product_id = prefix + suffix
            name = "Edge " + suffix.capitalize()
            conn.execute(
                "INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,fecha) VALUES (?,?,?,?,?,?,?)",
                (prefix + f"velocity-{counter}", product_id, name, quantity, 10, quantity * 10, today),
            )
            counter += 1
        # Benford anomaly and refund-ratio sample.
        for index in range(20):
            conn.execute(
                "INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,fecha) VALUES (?,?,?,?,?,?,?)",
                (prefix + f"fraud-{index}", prefix + "low", "Edge Low", 1, 99, 99, today),
            )
        for index in range(3):
            conn.execute(
                "INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,fecha) VALUES (?,?,?,?,?,?,?)",
                (prefix + f"refund-{index}", prefix + "low", "Devolucion Edge", 1, -10, -10, today),
            )
        conn.commit()
    finally:
        conn.close()
    return prefix


def _cleanup_edge_ai_data(prefix):
    conn = database.obtener_conexion()
    try:
        conn.execute("DELETE FROM historial_ventas WHERE venta_id LIKE ?", (prefix + "%",))
        conn.execute("DELETE FROM inventario_general WHERE producto_id LIKE ?", (prefix + "%",))
        conn.execute("DELETE FROM productos WHERE producto_id LIKE ?", (prefix + "%",))
        conn.commit()
    finally:
        conn.close()


def test_edge_ai_fraud_and_inventory_predictions_use_real_schema():
    from ai_fraud import get_fraud_dashboard
    from ai_predictor import get_inventory_predictions_summary

    prefix = _seed_edge_ai_data()
    try:
        fraud = get_fraud_dashboard()
        assert fraud["benford_analysis"]["applicable"]
        assert fraud["benford_analysis"]["is_anomaly"]
        assert fraud["refund_ratio"]["flagged"]
        assert fraud["recent_alerts"]

        prediction = get_inventory_predictions_summary()
        assert prediction["total_products"] >= 4
        assert prediction["risk_distribution"]["critical"] >= 1
        assert prediction["risk_distribution"]["high"] >= 1
        assert prediction["recommendations"]
        assert prediction["financial_forecast"]["estimated_revenue_week"] > 0
    finally:
        _cleanup_edge_ai_data(prefix)
