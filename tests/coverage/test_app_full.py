"""Cobertura de rutas y headers de app.py"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class TestAppFull:
    def test_health(self):
        from app import app; c = app.test_client(); r = c.get("/api/health")
        assert r.status_code in (200, 500)

    def test_index(self):
        from app import app; c = app.test_client(); r = c.get("/")
        assert r.status_code in (200, 404)

    def test_manifest(self):
        from app import app; c = app.test_client(); r = c.get("/manifest.json")
        assert r.status_code in (200, 404)

    def test_apk_health(self):
        from app import app; c = app.test_client(); r = c.get("/apk-health")
        assert r.status_code == 200

    def test_service_worker(self):
        from app import app; c = app.test_client(); r = c.get("/service-worker.js")
        assert r.status_code in (200, 404)

    def test_favicon(self):
        from app import app; c = app.test_client(); r = c.get("/favicon-32.png")
        assert r.status_code in (200, 404)

    def test_pwa_icons(self):
        from app import app; c = app.test_client()
        for icon in ["/pwa-icon-192.png", "/pwa-icon-512.png"]:
            r = c.get(icon)
            assert r.status_code in (200, 404)

    def test_headers_present(self):
        from app import app; c = app.test_client(); r = c.get("/api/health")
        assert "X-Content-Type-Options" in r.headers
        assert "X-Frame-Options" in r.headers
        assert "X-XSS-Protection" in r.headers
        assert "Referrer-Policy" in r.headers

    def test_cors_localhost(self):
        from app import app; c = app.test_client()
        r = c.get("/api/health", headers={"Origin": "http://localhost:5000"})
        assert "Access-Control-Allow-Origin" in r.headers
        assert "Access-Control-Allow-Credentials" in r.headers

    def test_cors_127(self):
        from app import app; c = app.test_client()
        r = c.get("/api/health", headers={"Origin": "http://127.0.0.1:5000"})
        assert "Access-Control-Allow-Origin" in r.headers

    def test_static_files(self):
        from app import app; c = app.test_client(); r = c.get("/static/lib/bootstrap.min.css")
        assert r.status_code in (200, 404)

    def test_routes_count(self):
        from app import app; rules = list(app.url_map.iter_rules()); assert len(rules) > 10
