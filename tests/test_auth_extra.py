import pytest
from app import app

def test_auth_routes():
    client = app.test_client()
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    assert response.status_code in [200, 401]

def test_auth_logout():
    client = app.test_client()
    response = client.post('/api/auth/logout')
    assert response.status_code in [200, 401]
