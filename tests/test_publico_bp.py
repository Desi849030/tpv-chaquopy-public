# -*- coding: utf-8 -*-
"""Tests para modules/publico_bp.py (endpoints publicos sin login)."""
import pytest


def test_blueprint_existe():
    from modules.publico_bp import publico_bp
    assert publico_bp.name == 'publico'


def test_catalogo_publico(client_anon):
    r = client_anon.get('/api/publico/catalogo')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True
    assert 'productos' in data


def test_buscar_publico(client_anon):
    r = client_anon.get('/api/publico/buscar?q=cafe')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True


def test_buscar_consulta_corta(client_anon):
    r = client_anon.get('/api/publico/buscar?q=a')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is False


def test_categorias_publicas(client_anon):
    r = client_anon.get('/api/publico/categorias')
    assert r.status_code == 200
    data = r.get_json()
    assert 'categorias' in data


def test_ofertas_publicas(client_anon):
    r = client_anon.get('/api/publico/ofertas')
    assert r.status_code == 200
    data = r.get_json()
    assert 'ofertas' in data


def test_tiendas_info_publica(client_anon):
    r = client_anon.get('/api/publico/tiendas-info')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True
    assert 'tiendas' in data
