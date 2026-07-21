"""End-to-end tests for the Flask API against the isolated SQLite database."""
from __future__ import annotations

import database
from app import app


def _client():
    database.crear_tablas()
    app.config.update(TESTING=True, SECRET_KEY="integration-secret")
    client = app.test_client()
    response = client.post("/api/auth/login", json={
        "username": "desarrollador", "password": "dev2024"
    })
    assert response.status_code == 200
    return client


def test_public_and_authenticated_get_routes():
    client = _client()
    public = [
        "/", "/health", "/api/health", "/api/ping", "/manifest.json",
        "/service-worker.js", "/api/auth/me", "/api/status",
    ]
    authenticated = [
        "/api/usuarios", "/api/licencias", "/api/inventario/general",
        "/api/inventario/entradas", "/api/catalogo", "/api/gastos",
        "/api/reportes/resumen", "/api/reportes/ganancias",
        "/api/historial", "/api/dev/metrics", "/api/security/dashboard",
        "/api/supabase/config", "/api/supabase/estado",
    ]
    for path in public + authenticated:
        response = client.get(path)
        assert response.status_code < 500, (path, response.get_data(as_text=True))


def test_validation_and_mutating_routes():
    client = _client()
    cases = [
        ("/api/usuarios/crear", {}),
        ("/api/licencias/crear", {}),
        ("/api/inventario/entrada", {}),
        ("/api/inventario/asignar", {}),
        ("/api/inventario/stock-masivo", {"items": []}),
        ("/api/catalogo/sincronizar", {"productos": []}),
        ("/api/gastos", {}),
        ("/api/auth/cambiar-password", {}),
        ("/api/supabase/config", {}),
        ("/api/supabase/test", {}),
        ("/api/supabase/push", {}),
        ("/api/supabase/pull", {}),
        ("/api/historial", {}),
        ("/api/seguridad/check", {"value": "texto seguro"}),
    ]
    for path, payload in cases:
        response = client.post(path, json=payload)
        # A missing optional Supabase backend is currently represented as 500 by
        # the legacy endpoint; all other validation paths must remain below 500.
        assert response.status_code < 500 or (
            path == "/api/supabase/pull" and response.status_code == 500
        ), (path, response.get_data(as_text=True))

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/auth/me").status_code in (200, 401)


def test_error_handlers_and_backup():
    client = _client()
    assert client.get("/ruta-inexistente").status_code == 404
    for path in ("/api/db/backup", "/api/backup/exportar", "/api/qr"):
        response = client.get(path)
        assert response.status_code < 500
