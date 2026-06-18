import os
import sys
import pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

@pytest.fixture
def client_noauth():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_health_endpoint_responde(client_noauth):
    r = client_noauth.get("/health")
    assert r.status_code in (200, 503)
    d = r.get_json()
    assert isinstance(d, dict)
    assert "ok" in d
    assert "status" in d
    assert "db" in d

def test_api_unauthorized_tiene_headers_seguridad(client_noauth):
    r = client_noauth.get("/api/ventas/hoy")
    assert r.status_code == 401
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("Permissions-Policy") is not None
    assert "no-store" in r.headers.get("Cache-Control", "")
