"""
Decorador de autenticación centralizado
"""
from functools import wraps
from flask import request, jsonify, session
from security import verify_password, get_jwt_secret
import hashlib

def login_required(f):
    """Verifica que el usuario esté autenticado vía sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar sesión
        usuario = session.get('usuario')
        if not usuario:
            return jsonify({'error': 'No autorizado', 'code': 'AUTH_REQUIRED'}), 401
        
        # Agregar usuario al request
        request.current_user = usuario
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Verifica que el usuario sea administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        usuario = session.get('usuario', {})
        if usuario.get('rol') not in ['admin', 'administrador', 'superadmin']:
            return jsonify({'error': 'Requiere permisos de administrador', 'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Verifica que el usuario tenga uno de los roles permitidos"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            usuario = session.get('usuario', {})
            if usuario.get('rol') not in roles:
                return jsonify({'error': 'Rol no autorizado', 'code': 'ROLE_REQUIRED'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def csrf_protected(f):
    """Verifica token CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token') or request.json.get('_csrf_token', '')
            stored = session.get('csrf_token', '')
            if not token or token != stored:
                return jsonify({'error': 'CSRF inválido', 'code': 'CSRF_INVALID'}), 403
        return f(*args, **kwargs)
    return decorated_function
