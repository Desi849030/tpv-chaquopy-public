"""Contract smoke test over every concrete Flask route.

The application has accumulated routes across several blueprints.  Exercising the
actual URL map catches registration/import regressions and verifies every handler
returns a Flask response, including validation/error branches.
"""
from __future__ import annotations

import database
from app import app
from tienda_routes import crear_tablas_tienda


SKIP = {
    "/api/sse",                 # streaming response never terminates by design
    "/api/auth/logout",         # would invalidate the session for later routes
    "/api/backup/auto",         # filesystem maintenance, covered separately
}


def test_all_concrete_route_contracts():
    database.crear_tablas()
    crear_tablas_tienda()
    app.config.update(TESTING=True, SECRET_KEY="route-contract-secret")
    client = app.test_client()
    login = client.post("/api/auth/login", json={
        "username": "desarrollador", "password": "dev2024"
    })
    assert login.status_code == 200

    exercised = set()
    for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
        path = rule.rule
        if "<" in path or path in SKIP or path.startswith("/static/"):
            continue
        if path.startswith("/api/dev/telecom/") and path not in {
            "/api/dev/telecom/red", "/api/dev/telecom/sqlite", "/api/dev/telecom/metodologia"
        }:
            continue
        methods = set(rule.methods) & {"GET", "POST", "PUT", "DELETE"}
        for method in sorted(methods):
            key = (method, path)
            if key in exercised:
                continue
            exercised.add(key)
            response = client.open(path, method=method, json={} if method != "GET" else None)
            assert response.status_code >= 100, key

    # Guard against accidentally collecting an empty or severely reduced URL map.
    assert len(exercised) >= 70
