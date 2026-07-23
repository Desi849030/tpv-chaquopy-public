"""Additional behavioural tests for active security helpers and PWA runtime."""
from __future__ import annotations

import json

from flask import Flask, jsonify


def test_crypto_password_cipher_tokens_and_migration(monkeypatch, tmp_path):
    from security import crypto

    stored = crypto.hash_password("StrongTest123!", salt="0123456789abcdef")
    assert crypto.verify_password("StrongTest123!", stored)
    assert not crypto.verify_password("wrong", stored)
    assert crypto.verify_password("legacy", "legacy")
    assert crypto.needs_hash_migration("legacy")
    assert not crypto.needs_hash_migration(stored)

    monkeypatch.setenv("TPV_FILES_DIR", str(tmp_path))
    monkeypatch.setattr(crypto, "_OBFUSC_KEY", None)
    encrypted = crypto.cifrar_valor("secret-value")
    assert encrypted != "secret-value"
    assert crypto.descifrar_valor(encrypted) == "secret-value"
    assert crypto.descifrar_valor("not-valid-base64") is None
    assert crypto.cifrar_valor("") == ""
    assert crypto.descifrar_valor("") == ""
    assert (tmp_path / ".tpv_crypto_key").is_file()

    assert len(crypto.generate_api_key(16)) == 32
    assert crypto.rate_limit_key("client", "login") == "rl:login:client"
    assert len(crypto.get_hmac_key()) == 48
    assert len(crypto.get_jwt_secret()) == 48
    assert len(crypto.get_csrf_token()) == 48
    assert len(crypto.get_session_salt()) == 32


def test_crypto_rate_limit_returns_429(monkeypatch):
    from security import crypto

    crypto._rl_store.clear()
    app = Flask(__name__)

    @app.get("/limited")
    @crypto.rate_limit(max_attempts=2, window=60)
    def limited():
        return jsonify({"ok": True})

    client = app.test_client()
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    blocked = client.get("/limited")
    assert blocked.status_code == 429
    assert "Demasiados" in blocked.get_json()["error"]


def test_het_middleware_blocks_query_and_json_attacks():
    import security_het as het

    het._request_log.clear()
    het._threat_alerts.clear()
    app = Flask(__name__)
    het.create_het_middleware(app)

    @app.route("/echo", methods=["GET", "POST", "OPTIONS"])
    def echo():
        return jsonify({"ok": True})

    client = app.test_client()
    assert client.get("/echo?q=normal").status_code == 200
    assert client.get("/echo?q=1%20OR%201%3D1").status_code == 400
    assert client.post("/echo", json={"name": "<script>alert(1)</script>"}).status_code == 400
    assert client.open("/echo", method="OPTIONS").status_code == 200
    response = client.get("/echo")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_core_security_headers_cors_and_compression():
    from core.security import add_security_headers, setup_compression

    app = Flask(__name__)
    setup_compression(app)

    @app.get("/api/large")
    def large():
        response = jsonify({"payload": "x" * 1200})
        return add_security_headers(response)

    response = app.test_client().get(
        "/api/large",
        headers={"Accept-Encoding": "gzip", "Origin": "http://127.0.0.1:5000"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5000"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_pwa_registration_fallback_routes(monkeypatch, tmp_path):
    from pwa_routes import registrar_pwa

    monkeypatch.chdir(tmp_path)
    app = Flask(__name__)
    registrar_pwa(app)
    client = app.test_client()

    manifest = client.get("/manifest.json")
    assert manifest.status_code == 200
    payload = json.loads(manifest.get_data(as_text=True))
    assert payload["name"] == "TPV Ultra Smart"
    assert payload["display"] == "standalone"

    worker = client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["Service-Worker-Allowed"] == "/"
    assert "self.addEventListener" in worker.get_data(as_text=True)

    icon = client.get("/pwa-icon-192.png")
    assert icon.status_code == 200
    assert icon.mimetype == "image/png"
    assert len(icon.data) > 20
