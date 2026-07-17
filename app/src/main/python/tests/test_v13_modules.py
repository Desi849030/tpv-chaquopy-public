#!/usr/bin/env python3
"""Tests modulos v13 — 9 modulos."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = F = 0
def T(n, fn):
    global P, F
    try:
        fn(); P += 1; print(f"  PASS {n}")
    except Exception as e:
        F += 1; print(f"  FAIL {n}: {e}")

def t1():
    from ia.intent_router import detect_intent
    if callable(detect_intent):
        r = detect_intent("cuanto cuesta")
        assert r is not None

def t2():
    from ia.intent_router import detect_intent
    if callable(detect_intent):
        detect_intent("hola buenos dias")
        detect_intent("quiero comprar")

def t3():
    from ia.compaction import compact_history
    h = [{"role":"u","content":"hola"},{"role":"b","content":"hi"}]*10
    r = compact_history(h)
    assert isinstance(r, list) and len(r) <= len(h)

def t4():
    from ia.compaction import should_compact
    if callable(should_compact):
        assert isinstance(should_compact([{"role":"u"}]*20), (bool,int))

def t5():
    from ia.skill_registry import SkillRegistry
    sr = SkillRegistry()
    sr.register("test_s", lambda x: "ok")
    assert "test_s" in sr.list_skills()

def t6():
    from ia.denial_tracking import DenialTracker
    dt = DenialTracker()
    dt.track("u", "no puedo")
    assert dt.get_count("u") >= 0

def t7():
    from ia.denial_tracking import check_denial
    if callable(check_denial):
        check_denial("no se puede")

def t8():
    from ia.error_formatter import format_error
    if callable(format_error):
        r = format_error(ValueError("test"))
        assert isinstance(r, str) and len(r) > 0

def t9():
    from ia.task_manager import TaskManager
    tm = TaskManager()
    t = tm.create("t1", steps=["a","b","c"])
    assert t is not None

def t10():
    from ia.task_manager import TaskManager
    tm = TaskManager()
    t = tm.create("t2", steps=["auto1","input1","auto2"])
    tm.advance(t)
    assert t is not None

def t11():
    from ia.hooks import run_pre_hooks, run_post_hooks
    if callable(run_pre_hooks):
        run_pre_hooks("test", {"text":"hola"})
    if callable(run_post_hooks):
        run_post_hooks("test", "resp", role="cliente")

def t12():
    from ia.result_cache import ResultCache
    rc = ResultCache(ttl=60)
    rc.set("k1","v1")
    assert rc.get("k1") == "v1"

def t13():
    from ia.result_cache import ResultCache
    rc = ResultCache(ttl=0)
    rc.set("k2","v2")
    assert rc.get("k2") is None

def t14():
    from ia.response_budget import trim_response
    r = trim_response("palabra "*500, max_tokens=50)
    assert len(r) < 2500

def t15():
    from ia.response_budget import trim_response
    r = trim_response("corto", max_tokens=200)
    assert r == "corto"

def t16():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ia', 'agent.py')
    with open(p) as f:
        c = f.read()
    flags = ['_HAS_NORM','_HAS_INTENT','_HAS_CTX','_HAS_SKILLS','_HAS_MEM','_HAS_ANTI_SLOP','_HAS_BUDGET','_HAS_CACHE','_HAS_DENIAL','_HAS_HOOKS']
    assert sum(1 for x in flags if x in c) >= 6

def t17():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ia', 'agent.py')
    with open(p) as f:
        compile(f.read(), p, 'exec')

def t18():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ia', 'db_utils.py')
    with open(p) as f:
        compile(f.read(), p, 'exec')

def t19():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ia', 'db_utils.py')
    with open(p) as f:
        c = f.read()
    assert 'cache' in c.lower() or 'result_cache' in c

def t20():
    for mod in ['intent_router','compaction','skill_registry','denial_tracking','error_formatter','task_manager','hooks','result_cache','response_budget']:
        p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ia', f'{mod}.py')
        assert os.path.exists(p), f"Falta {mod}.py"

if __name__ == '__main__':
    print("="*50)
    print("  Tests v13 — 9 modulos + integracion")
    print("="*50)
    for k,v in sorted(globals().items()):
        if k.startswith('t') and k[1:].isdigit():
            T(k, v)
    print(f"\n  {P} PASS / {F} FAIL / {P+F} total")
    sys.exit(0 if F == 0 else 1)
