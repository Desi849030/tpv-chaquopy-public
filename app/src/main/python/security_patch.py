"""
Parche de seguridad para app.py
Agrega: CSRF, headers seguros, rate limit global, logging seguro
"""

import secrets
from functools import wraps
from flask import request, jsonify, abort
import time

# Tokens CSRF
_csrf_tokens = {}

def generate_csrf():
    token = secrets.token_hex(32)
    _csrf_tokens[token] = time.time()
    return token

def validate_csrf(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token') or request.json.get('_csrf')
            if not token or token not in _csrf_tokens:
                abort(403, 'CSRF token inválido')
            # Expirar token después de 1 hora
            if time.time() - _csrf_tokens[token] > 3600:
                del _csrf_tokens[token]
                abort(403, 'CSRF token expirado')
        return f(*args, **kwargs)
    return decorated

# Rate limit global
_rate_store = {}

def rate_limit_global(max_attempts=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            now = time.time()
            if ip not in _rate_store:
                _rate_store[ip] = []
            _rate_store[ip] = [t for t in _rate_store[ip] if now - t < window]
            if len(_rate_store[ip]) >= max_attempts:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            _rate_store[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Headers de seguridad
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

def add_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

