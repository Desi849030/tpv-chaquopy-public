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

from routes.tienda_helpers import tienda_bp
