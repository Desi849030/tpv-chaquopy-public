# -*- coding: utf-8 -*-
import os
from functools import wraps
from flask import request, jsonify, session, redirect

def usuario_actual():
    """Retorna el diccionario del usuario en sesión."""
    return session.get("usuario", {})

def login_required(f):
    """Decorator para rutas que requieren estar autenticado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = session.get('usuario')
        token_sesion = session.get('session_token')
        if not usuario or not token_sesion:
            session.clear()
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({'error': 'No autorizado', 'code': 'AUTH_REQUIRED'}), 401
            return redirect("/")
        
        # Validación de token único (evita sesiones concurrentes si el token cambió)
        token_usuario = usuario.get('session_token')
        if token_usuario and token_usuario != token_sesion:
            session.clear()
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({'error': 'Sesion invalida', 'code': 'SESSION_MISMATCH'}), 401
            return redirect("/")
            
        request.current_user = usuario
        return f(*args, **kwargs)
    return decorated

# Alias comunes usados en tus módulos
requiere_login = login_required

def requiere_rol(*roles):
    """Decorator para rutas que requieren roles específicos (admin, vendedor, etc)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            usuario = session.get('usuario')
            if not usuario or usuario.get('rol') not in roles:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({'error': 'Permiso denegado', 'code': 'FORBIDDEN'}), 403
                return redirect("/")
            return f(*args, **kwargs)
        return login_required(decorated)
    return decorator

def admin_required(f):
    """Shorthand para rutas que solo admin o desarrollador pueden ver."""
    return requiere_rol('administrador', 'desarrollador')(f)

def _check_active_atomic(usuario):
    """Verificación rápida de si el usuario sigue activo en la DB."""
    try:
        from db_connection import get_db_connection
        with get_db_connection() as conn:
            user = conn.execute("SELECT activo FROM usuarios WHERE usuario_id = ?", 
                             (usuario.get('usuario_id'),)).fetchone()
            return user and user[0] == 1
    except:
        return True # En caso de error, permitimos para no bloquear el sistema
