from decorators import login_required
"""ai_modules.py v2.0 — Rutas API IA Edge FIXED
Todas las rutas que el frontend espera, correctamente mapeadas.
"""
from flask import Blueprint, jsonify, request
ai_bp = Blueprint('ai_edge', __name__, url_prefix='/api/ai')


analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
