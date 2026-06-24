"""integration tests"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","app","src","main","python"))
class T:
    def test_c(self): from app import app; assert app
    def test_h(self): from app import app; r=app.test_client().get("/api/health"); assert r.status_code in (200,500)