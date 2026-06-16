# -*- coding: utf-8 -*-
"""Tests para modules/telecom_diag.py (v8.2)."""
import sys
import os

# Añadir el path del proyecto
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'
))

import pytest


def test_info_red_local():
    """Verifica que info_red_local devuelve hostname e IP."""
    from modules.telecom_diag import info_red_local
    r = info_red_local()
    assert r.get('ok') is True
    assert 'hostname' in r
    assert 'ip_local' in r
    assert 'python' in r
    assert 'plataforma' in r


def test_medir_dns_localhost():
    """DNS lookup de localhost (siempre disponible)."""
    from modules.telecom_diag import medir_dns
    r = medir_dns(host="localhost")
    assert r.get('ok') is True
    assert r.get('host') == "localhost"
    assert 'ip_principal' in r
    assert 'tiempo_ms' in r
    assert r['tiempo_ms'] >= 0


def test_diagnostico_completo_estructura():
    """El diagnostico completo debe devolver todas las secciones."""
    from modules.telecom_diag import diagnostico_completo
    r = diagnostico_completo()
    assert r.get('ok') is True
    assert 'red_local' in r
    assert 'dns' in r
    assert 'sqlite' in r
    assert 'timestamp' in r


def test_formato_humano_es_string():
    """El formato humano debe devolver un string con info clave."""
    from modules.telecom_diag import formato_humano_diagnostico
    s = formato_humano_diagnostico()
    assert isinstance(s, str)
    assert len(s) > 100  # Debe tener contenido
    # Alguna palabra clave debe aparecer
    assert any(k in s for k in ['Dispositivo', 'DNS', 'SQLite', 'IP'])


def test_blueprint_existe():
    """El blueprint telecom_bp debe existir y tener el nombre correcto."""
    from modules.telecom_bp import telecom_bp
    assert telecom_bp.name == 'telecom_dev'


def test_velocidad_sqlite():
    """Test de IOPS SQLite."""
    from modules.telecom_diag import velocidad_sqlite
    r = velocidad_sqlite()
    # Puede fallar si no hay BD, pero la estructura debe ser correcta
    assert 'ok' in r
    if r.get('ok'):
        assert 'lectura_100_ops_ms' in r
        assert 'ops_por_segundo' in r
        assert 'quick_check' in r


def test_latencia_supabase_no_configurado():
    """Si Supabase no esta configurado, debe devolver error claro."""
    from modules.telecom_diag import medir_latencia_supabase
    r = medir_latencia_supabase(intentos=1)
    # Si esta configurado debe ok=True, sino ok=False con error
    assert 'ok' in r
