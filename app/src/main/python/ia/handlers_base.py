# -*- coding: utf-8 -*-
"""
Handlers Base del Agente
"""
import logging

logger = logging.getLogger(__name__)


def greet(role='cliente', name='amigo'):
    if role == 'administrador':
        return f"¡Hola {name}! Panel de administración activo."
    elif role == 'vendedor':
        return f"¡Hola {name}! Listo para vender."
    else:
        return f"¡Hola {name}! Bienvenido ☕"


def handle_products(role='cliente'):
    return "📦 Consultando productos..."


def handle_stock(role='cliente'):
    if role in ['administrador', 'vendedor']:
        return "📦 Inventario completo disponible."
    else:
        return "📦 Tenemos productos disponibles."


def say_goodbye(name='amigo'):
    return f"¡Hasta luego, {name}! 👋"


def handle_unknown(text):
    return f"No entendí: {text}. ¿Puedes repetir?"
