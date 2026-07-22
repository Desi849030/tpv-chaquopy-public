"""First-run developer onboarding without console or hardcoded credentials."""
from __future__ import annotations

import pytest

import database
from app import app


@pytest.fixture(autouse=True)
def restore_test_developer():
    yield
    password_hash, salt = database._hash_password("dev2024")
    conn = database.obtener_conexion()
    try:
        conn.execute(
            "UPDATE usuarios SET password_hash=?, password_salt=? WHERE username='desarrollador'",
            (password_hash, salt),
        )
        conn.execute(
            "INSERT OR REPLACE INTO app_state (clave, valor, actualizado) "
            "VALUES ('developer_setup_required', '0', datetime('now','localtime'))"
        )
        try:
            conn.execute("DELETE FROM clientes_tienda WHERE username LIKE 'setup-test-%'")
        except Exception:
            pass
        conn.commit()
    finally:
        conn.close()


def _require_setup():
    password_hash, salt = database._hash_password("temporary-unusable-password")
    conn = database.obtener_conexion()
    try:
        conn.execute(
            "UPDATE usuarios SET password_hash=?, password_salt=? WHERE username='desarrollador'",
            (password_hash, salt),
        )
        conn.execute(
            "INSERT OR REPLACE INTO app_state (clave, valor, actualizado) "
            "VALUES ('developer_setup_required', '1', datetime('now','localtime'))"
        )
        conn.commit()
    finally:
        conn.close()


def test_setup_status_and_login_blocked_until_completed():
    _require_setup()
    app.config.update(TESTING=True, SECRET_KEY="setup-test")
    client = app.test_client()
    status = client.get("/api/setup/status").get_json()
    assert status == {"ok": True, "required": True, "username": "desarrollador", "local_only": True}
    blocked = client.post("/api/auth/login", json={
        "username": "desarrollador", "password": "temporary-unusable-password"
    })
    assert blocked.status_code == 428
    assert blocked.get_json()["code"] == "SETUP_REQUIRED"


def test_setup_rejects_remote_weak_and_mismatched_requests():
    _require_setup()
    app.config.update(TESTING=True, SECRET_KEY="setup-test")
    client = app.test_client()
    remote = client.post(
        "/api/setup/developer",
        json={"password": "StrongPass123!", "confirmacion": "StrongPass123!"},
        environ_base={"REMOTE_ADDR": "192.0.2.20"},
    )
    assert remote.status_code == 403
    assert client.post("/api/setup/developer", json={
        "password": "StrongPass123!", "confirmacion": "different"
    }).status_code == 400
    assert client.post("/api/setup/developer", json={
        "password": "weak", "confirmacion": "weak"
    }).status_code == 400
    common = client.post("/api/setup/developer", json={
        "password": "Desarrollador123!", "confirmacion": "Desarrollador123!"
    })
    assert common.status_code == 400
    assert "común" in common.get_json()["error"]


def test_developer_setup_requires_password_not_used_by_another_account():
    _require_setup()
    from tienda_routes import crear_tablas_tienda
    crear_tablas_tienda()
    password_hash, salt = database._hash_password("AlreadyUsed123!")
    connection = database.obtener_conexion()
    try:
        connection.execute(
            "INSERT INTO clientes_tienda "
            "(cliente_id, username, nombre, email, password_hash, password_salt, activo) "
            "VALUES ('setup-client', 'setup-test-client', 'Client', 'setup-test@example.com', ?, ?, 1)",
            (password_hash, salt),
        )
        connection.commit()
    finally:
        connection.close()
    app.config.update(TESTING=True, SECRET_KEY="setup-test")
    response = app.test_client().post("/api/setup/developer", json={
        "password": "AlreadyUsed123!", "confirmacion": "AlreadyUsed123!"
    })
    assert response.status_code == 409
    assert "exclusiva" in response.get_json()["error"]


def test_local_setup_is_one_time_and_new_password_logs_in():
    _require_setup()
    app.config.update(TESTING=True, SECRET_KEY="setup-test")
    client = app.test_client()
    configured = client.post("/api/setup/developer", json={
        "password": "StrongPass123!", "confirmacion": "StrongPass123!"
    })
    assert configured.status_code == 200
    assert configured.get_json()["ok"] is True
    assert client.get("/api/setup/status").get_json()["required"] is False
    assert client.post("/api/setup/developer", json={
        "password": "AnotherPass123!", "confirmacion": "AnotherPass123!"
    }).status_code == 409

    connection = database.obtener_conexion()
    try:
        dev_id = connection.execute(
            "SELECT usuario_id FROM usuarios WHERE username='desarrollador'"
        ).fetchone()[0]
    finally:
        connection.close()
    reused = database.crear_usuario(
        {"username": "other-user", "nombre": "Other", "password": "StrongPass123!", "rol": "vendedor"},
        "desarrollador", dev_id,
    )
    assert reused["ok"] is False
    assert "reservada" in reused["mensaje"]
    reserved = database.crear_usuario(
        {"username": "desarrollador", "nombre": "Copy", "password": "OtherStrong123!", "rol": "vendedor"},
        "desarrollador", dev_id,
    )
    assert reserved["ok"] is False
    assert "reservada" in reserved["mensaje"]

    from db.users import crear_usuario as crear_usuario_modular
    modular_reuse = crear_usuario_modular(
        {"username": "other-module", "nombre": "Other", "password": "StrongPass123!", "rol": "vendedor"},
        creado_por_rol="desarrollador", creado_por_id=dev_id,
    )
    assert modular_reuse["ok"] is False
    assert "reservada" in modular_reuse["mensaje"]

    from tienda_routes import crear_tablas_tienda
    crear_tablas_tienda()
    client_reuse = client.post("/api/clientes/registrar", json={
        "nombre": "Cliente", "email": "cliente-reserva@example.com", "password": "StrongPass123!"
    })
    assert client_reuse.status_code == 400
    assert "reservada" in client_reuse.get_json()["error"]

    login = client.post("/api/auth/login", json={
        "username": "desarrollador", "password": "StrongPass123!"
    })
    assert login.status_code == 200
    assert login.get_json()["usuario"]["rol"] == "desarrollador"
