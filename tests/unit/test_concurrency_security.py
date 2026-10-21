# -*- coding: utf-8 -*-
"""Pruebas reales de atomicidad, idempotencia HTTP, concurrencia y FK/RBAC.

Verifica directamente el comportamiento en tiempo de ejecución de:
- modules/ventas_atomic_v10.py (POST /api/ventas/registrar y _registrar)
- database.py (crear_tablas, 6 roles en CHECK, claves foráneas activas, WAL)
- db_connection.py (registro real en audit_logs sin errores silenciosos)
"""
from __future__ import annotations

import os
import sqlite3
import threading
import pytest


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Inicializa una base SQLite limpia tal como arranca el APK Android."""
    db_dir = str(tmp_path)
    db_file = os.path.join(db_dir, "tpv_datos.db")
    monkeypatch.setenv("TPV_FILES_DIR", db_dir)
    monkeypatch.setenv("TPV_DB_PATH", db_file)

    import database
    import db_connection
    import app as flask_app

    monkeypatch.setattr(database, "DB_FILE", db_file)
    monkeypatch.setattr(db_connection, "DB_FILE", db_file)
    monkeypatch.setattr(db_connection, "DB_PATH", db_file)

    database.crear_tablas()

    conn = database.obtener_conexion()
    try:
        pw, salt = database._hash_password("ClaveSegura123!")
        conn.execute(
            "INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt, activo) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            ("u_vend", "vendedor1", "Vendedor Turno", "vendedor", pw, salt),
        )
        conn.execute(
            "INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt, activo) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            ("u_caj", "cajero1", "Cajero Principal", "cajero", pw, salt),
        )
        conn.execute(
            "INSERT INTO productos (producto_id, nombre, precio, costo, categoria, activo) "
            "VALUES ('P_ARROZ', 'Arroz 1 kg', 650.0, 500.0, 'Alimentos', 1)"
        )
        conn.execute(
            "INSERT INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta) "
            "VALUES ('P_ARROZ', 'Arroz 1 kg', 10.0, 2.0, 500.0, 650.0)"
        )
        conn.execute(
            "INSERT INTO productos (producto_id, nombre, precio, costo, categoria, activo) "
            "VALUES ('P_WHISKY', 'Whisky Old Star', 1700.0, 1400.0, 'Licores', 1)"
        )
        conn.execute(
            "INSERT INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta) "
            "VALUES ('P_WHISKY', 'Whisky Old Star', 2.0, 1.0, 1400.0, 1700.0)"
        )
        conn.commit()
    finally:
        conn.close()

    flask_app.app.config.update(TESTING=True)
    return database, flask_app.app


def _stock_actual(database, pid: str) -> float:
    conn = database.obtener_conexion()
    try:
        row = conn.execute(
            "SELECT stock_actual FROM inventario_general WHERE producto_id=?", (pid,)
        ).fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def test_idempotencia_http_arranque_real_apk(isolated_env):
    """Enviar dos veces el mismo client_txn_id NO duplica la venta ni el descuento."""
    database, app = isolated_env
    client = app.test_client()

    login = client.post(
        "/api/auth/login", json={"username": "vendedor1", "password": "ClaveSegura123!"}
    )
    assert login.status_code == 200 and login.get_json()["ok"]

    payload = {
        "client_txn_id": "TXN-IDEMP-0001",
        "metodo_pago": "efectivo",
        "items": [
            {"producto_id": "P_ARROZ", "nombre": "Arroz 1 kg", "cantidad": 2, "precio": 650.0},
            {"producto_id": "P_WHISKY", "nombre": "Whisky Old Star", "cantidad": 1, "precio": 1700.0},
        ],
    }

    r1 = client.post("/api/ventas/registrar", json=payload)
    r2 = client.post("/api/ventas/registrar", json=payload)

    assert r1.status_code == 200 and r2.status_code == 200
    b1, b2 = r1.get_json(), r2.get_json()
    assert b1["ok"] and b1["idempotent"] is False
    assert b2["ok"] and b2["idempotent"] is True
    assert b1["venta_id"] == b2["venta_id"]
    assert b1["total"] == 3000.0 and b2["total"] == 3000.0
    assert _stock_actual(database, "P_ARROZ") == 8.0
    assert _stock_actual(database, "P_WHISKY") == 1.0

    conn = database.obtener_conexion()
    try:
        n_cab = conn.execute("SELECT COUNT(*) FROM ventas_cabecera").fetchone()[0]
        n_det = conn.execute("SELECT COUNT(*) FROM ventas_detalle").fetchone()[0]
        n_hist = conn.execute("SELECT COUNT(*) FROM historial_ventas").fetchone()[0]
        n_aud = conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE accion='registrar_venta'"
        ).fetchone()[0]
        assert n_cab == 1
        assert n_det == 2
        assert n_hist == 2
        assert n_aud == 1
    finally:
        conn.close()


def test_rollback_atomico_stock_insuficiente(isolated_env):
    """Si el segundo ítem excede el stock, revierte también el descuento del primero."""
    database, app = isolated_env
    client = app.test_client()
    client.post(
        "/api/auth/login", json={"username": "vendedor1", "password": "ClaveSegura123!"}
    )

    payload = {
        "client_txn_id": "TXN-ROLLBACK-0001",
        "items": [
            {"producto_id": "P_ARROZ", "nombre": "Arroz 1 kg", "cantidad": 4, "precio": 650.0},
            {"producto_id": "P_WHISKY", "nombre": "Whisky Old Star", "cantidad": 99, "precio": 1700.0},
        ],
    }
    resp = client.post("/api/ventas/registrar", json=payload)
    assert resp.status_code == 409
    assert resp.get_json()["code"] == "STOCK_INSUFICIENTE"

    # El stock del primer producto permanece intacto (10.0), sin registros huérfanos
    assert _stock_actual(database, "P_ARROZ") == 10.0
    assert _stock_actual(database, "P_WHISKY") == 2.0

    conn = database.obtener_conexion()
    try:
        assert conn.execute("SELECT COUNT(*) FROM ventas_cabecera").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ventas_detalle").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM historial_ventas").fetchone()[0] == 0
    finally:
        conn.close()


def test_concurrencia_dos_hilos_ultimo_articulo(isolated_env):
    """Dos hilos compitiendo por stock=1 producen 1 éxito (200) y 1 rechazo limpio (409)."""
    database, _ = isolated_env
    from modules.ventas_atomic_v10 import _registrar

    conn = database.obtener_conexion()
    try:
        conn.execute("UPDATE inventario_general SET stock_actual=1 WHERE producto_id='P_WHISKY'")
        conn.commit()
    finally:
        conn.close()

    resultados = [None, None]
    usuarios = [
        {"usuario_id": "u_vend", "nombre": "Vendedor", "rol": "vendedor"},
        {"usuario_id": "u_caj", "nombre": "Cajero", "rol": "cajero"},
    ]

    def worker(idx: int):
        body, status = _registrar(
            {
                "client_txn_id": f"TXN-CONC2-{idx}",
                "items": [{"producto_id": "P_WHISKY", "nombre": "Whisky", "cantidad": 1, "precio": 1700}],
            },
            usuarios[idx],
        )
        resultados[idx] = (status, body)

    hilos = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in hilos:
        t.start()
    for t in hilos:
        t.join(timeout=10)

    codigos = sorted(r[0] for r in resultados if r is not None)
    assert codigos == [200, 409], f"Resultados inesperados: {resultados}"
    assert _stock_actual(database, "P_WHISKY") == 0.0


def test_concurrencia_cinco_hilos_serializacion_estricta(isolated_env):
    """Cinco hilos concurrentes sobre stock=3 producen exactamente 3 ventas y 2 rechazos."""
    database, _ = isolated_env
    from modules.ventas_atomic_v10 import _registrar

    conn = database.obtener_conexion()
    try:
        conn.execute("UPDATE inventario_general SET stock_actual=3 WHERE producto_id='P_ARROZ'")
        conn.commit()
    finally:
        conn.close()

    resultados = [None] * 5
    user = {"usuario_id": "u_vend", "nombre": "Vendedor", "rol": "vendedor"}

    def worker(idx: int):
        body, status = _registrar(
            {
                "client_txn_id": f"TXN-CONC5-{idx}",
                "items": [{"producto_id": "P_ARROZ", "nombre": "Arroz", "cantidad": 1, "precio": 650}],
            },
            user,
        )
        resultados[idx] = (status, body)

    hilos = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in hilos:
        t.start()
    for t in hilos:
        t.join(timeout=15)

    exitos = [r for r in resultados if r and r[0] == 200]
    rechazos = [r for r in resultados if r and r[0] == 409]
    assert len(exitos) == 3, f"Se esperaban 3 ventas confirmadas: {resultados}"
    assert len(rechazos) == 2, f"Se esperaban 2 rechazos limpios: {resultados}"
    assert _stock_actual(database, "P_ARROZ") == 0.0


def test_seis_perfiles_rol_check_constraint(isolated_env):
    """La restricción CHECK de usuarios acepta los 6 perfiles y bloquea roles inválidos."""
    database, _ = isolated_env
    conn = database.obtener_conexion()
    try:
        pw, salt = database._hash_password("Test1234!")
        roles = ("desarrollador", "administrador", "supervisor", "vendedor", "cajero", "cliente")
        for idx, rol in enumerate(roles):
            conn.execute(
                "INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt, activo) "
                "VALUES (?, ?, ?, ?, ?, ?, 1)",
                (f"role_u_{idx}", f"role_usr_{idx}", f"Usuario {rol}", rol, pw, salt),
            )
        conn.commit()
        total_roles = conn.execute(
            "SELECT COUNT(DISTINCT rol) FROM usuarios WHERE usuario_id LIKE 'role_u_%'"
        ).fetchone()[0]
        assert total_roles == 6

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt, activo) "
                "VALUES ('bad_u', 'bad_usr', 'Rol Invalido', 'superadmin_inexistente', ?, ?, 1)",
                (pw, salt),
            )
    finally:
        conn.close()


def test_claves_foraneas_integridad_referencial(isolated_env):
    """PRAGMA foreign_keys=ON impide insertar registros con usuario o cabecera inexistentes."""
    database, _ = isolated_env
    conn = database.obtener_conexion()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO historial_ventas (venta_id, producto_id, nombre, cantidad, precio_unit, total, vendedor_id) "
                "VALUES ('V_FK', 'P_ARROZ', 'Arroz', 1, 650, 650, 'USUARIO_NO_EXISTE')"
            )

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ventas_detalle (venta_id, producto_id, nombre, cantidad, precio_unit, subtotal) "
                "VALUES ('CABECERA_INEXISTENTE', 'P_ARROZ', 'Arroz', 1, 650, 650)"
            )
    finally:
        conn.close()


def test_endpoints_resumen_y_cierre_caja_v10(isolated_env):
    """Ejercita /api/ventas/hoy, /api/ventas/totales, /api/ventas/cierre y /api/ventas/cierres."""
    _, app = isolated_env
    client = app.test_client()
    client.post(
        "/api/auth/login", json={"username": "cajero1", "password": "ClaveSegura123!"}
    )

    # Bloqueo anti-CSRF de origen cruzado externo
    csrf_resp = client.post(
        "/api/ventas/registrar",
        headers={"Origin": "https://sitio-externo-malicioso.example"},
        json={"items": [{"producto_id": "P_ARROZ", "cantidad": 1, "precio": 650}]},
    )
    assert csrf_resp.status_code == 403

    r_venta = client.post(
        "/api/ventas/registrar",
        json={
            "client_txn_id": "TXN-CIERRE-01",
            "items": [{"producto_id": "P_ARROZ", "nombre": "Arroz 1 kg", "cantidad": 3, "precio": 650}],
        },
    )
    assert r_venta.status_code == 200

    hoy = client.get("/api/ventas/hoy").get_json()
    assert hoy["ok"] and hoy["total"] == 1950.0 and hoy["cantidad"] == 1

    totales = client.get("/api/ventas/totales").get_json()
    assert totales["ok"] and totales["hoy"]["total"] == 1950.0

    cierre = client.post("/api/ventas/cierre", json={}).get_json()
    assert cierre["ok"] and cierre["total_ventas"] == 1950.0

    lista_cierres = client.get("/api/ventas/cierres").get_json()
    assert lista_cierres["ok"] and len(lista_cierres["cierres"]) >= 1
