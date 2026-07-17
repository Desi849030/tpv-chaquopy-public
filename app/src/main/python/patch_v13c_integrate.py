#!/usr/bin/env python3
"""
patch_v13c_integrate.py — Integra modulos v13 en agent.py y db_utils.py
(v13c: elimina 1G-a/b que causaban IndentationError; budget ya va por 1F en _r())

Ejecutar en Termux:
  cd ~/tpv-chaquopy-public/app/src/main/python
  cp ia/backup_v13b/agent.py.bak_20260717_125454 ia/agent.py
  cp ia/backup_v13b/db_utils.py.bak_20260717_125454 ia/db_utils.py
  python patch_v13c_integrate.py
"""

import os, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
IA_DIR = os.path.join(BASE, "ia")

def backup(fp):
    d = os.path.join(IA_DIR, "backup_v13c")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(fp) + ".bak_" + datetime.now().strftime('%Y%m%d_%H%M%S'))
    shutil.copy2(fp, dst)
    print(f"  [BACKUP] {os.path.basename(fp)}")

def readf(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def writef(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)

def syntax(p):
    import py_compile
    try:
        py_compile.compile(p, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  [SYNTAX ERROR] {os.path.basename(p)}: {e}")
        return False


def patch_agent():
    fp = os.path.join(IA_DIR, "agent.py")
    if not os.path.exists(fp):
        print("  [SKIP] agent.py no encontrado"); return False
    backup(fp)
    code = readf(fp)
    orig = code
    n = 0

    # 1A: imports v13
    a = "    _HAS_ANTI_SLOP = False"
    b = """
# --- v13 Architecture Modules (safe fallback) ---
try:
    from ia.intent_router import get_router as _get_v13_router
    from ia.compaction import compact_history as _v13_compact, Message as _v13_msg
    from ia.denial_tracking import get_tracker as _get_v13_tracker
    from ia.error_formatter import get_error_formatter as _get_v13_efmt
    from ia.hooks import (get_hook_pipeline as _get_v13_hooks,
                          HookPoint as _v13_hp, HookContext as _v13_hctx)
    from ia.response_budget import get_budget as _get_v13_budget, BudgetMode as _v13_bm
    from ia.result_cache import get_cache as _get_v13_cache
    _HAS_V13 = True
except Exception:
    _HAS_V13 = False"""
    if a in code:
        code = code.replace(a, a + b, 1); n += 1; print("  [1A] Imports v13 OK")

    # 1B: init v13 en __init__
    a = "        self._as_ok = _HAS_ANTI_SLOP"
    b = """
        # v13 modules
        self._v13_ok = _HAS_V13
        if _HAS_V13:
            self._v13_tracker = _get_v13_tracker()
            self._v13_hooks = _get_v13_hooks()
            self._v13_budget = _get_v13_budget()
            self._v13_efmt = _get_v13_efmt()"""
    if a in code:
        code = code.replace(a, a + b, 1); n += 1; print("  [1B] Init v13 OK")

    # 1C: pre-process hooks
    a = "        # === AGENTIC PIPELINE ==="
    b = """        # v13: Pre-processing hooks
        if self._v13_ok:
            try:
                hctx = _v13_hctx(hook_point=_v13_hp.PRE_PROCESS, agent=self, text=t, role=role)
                hr = self._v13_hooks.execute(_v13_hp.PRE_PROCESS, hctx)
                if hr.modified_text:
                    t = hr.modified_text
                if hr.override:
                    return self._r(hr.override, role, 'HOOK_OVERRIDE')
            except Exception:
                pass

"""
    if a in code:
        code = code.replace(a, b + a, 1); n += 1; print("  [1C] Pre-hooks OK")

    # 1D: compaction
    old = """        if len(m['h']) > 20:
            m['h'] = m['h'][-20:]"""
    new = """        # v13: Smart compaction (replaces simple truncation)
        if self._v13_ok and len(m['h']) > 40:
            try:
                msgs = [_v13_msg(role='user', content=h) for h in m['h']]
                cr = _v13_compact(msgs, max_messages=30)
                m['h'] = [msg.content for msg in cr.messages if msg.role == 'user']
            except Exception:
                m['h'] = m['h'][-20:]
        elif len(m['h']) > 20:
            m['h'] = m['h'][-20:]"""
    if old in code:
        code = code.replace(old, new, 1); n += 1; print("  [1D] Compaction OK")

    # 1E: dispatch con error handling
    old = """        # === DISPATCH POR ROL ===
        if role == 'cliente':
            result = handle_cliente(self, t, m)
        elif role == 'vendedor':
            result = handle_vendedor(self, t, m)
        elif role == 'cajero':
            result = handle_cajero(self, t, m)
        elif role == 'supervisor':
            result = handle_supervisor(self, t, m)
        elif role == 'administrador':
            result = handle_admin(self, t, name)
        else:
            result = handle_dev(self, t, name)"""
    new = """        # === DISPATCH POR ROL (v13: error formatter + denial tracking) ===
        result = ''
        try:
            if role == 'cliente':
                result = handle_cliente(self, t, m)
            elif role == 'vendedor':
                result = handle_vendedor(self, t, m)
            elif role == 'cajero':
                result = handle_cajero(self, t, m)
            elif role == 'supervisor':
                result = handle_supervisor(self, t, m)
            elif role == 'administrador':
                result = handle_admin(self, t, name)
            else:
                result = handle_dev(self, t, name)
            if self._v13_ok:
                self._v13_tracker.record_success()
        except Exception as _e:
            result = ''
            if self._v13_ok:
                self._v13_tracker.record_failure(str(_e))
                try:
                    _fe = self._v13_efmt.format(_e, context={'role': role, 'text': t[:100]})
                    result = _fe.to_user_string()
                except Exception:
                    result = 'Lo siento, ocurrio un error procesando tu solicitud.'
                if self._v13_tracker.state.is_stuck:
                    _rec = self._v13_tracker.get_recovery_message()
                    if _rec:
                        result = _rec
            else:
                result = 'Lo siento, ocurrio un error procesando tu solicitud.'"""
    if old in code:
        code = code.replace(old, new, 1); n += 1; print("  [1E] Dispatch + error handling OK")

    # 1F: response budget en _r()
    a = """        return {
            'answer': msg,
            'role': role,
            'suggestions': suggestions,
            'intent': intent,
            'ts': datetime.now().isoformat(),
        }"""
    b = """        # v13: Apply response budget
        if self._v13_ok:
            try:
                msg = self._v13_budget.apply(msg, mode=_v13_bm.NORMAL)
            except Exception:
                pass
""" + a
    if a in code:
        code = code.replace(a, b, 1); n += 1; print("  [1F] Response budget OK")

    # NOTA: 1G-a/b omitidos intencionalmente.
    # El response budget ya se aplica via 1F en _r(), que es llamado
    # tanto por el camino agentic como el classic en process_question().

    if code != orig:
        writef(fp, code)
        print(f"\n  agent.py: {n} cambios, sintaxis ", end="")
        return syntax(fp)
    return True


def patch_db():
    fp = os.path.join(IA_DIR, "db_utils.py")
    if not os.path.exists(fp):
        print("  [SKIP] db_utils.py"); return False
    backup(fp)
    code = readf(fp)
    orig = code
    n = 0

    # 2A: import cache
    a = 'def q(sql, params=(), one=False):'
    b = """# v13: Query result cache
try:
    from ia.result_cache import get_cache as _get_qcache
    _HAS_QCACHE = True
    _qcache = _get_qcache() if _HAS_QCACHE else None
except Exception:
    _HAS_QCACHE = False
    _qcache = None

""" + a
    if a in code:
        code = code.replace(a, b, 1); n += 1; print("  [2A] Import cache OK")

    # 2B: reemplazar q()
    old = '''def q(sql, params=(), one=False):
    """Execute query and return results."""
    c = _db()
    if not c:
        return None
    try:
        cur = c.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
    except:
        return None
    finally:
        try: c.close()
        except: pass'''
    new = '''def q(sql, params=(), one=False):
    """Execute query and return results."""
    _sql_up = sql.strip().upper()
    _is_select = _sql_up.startswith("SELECT")
    if _is_select and _HAS_QCACHE and _qcache is not None:
        _cached = _qcache.get(sql, params)
        if _cached is not None:
            return _cached[0] if one else _cached
    c = _db()
    if not c:
        return None
    try:
        cur = c.execute(sql, params)
        if _is_select:
            rows = cur.fetchall()
            if _HAS_QCACHE and _qcache is not None and rows:
                _qcache.set(sql, rows, params, ttl=30.0)
            return rows[0] if one and rows else (rows if rows else None)
        else:
            if _HAS_QCACHE and _qcache is not None:
                _qcache.invalidate()
            return cur.fetchone() if one else cur.fetchall()
    except:
        return None
    finally:
        try: c.close()
        except: pass'''
    if old in code:
        code = code.replace(old, new, 1); n += 1; print("  [2B] q() con cache OK")

    if code != orig:
        writef(fp, code)
        print(f"\n  db_utils.py: {n} cambios, sintaxis ", end="")
        return syntax(fp)
    return True


def main():
    print("=" * 55)
    print("  PATCH v13c — Integracion v13 (sin 1G)")
    print("=" * 55 + "\n")
    r1 = patch_agent()
    print()
    r2 = patch_db()
    print("\n" + "=" * 55)
    if r1 and r2:
        print("  OK — 6 integraciones en agent.py + 2 en db_utils.py")
    else:
        print("  VER ERRORES ARRIBA")
    print("=" * 55)
    return 0 if (r1 and r2) else 1

if __name__ == "__main__":
    exit(main())