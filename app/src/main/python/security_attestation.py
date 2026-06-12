# SIMULADO - PROYECTO ACADÉMICO
# ══════════════════════════════════════════════════════════════
# ⚠️  Este módulo es un PLACEBO con fines demostrativos/académicos.
#     NO realiza atestación real del dispositivo:
#     - El "fingerprint" es os.urandom(32) (aleatorio en cada llamada,
#       no identifica al dispositivo).
#     - Los checks de root/emulador/debug/tampering devuelven siempre
#       False sin inspeccionar nada.
#     - risk_score es siempre 0, por lo que authorize_payment() siempre
#       autoriza.
#     En producción se usaría Play Integrity API / SafetyNet via Chaquopy.
# ══════════════════════════════════════════════════════════════
"""security_attestation.py — MPOC Device Attestation (SIMULADO)"""
from datetime import datetime
import hashlib, os, json, threading

_attestation_log = []
_LOCK = threading.Lock()

def _device_fingerprint():
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

def run_full_attestation(device_info=None):
    with _LOCK:
        fp = _device_fingerprint()
        now = datetime.now().isoformat()
        result = {"device_fingerprint": fp, "timestamp": now, "integrity": "PASS", "checks": {"root": False, "emulator": False, "debug": False, "tampering": False}, "risk_score": 0}
        _attestation_log.append(result)
        return result

def authorize_payment(amount=0):
    att = run_full_attestation()
    if att["risk_score"] < 50:
        return {"authorized": True, "attestation": att, "token_required": amount > 100}
    return {"authorized": False, "reason": "Device integrity check failed", "attestation": att}

def get_attestation_status():
    return {"last_check": _attestation_log[-1] if _attestation_log else None, "total_checks": len(_attestation_log), "device_healthy": True}
