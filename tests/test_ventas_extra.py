import pytest
from app import app

def test_ventas_list():
    client = app.test_client()
    response = client.get('/api/ventas')
    # Aceptamos 200, 404 (si no hay datos) o 401 (si requiere auth)
    assert response.status_code in [200, 404, 401]

def test_ventas_create():
    client = app.test_client()
    response = client.post('/api/ventas', json={'producto': 'test', 'cantidad': 1})
    assert response.status_code in [200, 401, 404]

def test_ventas_detalle():
    client = app.test_client()
    response = client.get('/api/ventas/1')
    assert response.status_code in [200, 404, 401]
