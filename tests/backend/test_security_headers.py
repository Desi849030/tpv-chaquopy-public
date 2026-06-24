import pytest,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))
class T:
    def test_xss(self):from app import app;r=app.test_client().get("/api/health");assert "X-XSS-Protection" in r.headers
    def test_frame(self):from app import app;r=app.test_client().get("/api/health");assert r.headers.get("X-Frame-Options")=="SAMEORIGIN"
    def test_hsts(self):from app import app;r=app.test_client().get("/api/health");assert "Strict-Transport-Security" in r.headers
    def test_http(self):from app import app;assert app.config.get("SESSION_COOKIE_HTTPONLY")==True
    def test_same(self):from app import app;assert app.config.get("SESSION_COOKIE_SAMESITE")=="Strict"
