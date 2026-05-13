"""
╔══════════════════════════════════════════════════════════════╗
║   tienda_routes.py  —  TPV ULTRA SMART  v5.0                ║
║   Clientes con imagen, QR, stock por color en catálogo      ║
╚══════════════════════════════════════════════════════════════╝
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
import uuid, base64, os

from database import (
    obtener_conexion, agregar_log,
    _hash_password, verificar_password
)

# tienda_bp = Blueprint('tienda', __name__)  # REMOVIDO: blueprint viene de routes/tienda_bp.py
from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import *
from routes.tienda_clientes import *
from routes.tienda_productos import *
from routes.tienda_tiendas import *
from routes.tienda_other import *
