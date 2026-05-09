"""
payment_tokenizer.py v1.0 - TPV Ultra Smart
Tokenización de datos de pago en tiempo real
Cumple con MPOC - Nunca almacena datos reales de tarjeta
"""
import hashlib, hmac, os, json, time, uuid
from datetime import datetime

# Clave secreta para HMAC (generada por dispositivo)
_SECRET_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), ".tpv_hmac_secret")
def _load_or_create_secret():
    if os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "rb") as f:
            data = f.read()
        if len(data) == 64:
            return data
    secret = hashlib.sha256(os.urandom(64)).digest()
    try:
        with open(_SECRET_FILE, "wb") as f:
            f.write(secret)
    except Exception:
        pass
    return secret
_SECRET = _load_or_create_secret()

def tokenize(card_data: str) -> dict:
    """
    Convierte datos sensibles de pago en token no reversible.
    
    Args:
        card_data: Últimos 4 dígitos o referencia de pago
    
    Returns:
        dict con token, hash y timestamp
    """
    salt = os.urandom(32)
    timestamp = str(int(time.time()))
    
    # Crear token único
    raw = f"{card_data}:{timestamp}:{salt.hex()}"
    token = hashlib.blake2b(raw.encode(), digest_size=32).hexdigest()
    
    # HMAC para verificación
    signature = hmac.new(_SECRET, token.encode(), hashlib.sha256).hexdigest()
    
    return {
        "token": token[:16],
        "signature": signature[:16],
        "timestamp": timestamp,
        "type": "one_time"
    }

def verify_token(token: str, signature: str) -> bool:
    """Verifica que un token sea válido"""
    expected = hmac.new(_SECRET, token.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected[:16], signature[:16])

def mask_card(number: str) -> str:
    """Enmascara número de tarjeta: ****-****-****-1234"""
    if not number or len(number) < 4:
        return "****"
    return f"****-****-****-{number[-4:]}"

def create_payment_record(amount: float, method: str, card_ref: str = "") -> dict:
    """
    Crea registro de pago tokenizado para almacenar en SQLite.
    Nunca guarda el número real de tarjeta.
    """
    token_info = tokenize(card_ref or str(uuid.uuid4().hex[:8]))
    
    return {
        "payment_id": f"pay-{uuid.uuid4().hex[:10]}",
        "amount": amount,
        "method": method,
        "card_masked": mask_card(card_ref) if card_ref else None,
        "token": token_info["token"],
        "signature": token_info["signature"],
        "timestamp": datetime.now().isoformat(),
        "verified": False
    }

print("✅ payment_tokenizer.py v1.0 listo - Tokenización MPOC activa")
