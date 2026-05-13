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
        u = session.get("usuario", {})
        uid = u.get("usuario_id")
        last_chk = session.get("_active_check_ts", 0)
        import time as _t
        if uid and _t.time() - last_chk > 300:
            try:
                from db.users import login_usuario
                _conn = None
                try:
                    from database import obtener_conexion as _oc
                    _conn = _oc()
                    _row = _conn.execute(
                        "SELECT activo FROM usuarios WHERE usuario_id=?",
                        (uid,)
                    ).fetchone()
                    if _row and _row[0] == 1:
                        session["_active_check_ts"] = _t.time()
                    else:
                        session.clear()
                        return jsonify({"error": "Sesion revocada"}), 401
                finally:
                    if _conn:
                        try: _conn.close()
                        except: pass
            except Exception:
                pass
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
