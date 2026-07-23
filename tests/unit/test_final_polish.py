"""Final UI/UX and backend hardening acceptance tests."""
from __future__ import annotations

from pathlib import Path

from app import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "app/src/main/assets/frontend"


def test_final_assets_are_linked_and_syntactically_present():
    index = (FRONTEND / "templates/index.html").read_text(encoding="utf-8")
    assert '/static/css/final-polish.css' in index
    assert '/static/js/final-polish.js' in index
    css = (FRONTEND / "static/css/final-polish.css").read_text(encoding="utf-8")
    for requirement in (
        "focus-visible", "prefers-reduced-motion", "prefers-contrast",
        "safe-area-inset-bottom", "min-height: 44px", "@media (max-width: 767.98px)",
    ):
        assert requirement in css
    javascript = (FRONTEND / "static/js/final-polish.js").read_text(encoding="utf-8")
    for requirement in (
        "aria-live", "MutationObserver", "navigator.onLine",
        "visibilitychange", "localBackendAvailable", "TPV_UX",
    ):
        assert requirement in javascript


def test_frontend_serves_new_assets_and_responsive_document():
    app.config.update(TESTING=True, SECRET_KEY="polish-test")
    client = app.test_client()
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'name="viewport"' in html
    assert client.get("/static/css/final-polish.css").status_code == 200
    assert client.get("/static/js/final-polish.js").status_code == 200


def test_security_headers_and_api_cache_policy():
    app.config.update(TESTING=True, SECRET_KEY="polish-test")
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "geolocation=()" in response.headers["Permissions-Policy"]
    assert response.headers["Cache-Control"] == "no-store, max-age=0"
    assert response.headers["Pragma"] == "no-cache"
    assert "tamano_kb" in response.get_json()["db_info"]


def test_upload_limit_and_cookie_defaults():
    assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024 * 1024
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
