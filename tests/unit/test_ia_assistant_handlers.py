"""Direct tests for each offline-assistant capability handler."""
from __future__ import annotations

import ia_assistant as assistant


class Row(dict):
    """Small sqlite.Row-compatible mapping used at the query boundary."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def test_all_capability_handlers(monkeypatch):
    rows = [Row(
        nombre="Cafe", producto_id="p1", precio=12.5, precio_venta=12.5,
        precio_compra=7.0, costo=7.0, stock=8, stock_actual=8,
        cantidad=4, total=100.0, total_ventas=100.0, num_ventas=4,
        ganancia=30.0, margen=25.0, categoria="Bebidas", vendedor="Ana",
        fecha="2026-07-21", puntos=20,
    )]

    def fake_query(sql, params=(), one=False):
        return rows[0] if one else rows

    monkeypatch.setattr(assistant, "_safe_q", fake_query)
    monkeypatch.setattr(assistant, "_q", fake_query)
    monkeypatch.setattr(assistant, "_search_products", lambda *args, **kwargs: rows)

    calls = [
        lambda: assistant._handle_greeting("administrador", "Ana"),
        lambda: assistant._handle_resumen_rol("administrador", "Ana"),
        assistant._handle_thanks,
        assistant._handle_farewell,
        lambda: assistant._handle_help("administrador"),
        lambda: assistant._handle_product_price("cafe", "administrador"),
        lambda: assistant._handle_product_search("cafe"),
        lambda: assistant._handle_app_info("administrador"),
        lambda: assistant._handle_ventas({}, "administrador"),
        lambda: assistant._handle_inventario({}, "administrador"),
        lambda: assistant._handle_seguridad({}, "administrador"),
        lambda: assistant._handle_recomendacion("administrador"),
        lambda: assistant._handle_resumen("administrador"),
        lambda: assistant._handle_financiero({}, "administrador"),
        lambda: assistant._handle_lealtad("administrador"),
        lambda: assistant._handle_prediccion("administrador"),
        lambda: assistant._handle_edge_dashboard("administrador"),
        lambda: assistant._handle_edge_kpis("administrador"),
        lambda: assistant._handle_edge_abc("administrador"),
        lambda: assistant._handle_edge_cross_selling("administrador"),
        lambda: assistant._handle_edge_precios("administrador"),
        lambda: assistant._handle_unknown("consulta desconocida", "administrador"),
    ]
    for call in calls:
        assert isinstance(call(), str)


def test_detection_suggestions_and_compatibility_wrapper(monkeypatch):
    monkeypatch.setattr(assistant, "_learn", lambda *args: None)
    monkeypatch.setattr(assistant, "_recall", lambda *args: None)
    monkeypatch.setattr(assistant, "_search_products", lambda *args, **kwargs: [])
    samples = [
        "", "hola", "gracias", "adios", "resumen del dia", "ayuda",
        "precio cafe", "buscar producto cafe", "ventas hoy", "stock bajo",
        "seguridad usuarios permisos", "recomendacion", "ganancias",
        "puntos lealtad", "prediccion", "edge dashboard", "analisis abc",
    ]
    for sample in samples:
        intent, _ = assistant._detect_intent(sample, "administrador")
        assert isinstance(intent, str)
        assert isinstance(assistant._get_suggestions(intent), list)
    result = assistant.chat("hola", "compat", "vendedor")
    assert result["response"]
