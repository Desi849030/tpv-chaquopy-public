# -*- coding: utf-8 -*-
"""decorators.py - TPV Ultra Smart - Decoradores compartidos"""
from functools import wraps
from flask import request, jsonify, session, redirect

def requiere_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "No autenticado"}), 401
            return redirect("/")
        return f(*args, **kwargs)
    return decorated

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            u = session.get("usuario", {})
            if u.get("rol") not in roles:
                return jsonify({"error": "Sin permisos"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def usuario_actual():
    return session.get("usuario", {})

print("[decorators.py] Decoradores cargados")
