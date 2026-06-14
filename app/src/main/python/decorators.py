# -*- coding: utf-8 -*-
"""decorators.py — Decoradores de autenticación unificados

Fusiona los anteriores auth_decorator.py y decorators.py en uno solo.
Provee nombres en inglés y español para compatibilidad.
"""
import os
from functools import wraps
from flask import request, jsonify, session, redirect


# ── Helpers ──────────────────────────────────────────────────

def usuario_actual():
    """Devuelve el dict del usuario en sesión o {}."""
    return session.get("usuario", {})


# ── Decoradores principales ─────────────────────────────────

def login_required(f):
    """Verifica que el usuario esté autenticado vía sesión (inglés)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = session.get('usuario')
        if not usuario:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({'error': 'No autorizado', 'code': 'AUTH_REQUIRED'}), 401
            return redirect("/")
        request.current_user = usuario
        # Verificar activo cada 5 min (no en testing)
        if not os.environ.get("TPV_TESTING"):
            _check_active(usuario)
        return f(*args, **kwargs)
    return decorated


# Alias español
requiere_login = login_required


def admin_required(f):
    """Verifica que el usuario sea administrador o desarrollador."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        usuario = session.get('usuario', {})
        if usuario.get('rol') not in ('admin', 'administrador', 'superadmin', 'desarrollador'):
            return jsonify({'error': 'Requiere permisos de administrador',
                            'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated


def role_required(roles):
    """Verifica que el usuario tenga uno de los roles indicados."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            usuario = session.get('usuario', {})
            if usuario.get('rol') not in roles:
                return jsonify({'error': 'Rol no autorizado',
                                'code': 'ROLE_REQUIRED'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# Alias español
def requiere_rol(*roles):
    """Alias español de role_required."""
    return role_required(roles)


# ── Helpers internos ─────────────────────────────────────────

def _check_active(usuario):
    """Cada 5 min verifica en la BD que el usuario siga activo."""
    import time
    uid = usuario.get("usuario_id")
    last_chk = session.get("_active_check_ts", 0)
    if uid and time.time() - last_chk > 300:
        conn = None
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT activo FROM usuarios WHERE usuario_id=?", (uid,)
            ).fetchone()
            if row and row[0] == 1:
                session["_active_check_ts"] = time.time()
            else:
                session.clear()
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
