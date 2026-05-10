"""security.py — Generacion dinamica de secretos v2.3.0
Evita almacenar secretos en el repo. Se generan en runtime
y se guardan en el almacenamiento interno de la app.
"""
import os, secrets, hashlib, json, re as _re

_SECRETS_FILE = None
_SECRETS = {}

def _get_secrets_path():
    global _SECRETS_FILE
    if _SECRETS_FILE is None:
        base = os.environ.get("ANDROID_DATA", "")
        if base:
            _SECRETS_FILE = os.path.join(base, ".tpv_secrets_v2")
        else:
            _SECRETS_FILE = os.path.join(os.path.expanduser("~"), ".tpv_secrets_v2")
    return _SECRETS_FILE

def _load_or_generate():
    global _SECRETS
    if _SECRETS:
        return _SECRETS
    path = _get_secrets_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                _SECRETS = json.load(f)
            return _SECRETS
        except (json.JSONDecodeError, IOError):
            pass
    _SECRETS = {
        "hmac_key": secrets.token_hex(32),
        "jwt_secret": secrets.token_hex(32),
        "csrf_token": secrets.token_hex(16),
        "session_salt": secrets.token_hex(16),
    }
    try:
        with open(path, "w") as f:
            json.dump(_SECRETS, f)
        os.chmod(path, 0o600)
    except OSError:
        pass
    return _SECRETS

def get_hmac_key():
    return _load_or_generate().get("hmac_key", "")

def get_jwt_secret():
    return _load_or_generate().get("jwt_secret", "")

def get_csrf_token():
    return _load_or_generate().get("csrf_token", "")

def get_session_salt():
    return _load_or_generate().get("session_salt", "")

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return "%s:$%s" % (salt, h.hex())

def verify_password(password, stored_hash):
    try:
        salt, h = stored_hash.split(":$", 1)
        h2 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(h, h2.hex())
    except (ValueError, AttributeError):
        return False

def sanitize_input(text):
    if not isinstance(text, str):
        return str(text)
    text = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()

def validate_email(email):
    if not email:
        return False
    return bool(_re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))

def generate_api_key(length=32):
    return secrets.token_urlsafe(length)

def rate_limit_key(client_id, action="api"):
    return "rl:%s:%s" % (action, client_id)
