from auth_decorator import login_required, admin_required
"""Facade: admin — delega a routes/admin_bp"""
from routes.admin_bp import admin_bp
from routes.admin_helpers import _MODULOS_DISPONIBLES, _PRIVILEGIOS_DEFAULT
