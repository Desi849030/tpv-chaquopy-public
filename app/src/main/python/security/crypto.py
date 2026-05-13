import hashlib, time, re, uuid, threading, json, base64
from functools import wraps
from datetime import datetime


_rl_store = {}

_rl_lock = threading.Lock()


def rate_limit(max_attempts=5, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            key = request.remote_addr or "unknown"
            now = time.time()
            with _rl_lock:
                if key not in _rl_store:
                    _rl_store[key] = []
                _rl_store[key] = [t for t in _rl_store[key] if now - t < window]
                if len(_rl_store[key]) >= max_attempts:
                    wait = int(window - (now - _rl_store[key][0]))
                    return jsonify({"error": f"Demasiados intentos. Espera {wait}s"}), 429
                _rl_store[key].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ══════════════════════════════════════════════════════════════
#  HASH DE CONTRASEÑAS (SHA-256+salt, sin bcrypt)
# ══════════════════════════════════════════════════════════════

def hash_password(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex[:16]
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password, stored_hash):
    if not stored_hash or '$' not in stored_hash:
        return password == stored_hash
    salt, h = stored_hash.split('$', 1)
    return hash_password(password, salt) == stored_hash


def needs_hash_migration(stored_hash):
    return stored_hash is not None and '$' not in stored_hash and len(stored_hash) < 50

# ══════════════════════════════════════════════════════════════
#  SANITIZACION DE INPUT
# ══════════════════════════════════════════════════════════════
_XSS = re.compile(r'<script|javascript:|on\w+=|<iframe|<object|data:', re.IGNORECASE)
_SQLI_PATTERNS = ["';", "--", "/*", "*/", "xp_", "UNION ", "SELECT ", "INSERT ", "DELETE ", "UPDATE ", "DROP "]


def _get_key():
    global _OBFUSC_KEY
    if _OBFUSC_KEY is None:
        try:
            _OBFUSC_KEY = uuid.uuid4().hex[:32]
        except Exception:
            _OBFUSC_KEY = "tpv_ultra_smart_default_key_32"
    return _OBFUSC_KEY


def cifrar_valor(valor):
    if not valor: return valor
    key = _get_key().encode()
    data = str(valor).encode()
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(xored).decode()


def descifrar_valor(cifrado):
    if not cifrado: return cifrado
    try:
        key = _get_key().encode()
        data = base64.b64decode(cifrado)
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return xored.decode()
    except Exception:
        return None

