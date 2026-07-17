#!/usr/bin/env python3
"""
patch_v13d_integrate.py — Paso 1G: Post-agentic hooks (el paso que faltaba)
=============================================================
Estrategia segura: reemplaza SOLO la primera línea del return,
insertando el bloque v13 antes. No toca el resto del dict.
"""

import re, shutil, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.join(BASE, 'ia', 'agent.py')

def main():
    print("=" * 60)
    print("  PATCH v13d — 1G: Post-agentic hooks")
    print("=" * 60)

    # ── Backup ──
    ts = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = f"{AGENT}.bak_v13d_{ts}"
    shutil.copy2(AGENT, bak)
    print(f"  [BACKUP] {os.path.basename(AGENT)} -> {os.path.basename(bak)}")

    with open(AGENT, 'r', encoding='utf-8') as f:
        code = f.read()

    original_code = code
    changes = 0

    # ═══════════════════════════════════════════════════════
    # 1G-a — Post-agentic path
    # ═══════════════════════════════════════════════════════
    # Reemplazamos SOLO la línea del return del agentic path
    # Antes:  return { 'answer': agentic['response'],
    # Después: bloque v13 + return { 'answer': _resp,

    old_agentic_return = "                return { 'answer': agentic['response'],"

    if old_agentic_return in code:
        new_agentic_return = (
            "                # === V13 POST-AGENTIC ===\n"
            "                _resp = agentic['response']\n"
            "                if _HAS_BUDGET:\n"
            "                    try:\n"
            "                        from response_budget import trim_response\n"
            "                        _resp = trim_response(_resp, max_tokens=200)\n"
            "                    except: pass\n"
            "                if _HAS_CACHE:\n"
            "                    try:\n"
            "                        from result_cache import cache_result\n"
            "                        cache_result(sid, question, _resp, role)\n"
            "                    except: pass\n"
            "                if _HAS_DENIAL:\n"
            "                    try:\n"
            "                        from denial_tracking import check_denial\n"
            "                        check_denial(_resp)\n"
            "                    except: pass\n"
            "                if _HAS_HOOKS:\n"
            "                    try:\n"
            "                        from hooks import run_post_hooks\n"
            "                        _resp = run_post_hooks('agentic_response', _resp, role=role)\n"
            "                    except: pass\n"
            "                return { 'answer': _resp,"
        )
        code = code.replace(old_agentic_return, new_agentic_return, 1)
        changes += 1
        print("  [1G-a] Post-agentic hooks OK")
    else:
        # Puede que ya tenga _resp (ya aplicado)
        if "                _resp = agentic['response']" in code:
            print("  [1G-a] SKIP — ya aplicado (encuentra _resp)")
        else:
            print("  [1G-a] SKIP — anchor no encontrada")

    # ═══════════════════════════════════════════════════════
    # 1G-b — Post-fallback path
    # ═══════════════════════════════════════════════════════
    old_fb_return = "                return { 'answer': r['answer'],"

    if old_fb_return in code:
        new_fb_return = (
            "                # === V13 POST-FALLBACK ===\n"
            "                _fb_resp = r['answer']\n"
            "                if _HAS_BUDGET:\n"
            "                    try:\n"
            "                        from response_budget import trim_response\n"
            "                        _fb_resp = trim_response(_fb_resp, max_tokens=200)\n"
            "                    except: pass\n"
            "                if _HAS_CACHE:\n"
            "                    try:\n"
            "                        from result_cache import cache_result\n"
            "                        cache_result(sid, question, _fb_resp, role)\n"
            "                    except: pass\n"
            "                if _HAS_HOOKS:\n"
            "                    try:\n"
            "                        from hooks import run_post_hooks\n"
            "                        _fb_resp = run_post_hooks('fallback_response', _fb_resp, role=role)\n"
            "                    except: pass\n"
            "                return { 'answer': _fb_resp,"
        )
        code = code.replace(old_fb_return, new_fb_return, 1)
        changes += 1
        print("  [1G-b] Post-fallback hooks OK")
    else:
        if "                _fb_resp = r['answer']" in code:
            print("  [1G-b] SKIP — ya aplicado (encuentra _fb_resp)")
        else:
            print("  [1G-b] SKIP — anchor no encontrada")

    # ═══════════════════════════════════════════════════════
    # Imports faltantes
    # ═══════════════════════════════════════════════════════
    for flag, mod in [('_HAS_BUDGET','response_budget'), ('_HAS_CACHE','result_cache'),
                      ('_HAS_DENIAL','denial_tracking'), ('_HAS_HOOKS','hooks')]:
        if flag not in code:
            # Insertar import después del último "except: _OK=False"
            last_exc = code.rfind("except: _OK=False")
            if last_exc != -1:
                nl = code.index('\n', last_exc) + 1
                code = code[:nl] + f"try:\n    from {mod} import *; _OK=True\nexcept: _OK=False\n" + code[nl:]
            # Insertar flag después del último _HAS_
            flags = re.findall(r'^(_HAS_\w+)\s*=', code, re.MULTILINE)
            if flags:
                m = re.search(rf'^{re.escape(flags[-1])}\s*=\s*.*$', code, re.MULTILINE)
                if m:
                    p = m.end()
                    code = code[:p] + f"\n{flag} = _OK  # v13d" + code[p:]
            changes += 1
            print(f"  [IMPORT] {flag} ({mod}) OK")
        else:
            print(f"  [IMPORT] {flag} ya existe")

    # ── Escribir + verificar sintaxis ──
    if code != original_code or changes > 0:
        with open(AGENT, 'w', encoding='utf-8') as f:
            f.write(code)
        try:
            compile(code, AGENT, 'exec')
            print(f"\n  agent.py: {changes} cambio(s), sintaxis OK")
        except SyntaxError as e:
            print(f"\n  *** SYNTAX ERROR línea {e.lineno}: {e.msg} ***")
            shutil.copy2(bak, AGENT)
            print(f"  Restaurado desde {os.path.basename(bak)}")
            sys.exit(1)
    else:
        print("\n  Sin cambios necesarios")

    print("=" * 60)
    print(f"  OK — {changes} cambio(s) en agent.py")
    print("=" * 60)

if __name__ == '__main__':
    main()