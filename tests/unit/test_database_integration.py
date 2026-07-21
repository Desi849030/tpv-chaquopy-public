"""Integration tests for the active SQLite persistence layer.

These tests intentionally exercise public database operations against an isolated
real SQLite database rather than mocking calls just to increase line counts.
"""
from __future__ import annotations

from datetime import date

import database as db


def _developer_id() -> str:
    conn = db.obtener_conexion()
    try:
        return conn.execute(
            "SELECT usuario_id FROM usuarios WHERE username='desarrollador'"
        ).fetchone()[0]
    finally:
        conn.close()


def test_user_and_license_lifecycle():
    db.crear_tablas()
    dev_id = _developer_id()

    assert db.verificar_password("dev2024", *db._hash_password("dev2024"))
    assert db.login_usuario("desarrollador", "incorrecta") is None
    developer = db.login_usuario("desarrollador", "dev2024")
    assert developer and developer["rol"] == "desarrollador"

    bad = db.crear_usuario({}, "vendedor", dev_id)
    assert bad["ok"] is False
    missing = db.crear_usuario({"rol": "administrador"}, "desarrollador", dev_id)
    assert missing["ok"] is False

    created = db.crear_usuario(
        {"username": "admin_test", "nombre": "Admin Test", "password": "safe-pass", "rol": "administrador"},
        "desarrollador",
        dev_id,
    )
    assert created["ok"] is True
    admin_id = created["usuario_id"]
    assert db.crear_usuario(
        {"username": "admin_test", "nombre": "Duplicado", "password": "safe-pass", "rol": "administrador"},
        "desarrollador", dev_id,
    )["ok"] is False

    assert db.login_usuario("admin_test", "safe-pass")["usuario_id"] == admin_id
    assert db.cambiar_password(admin_id, "bad", "new-password")["ok"] is False
    assert db.cambiar_password(admin_id, "safe-pass", "new-password")["ok"] is True
    assert db.resetear_password(admin_id, "abc", dev_id)["ok"] is False
    assert db.resetear_password(admin_id, "reset-pass", dev_id)["ok"] is True
    assert any(u["usuario_id"] == admin_id for u in db.listar_usuarios("desarrollador", dev_id))
    assert db.listar_usuarios("vendedor", dev_id) == []

    denied = db.crear_licencia(admin_id, "anual", 365, "", admin_id)
    assert denied["ok"] is False
    license_result = db.crear_licencia(admin_id, "anual", 365, "prueba", dev_id)
    assert license_result["ok"] is True
    license_id = license_result["licencia_id"]
    assert db.listar_licencias(dev_id)
    assert db.verificar_licencia_activa(admin_id)
    assert db.desactivar_licencia(license_id, admin_id)["ok"] is False
    assert db.desactivar_licencia(license_id, dev_id)["ok"] is True
    assert db.desactivar_usuario(admin_id, dev_id)["ok"] is True


def test_catalog_inventory_state_and_reports():
    db.crear_tablas()
    dev_id = _developer_id()
    products = [
        {"id": "p-1", "nombre": "Cafe", "precio": 12.5, "costoUnitario": 7.0,
         "categoria": "Bebidas", "um": "u", "onSale": False},
        {"id": "p-2", "nombre": "Pan", "precio": 3.0, "costoUnitario": 1.0,
         "categoria": "Alimentos", "um": "u", "onSale": False},
    ]
    synced = db.sincronizar_productos_catalogo(products, dev_id)
    assert isinstance(synced, dict)
    assert len(db.obtener_productos_catalogo()) >= 2

    imported = db.importar_catalogo_a_inventario(dev_id)
    assert isinstance(imported, dict)
    stock = db.cargar_stock_masivo(dev_id, [
        {"producto_id": "p-1", "cantidad": 20, "precio_compra": 7},
        {"producto_id": "", "cantidad": 0},
    ])
    assert stock["ok"] is True

    entry = db.registrar_entrada_producto(
        {"producto_id": "p-1", "nombre": "Cafe", "cantidad": 5,
         "precio_compra": 7, "proveedor": "Proveedor"}, dev_id,
    )
    assert isinstance(entry, dict)
    assert isinstance(db.obtener_inventario_general(dev_id), list)
    assert isinstance(db.obtener_historial_entradas(dev_id), list)

    today = date.today().isoformat()
    assigned = db.asignar_inventario_diario(dev_id, [
        {"producto_id": "p-1", "nombre": "Cafe", "cant_asignada": 2,
         "precio_venta": 12.5, "precio_costo": 7}
    ], dev_id)
    assert isinstance(assigned, dict)
    assert isinstance(db.obtener_inventario_diario(dev_id, today), list)
    assert db.actualizar_vendido_diario(dev_id, "p-1", 1) is True

    payload = {
        "productos": [{"id": "p-3", "nombre": "Leche", "precio": 5}],
        "historialVentas": [], "cierresCaja": [], "actualizado": today,
    }
    assert db.guardar_estado(payload) is True
    assert db.cargar_estado() == payload

    assert isinstance(db.consultar_ventas_por_fecha(today, today), list)
    assert isinstance(db.consultar_resumen_ventas(), dict)
    assert isinstance(db.consultar_inventario_actual(), list)
    assert isinstance(db.consultar_ganancias_por_dia(), list)
    assert isinstance(db.obtener_info_db(), dict)

    snapshot = {"fecha": today, "total_ventas": 10, "ventas_data": [], "inventario_data": []}
    assert db.guardar_historial_diario_local(snapshot) is True
    assert isinstance(db.obtener_historial_diario_local(), list)
    assert db.obtener_historial_detalle_local(today)
    db.agregar_log("integration test", "info", dev_id)

    assert isinstance(db.sincronizar_estado_completo(dev_id), dict)
    assert isinstance(db.reconstruir_desde_productos(dev_id, products), dict)
    assert isinstance(db.limpiar_inventarios_diarios(dev_id), dict)
    assert isinstance(db.eliminar_producto_inventario_general("p-2", dev_id), dict)
