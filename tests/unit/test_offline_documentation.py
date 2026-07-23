"""Tests for documentation packaged and readable by the developer IA."""
from __future__ import annotations

import database
from app import app
from documentation_loader import available_document_names, find_document, sync_documentation


def test_documentation_sync_is_idempotent_and_contains_developer_policy():
    database.crear_tablas()
    conn = database.obtener_conexion()
    try:
        first = sync_documentation(conn)
        second = sync_documentation(conn)
        assert first >= 2
        assert second == first
        names = available_document_names(conn)
        assert "README.md" in names
        assert "docs/DEVELOPER_GUIDE.md" in names
        assert "docs/ROADMAP_10_10.md" in names
        assert "DEVELOPER_GUIDE.md" not in names
        assert "docs/DEFENSA.md" in names
        assert "docs/openapi.yaml" in names
        assert find_document(conn, "leer documento defensa")[0] == "docs/DEFENSA.md"
        row = conn.execute(
            "SELECT contenido, lineas FROM documentacion WHERE nombre=?",
            ("DEVELOPER_GUIDE.md",),
        ).fetchone()
        assert row is not None
        content = row["contenido"].lower()
        assert "sin límites" in content or "sin limites" in content
        assert "access: [\"all\"]" in content or "capacidad es `all`" in content
        assert row["lineas"] > 10
    finally:
        conn.close()


def test_docs_catalog_api_is_developer_only():
    database.crear_tablas()
    app.config.update(TESTING=True, SECRET_KEY="docs-test-secret")
    assert app.test_client().get("/api/dev/docs/catalog").status_code in (401, 403)


def test_developer_can_read_guide_through_agent_endpoint():
    database.crear_tablas()
    app.config.update(TESTING=True, SECRET_KEY="docs-test-secret")
    client = app.test_client()
    login = client.post("/api/auth/login", json={
        "username": "desarrollador",
        "password": "dev2024",
    })
    assert login.status_code == 200

    response = client.post("/api/agent/chat", json={
        "mensaje": "leer documento desarrollador",
    })
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["tipo"] == "documento"
    assert "DEVELOPER_GUIDE.md" in payload["respuesta"]
    continuation = client.post("/api/agent/chat", json={"mensaje": "siguiente"}).get_json()
    assert continuation["tipo"] == "documento"
    assert "página 2/" in continuation["respuesta"]

    arbitrary = client.post("/api/agent/chat", json={
        "mensaje": "leer documento defensa",
    }).get_json()
    assert arbitrary["tipo"] == "documento"
    assert "docs/DEFENSA.md" in arbitrary["respuesta"]

    inventory = client.post("/api/agent/chat", json={
        "mensaje": "todos los documentos",
    }).get_json()
    assert inventory["tipo"] == "docs_catalog"
    assert inventory["rol"] == "desarrollador"
    assert inventory["total_documentos"] >= 20
    names = [item["nombre"] for item in inventory["documentos"]]
    assert len(names) == len(set(names)) == inventory["total_documentos"]
    assert "docs/DEVELOPER_GUIDE.md" in names
    assert "DEVELOPER_GUIDE.md" not in names
    assert "docs/TELECOM_ENGINEERING.md" in names
    assert "docs/STATE_OF_THE_ART.md" in names
    hashes = [item["sha256"] for item in inventory["documentos"]]
    assert len(hashes) == len(set(hashes))
    assert all("lineas" in item and "categoria" in item for item in inventory["documentos"])

    api_catalog = client.get("/api/dev/docs/catalog")
    assert api_catalog.status_code == 200
    assert api_catalog.get_json()["total_documentos"] == inventory["total_documentos"]
