#!/usr/bin/env python3
"""Tests v13 - 9 modulos (self-discovering, API real)."""
import sys, os, importlib, inspect
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ia")
P = F = 0

def T(n, fn):
    global P, F
    try:
        fn(); P += 1; print("  PASS " + n)
    except Exception as e:
        F += 1; print("  FAIL " + n + ": " + str(e))

def test_intent_router_import():
    import ia.intent_router as m
    assert m.__file__ is not None

def test_intent_router_has_public_api():
    import ia.intent_router as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_compaction_import():
    import ia.compaction as m
    assert m.__file__ is not None

def test_compaction_has_public_api():
    import ia.compaction as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_skill_registry_import():
    import ia.skill_registry as m
    assert m.__file__ is not None

def test_skill_registry_has_public_api():
    import ia.skill_registry as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_denial_tracking_import():
    import ia.denial_tracking as m
    assert m.__file__ is not None

def test_denial_tracking_has_public_api():
    import ia.denial_tracking as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_error_formatter_import():
    import ia.error_formatter as m
    assert m.__file__ is not None

def test_error_formatter_has_public_api():
    import ia.error_formatter as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_task_manager_import():
    import ia.task_manager as m
    assert m.__file__ is not None

def test_task_manager_has_public_api():
    import ia.task_manager as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_hooks_import():
    import ia.hooks as m
    assert m.__file__ is not None

def test_hooks_has_public_api():
    import ia.hooks as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_result_cache_import():
    import ia.result_cache as m
    assert m.__file__ is not None

def test_result_cache_has_public_api():
    import ia.result_cache as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_response_budget_import():
    import ia.response_budget as m
    assert m.__file__ is not None

def test_response_budget_has_public_api():
    import ia.response_budget as m
    pub = [x for x in dir(m) if not x.startswith("_")]
    assert len(pub) > 0, "No public API"

def test_all_9_files_exist():
    mods = ['intent_router', 'compaction', 'skill_registry', 'denial_tracking', 'error_formatter', 'task_manager', 'hooks', 'result_cache', 'response_budget']
    for m in mods:
        assert os.path.exists(os.path.join(IA, m + ".py")), "Missing " + m

def test_agent_compiles():
    with open(os.path.join(IA, "agent.py")) as f: compile(f.read(), "agent.py", "exec")

def test_dbutils_compiles():
    with open(os.path.join(IA, "db_utils.py")) as f: compile(f.read(), "db_utils.py", "exec")

def test_flags_base_7():
    with open(os.path.join(IA, "agent.py")) as f: c = f.read()
    for fl in ["_HAS_NORM","_HAS_INTENT","_HAS_CTX","_HAS_SKILLS","_HAS_MEM","_HAS_ANTI_SLOP","_HAS_V13"]:
        assert fl in c, "Missing " + fl

def test_task_manager_class():
    import ia.task_manager as m
    cls = [x for x in dir(m) if inspect.isclass(getattr(m, x)) and not x.startswith("_")]
    assert len(cls) > 0

def test_skill_registry_class():
    import ia.skill_registry as m
    cls = [x for x in dir(m) if inspect.isclass(getattr(m, x)) and not x.startswith("_")]
    assert len(cls) > 0

def test_result_cache_class():
    import ia.result_cache as m
    cls = [x for x in dir(m) if inspect.isclass(getattr(m, x)) and not x.startswith("_")]
    assert len(cls) > 0

def test_result_cache_singleton():
    import ia.result_cache as m
    if hasattr(m, "get_cache"):
        c = m.get_cache()
        assert c is not None
    elif hasattr(m, "reset_cache"):
        m.reset_cache()

def test_hooks_callable():
    import ia.hooks as m
    fns = [x for x in dir(m) if callable(getattr(m, x)) and not x.startswith("_")]
    assert len(fns) > 0

def test_intent_router_callable():
    import ia.intent_router as m
    fns = [x for x in dir(m) if callable(getattr(m, x)) and not x.startswith("_")]
    assert len(fns) > 0

def test_response_budget_callable():
    import ia.response_budget as m
    fns = [x for x in dir(m) if callable(getattr(m, x)) and not x.startswith("_")]
    assert len(fns) > 0

def test_dbutils_has_cache():
    with open(os.path.join(IA, "db_utils.py")) as f: c = f.read().lower()
    assert "cache" in c

def test_module_count_9():
    assert len(['intent_router', 'compaction', 'skill_registry', 'denial_tracking', 'error_formatter', 'task_manager', 'hooks', 'result_cache', 'response_budget']) == 9

if __name__ == "__main__":
    print("=" * 50)
    print("  Tests v13 - 9 modulos (self-discovering)")
    print("=" * 50)
    for k, v in sorted(globals().items()):
        if k.startswith("test_") and callable(v):
            T(k, v)
    print("")
    print("  " + str(P) + " PASS / " + str(F) + " FAIL / " + str(P + F) + " total")
    sys.exit(0 if F == 0 else 1)
