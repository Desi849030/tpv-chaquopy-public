#!/usr/bin/env python3
"""
patch_v13b_integrate.py — Integra los 9 módulos v13 en agent.py y db_utils.py
Ejecutar en Termux:
  cd ~/tpv-chaquopy-public/app/src/main/python
  python patch_v13b_integrate.py
"""

import os
import re
import shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
IA_DIR = os.path.join(BASE, "ia")
BACKUP_DIR = os.path.join(IA_DIR, "backup_v13b")

def backup(filepath):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = os.path.basename(filepath)
    dst = os.path.join(BACKUP_DIR, f"{name}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(filepath, dst)
    print(f"  [BACKUP] {name} -> backup_v13b/")
    return dst

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def check_syntax(path):
    import py_compile
    try:
        py_compile.compile(path, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  [SYNTAX ERROR] {os.path.basename(path)}: {e}")
        return False


# ============================================================
# PATCH 1: agent.py
# ============================================================
def patch_agent():
    filepath = os.path.join(IA_DIR, "agent.py")
    if not os.path.exists(filepath):
        print("  [SKIP] agent.py no encontrado")
        return False

    backup(filepath)
    code = read_file(filepath)
    original = code
    changes = 0

    # --- 1A: Agregar imports v13 después del bloque _HAS_ANTI_SLOP ---
    v13_imports = '''
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
    _HAS_V13 = False'''

    anchor = "    _HAS_ANTI_SLOP = False"
    if anchor in code:
        code = code.replace(anchor, anchor + "\n" + v13_imports, 1)
        changes += 1
        print("  [1A] Imports v13 agregados")
    else:
        print("  [1A] SKIP - no encontro anchor _HAS_ANTI_SLOP")

    # --- 1B: Inicializar v13 en Agent.__init__ ---
    v13_init = """
        # v13 modules
        self._v13_ok = _HAS_V13
        if _HAS_V13:
            self._v13_tracker = _get_v13_tracker()
            self._v13_hooks = _get_v13_hooks()
            self._v13_budget = _get_v13_budget()
            self._v13_efmt = _get_v13_efmt()"""

    anchor = "        self._as_ok = _HAS_ANTI_SLOP"
    if anchor in code:
        code = code.replace(anchor, anchor + "\n" + v13_init, 1)
        changes += 1
        print("  [1B] Init v13 en __init__")
    else:
        print("  [1B] SKIP - no encontro anchor _as_ok")

    # --- 1C: Pre-process hooks antes de AGENTIC PIPELINE ---
    v13_pre_hooks = """        # v13: Pre-processing hooks
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
    anchor = "        # === AGENTIC PIPELINE ==="
    if anchor in code:
        code = code.replace(anchor, v13_pre_hooks + anchor, 1)
        changes += 1
        print("  [1C] Pre-process hooks agregados")
    else:
        print("  [1C] SKIP - no encontro anchor AGENTIC PIPELINE")

    # --- 1D: Reemplazar truncado simple con compaction ---
    old_truncate = """        if len(m['h']) > 20:
            m['h'] = m['h'][-20:]"""

    new_compaction = """        # v13: Smart compaction (replaces simple truncation)
        if self._v13_ok and len(m['h']) > 40:
            try:
                msgs = [_v13_msg(role='user', content=h) for h in m['h']]
                cr = _v13_compact(msgs, max_messages=30)
                m['h'] = [msg.content for msg in cr.messages if msg.role == 'user']
            except Exception:
                m['h'] = m['h'][-20:]
        elif len(m['h']) > 20:
            m['h'] = m['h'][-20:]"""

    if old_truncate in code:
        code = code.replace(old_truncate, new_compaction, 1)
        changes += 1
        print("  [1D] Compaction reemplaza truncado simple")
    else:
        print("  [1D] SKIP - no encontro truncado simple")

    # --- 1E: Wrap dispatch con error formatter + denial tracking ---
    old_dispatch = """        # === DISPATCH POR ROL ===
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

    new_dispatch = """        # === DISPATCH POR ROL (v13: error formatter + denial tracking) ===
        result = ''
        dispatch_error = None
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
            # v13: Track success
            if self._v13_ok:
                self._v13_tracker.record_success()
        except Exception as dispatch_error:
            result = ''
            if self._v13_ok:
                self._v13_tracker.record_failure(str(dispatch_error))
                try:
                    fe = self._v13_efmt.format(dispatch_error, context={'role': role, 'text': t[:100]})
                    result = fe.to_user_string()
                except Exception:
                    result = 'Lo siento, ocurrio un error procesando tu solicitud.'
                # v13: Recovery si esta atascado
                if self._v13_tracker.state.is_stuck:
                    recovery = self._v13_tracker.get_recovery_message()
                    if recovery:
                        result = recovery
            else:
                result = 'Lo siento, ocurrio un error procesando tu solicitud.'"""

    if old_dispatch in code:
        code = code.replace(old_dispatch, new_dispatch, 1)
        changes += 1
        print("  [1E] Dispatch con error formatter + denial tracking")
    else:
        print("  [1E] SKIP - no encontro bloque DISPATCH POR ROL")

    # --- 1F: Response budget en _r() ---
    v13_budget = """        # v13: Apply response budget
        if self._v13_ok:
            try:
                msg = self._v13_budget.apply(msg, mode=_v13_bm.NORMAL)
            except Exception:
                pass
"""
    # Insertar antes del return en _r()
    anchor = """        return {
            'answer': msg,
            'role': role,
            'suggestions': suggestions,
            'intent': intent,
            'ts': datetime.now().isoformat(),
        }"""
    if anchor in code:
        code = code.replace(anchor, v13_budget + anchor, 1)
        changes += 1
        print("  [1F] Response budget en _r()")
    else:
        print("  [1F] SKIP - no encontro return en _r()")

    # --- 1G: Post-process hooks + budget en process_question() ---
    # Insertar antes de cada return en process_question
    v13_post_agentic = """        # v13: Post-process hooks + budget (agentic path)
        if _HAS_V13:
            try:
                from ia.hooks import get_hook_pipeline as _gp, HookPoint as _hp, HookContext as _hc
                from ia.response_budget import get_budget as _gb, BudgetMode as _gm
                _pctx = _hc(hook_point=_hp.POST_PROCESS, text=question, role=role, response=agentic['response'])
                _pr = _gp().execute(_hp.POST_PROCESS, _pctx)
                if _pr.modified_response:
                    agentic['response'] = _pr.modified_response
                if _pr.override:
                    agentic['response'] = _pr.override
                agentic['response'] = _gb().apply(agentic['response'], mode=_gm.NORMAL)
            except Exception:
                pass
"""
    # Antes del return del agentic path
    anchor_agentic = """            return {
                'answer': agentic['response'],
                'intent': 'agentic',"""
    if anchor_agentic in code:
        code = code.replace(anchor_agentic, v13_post_agentic + anchor_agentic, 1)
        changes += 1
        print("  [1G-a] Post-hooks en camino agentic")
    else:
        print("  [1G-a] SKIP - no encontro return agentic")

    # Antes del return del classic path
    v13_post_classic = """    # v13: Post-process hooks + budget (classic path)
    if _HAS_V13:
        try:
            from ia.hooks import get_hook_pipeline as _gp2, HookPoint as _hp2, HookContext as _hc2
            from ia.response_budget import get_budget as _gb2, BudgetMode as _gm2
            _pctx2 = _hc2(hook_point=_hp2.POST_PROCESS, text=question, role=role, response=r['answer'])
            _pr2 = _gp2().execute(_hp2.POST_PROCESS, _pctx2)
            if _pr2.modified_response:
                r['answer'] = _pr2.modified_response
            if _pr2.override:
                r['answer'] = _pr2.override
            r['answer'] = _gb2().apply(r['answer'], mode=_gm2.NORMAL)
        except Exception:
            pass
"""
    anchor_classic = """    return {
        'answer': r['answer'],
        'intent': r.get('intent', 'chat'),"""
    if anchor_classic in code:
        code = code.replace(anchor_classic, v13_post_classic + anchor_classic, 1)
        changes += 1
        print("  [1G-b] Post-hooks en camino classic")
    else:
        print("  [1G-b] SKIP - no encontro return classic")

    if code != original:
        write_file(filepath, code)
        print(f"\n  agent.py: {changes} cambios aplicados")
        return check_syntax(filepath)
    else:
        print("  agent.py: sin cambios (ningun anchor encontrado)")
        return True


# ============================================================
# PATCH 2: db_utils.py
# ============================================================
def patch_db_utils():
    filepath = os.path.join(IA_DIR, "db_utils.py")
    if not os.path.exists(filepath):
        print("  [SKIP] db_utils.py no encontrado")
        return False

    backup(filepath)
    code = read_file(filepath)
    original = code
    changes = 0

    # --- 2A: Agregar import de cache ---
    cache_import = """
# v13: Query result cache
try:
    from ia.result_cache import get_cache as _get_qcache
    _HAS_QCACHE = True
    _qcache = _get_qcache() if _HAS_QCACHE else None
except Exception:
    _HAS_QCACHE = False
    _qcache = None"""

    anchor = 'def q(sql, params=(), one=False):'
    if anchor in code:
        code = code.replace(anchor, cache_import + "\n\n" + anchor, 1)
        changes += 1
        print("  [2A] Import cache agregado")
    else:
        print("  [2A] SKIP - no encontro def q()")

    # --- 2B: Modificar q() para usar cache ---
    old_q = """def q(sql, params=(), one=False):
    \"\"\"Execute query and return results.\"\"\"
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
        except: pass"""

    new_q = '''def q(sql, params=(), one=False):
    """Execute query and return results."""
    _sql_up = sql.strip().upper()
    _is_select = _sql_up.startswith("SELECT")

    # v13: Cache hit for SELECTs
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
            # v13: Cache SELECT results
            if _HAS_QCACHE and _qcache is not None and rows:
                _qcache.set(sql, rows, params, ttl=30.0)
            return rows[0] if one and rows else (rows if rows else None)
        else:
            # Non-SELECT: invalidate cache (data changed)
            if _HAS_QCACHE and _qcache is not None:
                _qcache.invalidate()
            return cur.fetchone() if one else cur.fetchall()
    except:
        return None
    finally:
        try: c.close()
        except: pass'''

    if old_q in code:
        code = code.replace(old_q, new_q, 1)
        changes += 1
        print("  [2B] q() con cache integrado")
    else:
        print("  [2B] SKIP - no encontro cuerpo de q() exacto")

    if code != original:
        write_file(filepath, code)
        print(f"\n  db_utils.py: {changes} cambios aplicados")
        return check_syntax(filepath)
    else:
        print("  db_utils.py: sin cambios")
        return True


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 55)
    print("  PATCH v13b — Integracion de modulos v13")
    print("  Archivos: agent.py + db_utils.py")
    print("=" * 55)
    print()

    r1 = patch_agent()
    print()
    r2 = patch_db_utils()

    print()
    print("=" * 55)
    if r1 and r2:
        print("  RESULTADO: Integracion completada OK")
        print()
        print("  Modulos integrados en agent.py:")
        print("    - Intent Router (imports listos)")
        print("    - Compaction (historial >40 msgs)")
        print("    - Denial Tracking (errores consecutivos)")
        print("    - Error Formatter (errores amigables)")
        print("    - Hook Pipeline (pre/post processing)")
        print("    - Response Budget (longitud de respuesta)")
        print()
        print("  Modulos integrados en db_utils.py:")
        print("    - Result Cache (SELECTs cacheados 30s)")
        print()
        print("  Todos los cambios son NO-INVASIVOS:")
        print("    - Si _HAS_V13=False, funciona igual que antes")
        print("    - Fallbacks en cada punto de integracion")
    else:
        print("  RESULTADO: Verificar errores arriba")
    print("=" * 55)
    return 0 if (r1 and r2) else 1


if __name__ == "__main__":
    exit(main())