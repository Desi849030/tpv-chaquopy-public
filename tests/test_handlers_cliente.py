# -*- coding: utf-8 -*-
"""Tests del handler universal de cliente (gestor v8.9)."""
import pytest


def test_import_handler():
    from ia.handlers_cliente import handle_cliente
    assert callable(handle_cliente)


def test_normalizar_tildes():
    from ia.handlers_cliente import _normalizar
    assert _normalizar("Cafe") == "cafe"


def test_extraer_producto():
    from ia.handlers_cliente import _extraer_producto
    assert "cafe" in _extraer_producto("cuanto cuesta el cafe")


def test_buscar_productos_devuelve_lista():
    from ia.handlers_cliente import _buscar_productos
    items = _buscar_productos("cafe")
    assert isinstance(items, list)


def test_handle_cliente_saludo():
    from ia.handlers_cliente import handle_cliente
    r = handle_cliente(None, "hola", None)
    assert isinstance(r, str)
    assert len(r) > 10


def test_handle_cliente_ayuda():
    from ia.handlers_cliente import handle_cliente
    r = handle_cliente(None, "ayuda", None)
    assert isinstance(r, str)


def test_handle_cliente_categorias():
    from ia.handlers_cliente import handle_cliente
    r = handle_cliente(None, "categorias", None)
    assert isinstance(r, str)


def test_handle_cliente_default():
    from ia.handlers_cliente import handle_cliente
    r = handle_cliente(None, "blah xyz", None)
    assert isinstance(r, str)
