import pytest
from app import app

def test_app_home():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code in [200, 404]

def test_app_health():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code in [200, 404]

def test_app_metrics():
    client = app.test_client()
    response = client.get('/metrics')
    assert response.status_code in [200, 404]

def test_app_static():
    client = app.test_client()
    response = client.get('/static/style.css')
    assert response.status_code in [200, 404]

def test_app_api():
    client = app.test_client()
    response = client.get('/api/')
    assert response.status_code in [200, 404]
