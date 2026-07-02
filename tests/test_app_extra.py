import pytest
from app import app

def test_app_existe():
    assert app is not None

def test_app_config():
    assert app.config is not None

def test_app_testing():
    assert app.testing is True

def test_app_routes():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code in [200, 404]
