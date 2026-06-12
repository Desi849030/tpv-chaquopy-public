import hashlib, time, re, uuid, threading, json, base64
from functools import wraps
from datetime import datetime



def registrar_auditoria(app_instance):
    @app_instance.before_request
    def audit_log():
        from flask import request, session
        try:
            path = request.path
            if any(path.startswith(r) for r in _RUTAS_AUDIT):
                u = session.get('usuario', {})
                entry = {
                    "ts": datetime.now().isoformat(),
                    "user": u.get('usuario_id', 'anon'),
                    "rol": u.get('rol', '-'),
                    "method": request.method,
                    "path": path,
                    "ip": request.remote_addr,
                }
                try:
                    from db_connection import agregar_log
                    agregar_log(f"AUDIT:{json.dumps(entry, ensure_ascii=False)}", "info")
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
        except Exception:  # noqa: broad-except - graceful degradation
            pass
# ══════════════════════════════════════════════════════════════
#  CIFRADO LIVIANO PARA DATOS SENSIBLES (offline-safe)
# ══════════════════════════════════════════════════════════════
_OBFUSC_KEY = None


