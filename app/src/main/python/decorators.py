# -*- coding: utf-8 -*-
"""decorators.py v8.0 - Verificacion atomica por usuario (sin cache)."""
import os
from functools import wraps
from flask import request, jsonify, session, redirect


def usuario_actual():
    return session.get("usuario", {})


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = session.get('usuario')
        token_sesion = session.get('session_token')
        if not usuario or not token_sesion:
            session.clear()
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({'error': 'No autorizado', 'code': 'AUTH_REQUIRED'}), 401
            return redirect("/")
        token_usuario = usuario.get('session_token')
        if token_usuario and token_usuario != token_sesion:
            session.clear()
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({'error': 'Sesion invalida', 'code': 'SESSION_MISMATCH'}), 401
            return redirect("/")
        request.current_user = usuario
        if not os.environ.get("TPV_TESTING"):
            if not _check_active_atomic(usuario):
                session.clear()
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({'error': 'Usuario inactivo', 'code': 'USER_INACTIVE'}), 401
                return redirect("/")
        return f(*args, **kwargs)
    return decorated


requiere_login = login_required


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        usuario = session.get('usuario', {})
        if usuario.get('rol') not in ('admin', 'administrador', 'superadmin', 'desarrollador'):
            return jsonify({'error': 'Requiere permisos de administrador', 'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated


def role_required(roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            usuario = session.get('usuario', {})
            if usuario.get('rol') not in roles:
                return jsonify({'error': 'Rol no autorizado', 'code': 'ROLE_REQUIRED'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def requiere_rol(*roles):
    return role_required(roles)


def _check_active_atomic(usuario):
    uid = usuario.get("usuario_id")
    if not uid:
        return False
    conn = None
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        row = conn.execute("SELECT activo FROM usuarios WHERE usuario_id=?", (uid,)).fetchone()
        return bool(row and row[0] == 1)
    except Exception:
        return True
    finally:
        if conn:
            try: conn.close()
            except Exception: pass
