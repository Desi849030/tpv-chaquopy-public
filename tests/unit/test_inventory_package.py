"""Integration coverage for the modular inventory data-access package."""
from __future__ import annotations

from datetime import date

from db_connection import obtener_conexion
from db.products_inventario import (
    actualizar_vendido_diario,
    asignar_inventario_diario,
    cargar_stock_masivo,
    limpiar_inventarios_diarios,
    obtener_historial_entradas,
    obtener_inventario_diario,
    obtener_inventario_general,
    registrar_entrada_producto,
)


def _dev_id():
    conn = obtener_conexion()
    try:
        return conn.execute(
            "SELECT usuario_id FROM usuarios WHERE username='desarrollador'"
        ).fetchone()[0]
    finally:
        conn.close()


def test_modular_inventory_complete_flow():
    dev_id = _dev_id()
    product_id = "pkg-inventory-1"

    invalid = registrar_entrada_producto({}, dev_id)
    assert invalid["ok"] is False
    entry = registrar_entrada_producto({
        "producto_id": product_id,
        "nombre": "Producto modular",
        "cantidad": 20,
        "precio_compra": 4,
        "precio_venta": 8,
        "categoria": "Pruebas",
        "unidad_medida": "u",
        "proveedor": "Proveedor",
    }, dev_id)
    assert entry["ok"] is True

    stock = cargar_stock_masivo(dev_id, [
        {"producto_id": product_id, "cantidad": 5, "precio_compra": 4.5},
        {"producto_id": "", "cantidad": 0},
    ])
    assert stock["ok"] is True and stock["actualizados"] == 1
    assert any(item["producto_id"] == product_id for item in obtener_inventario_general(dev_id))
    assert obtener_historial_entradas(dev_id)
    assert obtener_historial_entradas(dev_id, product_id)

    assigned = asignar_inventario_diario(dev_id, [{
        "producto_id": product_id,
        "nombre": "Producto modular",
        "cant_asignada": 3,
        "precio_venta": 8,
        "precio_costo": 4.5,
    }], dev_id)
    assert assigned["ok"] and assigned["asignados"] == 1
    assert obtener_inventario_diario(dev_id, date.today().isoformat())
    assert actualizar_vendido_diario(dev_id, product_id, 1)

    assert limpiar_inventarios_diarios(dev_id, dev_id, date.today().isoformat())["ok"]
    assert limpiar_inventarios_diarios(dev_id, vendedor_id=dev_id)["ok"]
    assert limpiar_inventarios_diarios(dev_id, fecha=date.today().isoformat())["ok"]
    assert limpiar_inventarios_diarios(dev_id)["ok"]
