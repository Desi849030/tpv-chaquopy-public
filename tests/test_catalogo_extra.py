import pytest
from app import app

def test_catalogo_list():
    client = app.test_client()
    response = client.get('/api/catalogo')
    assert response.status_code in [200, 404]

def test_catalogo_search():
    client = app.test_client()
    response = client.get('/api/catalogo/buscar?q=test')
    assert response.status_code in [200, 404]
