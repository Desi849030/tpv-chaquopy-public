def test_app_import():
    from app import app
    assert app is not None

def test_health():
    from app import app
    c = app.test_client()
    r = c.get('/api/health')
    assert r.status_code == 200
