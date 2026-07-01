"""Ejecuta rutas de app.py."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_all_routes(self):
        from app import app
        c = app.test_client()
        for r in ["/","/api/health","/apk-health","/manifest.json","/service-worker.js","/favicon-32.png","/pwa-icon-192.png","/pwa-icon-512.png"]:
            resp = c.get(r)
            assert resp.status_code in (200, 404)
    def test_headers(self):
        from app import app
        r = app.test_client().get("/api/health")
        for h in ["X-Content-Type-Options","X-Frame-Options","X-XSS-Protection","Referrer-Policy"]:
            assert h in r.headers
    def test_cors(self):
        from app import app
        c = app.test_client()
        for o in ["http://localhost:5000","http://127.0.0.1:5000"]:
            r = c.get("/api/health", headers={"Origin":o})
            assert "Access-Control-Allow-Origin" in r.headers
