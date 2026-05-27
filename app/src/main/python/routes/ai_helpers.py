from auth_decorator import login_required
from decorators import requiere_login
"""ai_routes.py v2.0 — Rutas API IA Edge FIXED
Todas las rutas que el frontend espera, correctamente mapeadas.
"""
from flask import Blueprint, jsonify, request
ai_bp = Blueprint('ai_edge', __name__, url_prefix='/api/ai')


analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
