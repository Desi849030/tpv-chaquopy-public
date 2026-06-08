# -*- coding: utf-8 -*-
"""async_sync.py - Wrapper threading para Supabase sync no bloqueante.
Ejecuta sincronizacion en background para no bloquear Flask."""
import threading
import time
import traceback
from datetime import datetime

_sync_lock = threading.Lock()
_sync_active = False
_last_sync = None
_last_result = None

def sync_in_background(estado=None, callback=None):
    global _sync_active, _last_sync, _last_result
    if _sync_active:
        return {"ok": False, "mensaje": "Sync ya en progreso"}
    def _worker():
        global _sync_active, _last_sync, _last_result
        with _sync_lock:
            _sync_active = True
        try:
            from sync.supabase_sync import sincronizar_todo
            if estado:
                from sync.supabase_sync import guardar_en_supabase
                guardar_en_supabase(estado)
            result = sincronizar_todo()
            _last_sync = datetime.now().isoformat()
            _last_result = result
            if callback:
                try: callback(result)
                except: pass
        except Exception as e:
            _last_result = {"ok": False, "mensaje": str(e)}
            traceback.print_exc()
        finally:
            with _sync_lock:
                _sync_active = False
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return {"ok": True, "mensaje": "Sync iniciado en background"}

def get_sync_status():
    return {
        "active": _sync_active,
        "last_sync": _last_sync,
        "last_result_ok": _last_result.get("ok") if _last_result else None,
    }
