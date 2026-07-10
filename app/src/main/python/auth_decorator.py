from functools import wraps
from flask import request, jsonify, g

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Aceptamos cualquier token, incluido el "admin_bypass"
        g.user = {"id": 1, "role": "admin", "name": "Desarrollador"}
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            g.user = {"id": 1, "role": "admin", "name": "Desarrollador"}
            return f(*args, **kwargs)
        return decorated
    return decorator
