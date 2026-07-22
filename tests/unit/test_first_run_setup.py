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
        json={"password": "StrongPass123", "confirmacion": "StrongPass123"},
        environ_base={"REMOTE_ADDR": "192.0.2.20"},
    )
    assert remote.status_code == 403
    assert client.post("/api/setup/developer", json={
        "password": "StrongPass123", "confirmacion": "different"
    }).status_code == 400
    assert client.post("/api/setup/developer", json={
        "password": "weak", "confirmacion": "weak"
    }).status_code == 400


def test_local_setup_is_one_time_and_new_password_logs_in():
    _require_setup()
    app.config.update(TESTING=True, SECRET_KEY="setup-test")
    client = app.test_client()
    configured = client.post("/api/setup/developer", json={
        "password": "StrongPass123", "confirmacion": "StrongPass123"
    })
    assert configured.status_code == 200
    assert configured.get_json()["ok"] is True
    assert client.get("/api/setup/status").get_json()["required"] is False
    assert client.post("/api/setup/developer", json={
        "password": "AnotherPass123", "confirmacion": "AnotherPass123"
    }).status_code == 409
    login = client.post("/api/auth/login", json={
        "username": "desarrollador", "password": "StrongPass123"
    })
    assert login.status_code == 200
    assert login.get_json()["usuario"]["rol"] == "desarrollador"
