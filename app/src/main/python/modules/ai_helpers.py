# -*- coding: utf-8 -*-
"""ai_helpers.py — Blueprints y re-exports para módulos AI Edge"""
from flask import Blueprint, jsonify, request
from decorators import login_required

# Alias para compatibilidad con sub-módulos que importan requiere_login
requiere_login = login_required

ai_bp = Blueprint('ai_edge', __name__, url_prefix='/api/ai')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
