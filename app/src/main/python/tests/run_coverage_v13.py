#!/usr/bin/env python3
"""Cobertura simple — cuenta líneas ejecutadas vs totales."""
import os, sys, trace, io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

modules = [
    'ia.intent_router',
    'ia.compaction',
    'ia.skill_registry',
    'ia.denial_tracking',
    'ia.error_formatter',
    'ia.task_manager',
    'ia.hooks',
    'ia.result_cache',
    'ia.response_budget',
]

total_lines = 0
covered_lines = 0

for mod in modules:
    try:
        __import__(mod)
    except ImportError:
        print(f"  SKIP {mod}")
        continue

    # Ejecutar import y llamadas básicas para activar líneas
    tracer = trace.Trace(count=True, trace=False)
    try:
        tracer.runfunc(__import__, mod)
    except:
        pass

    results = tracer.results()
    if results:
        for f in results.files:
            if mod.replace('.', '/') in f or any(m in f for m in modules):
                lines = results.files[f]
                for line_no in lines:
                    total_lines += 1
                    if lines[line_no] > 0:
                        covered_lines += 1

print(f"\n  Líneas cubiertas: {covered_lines}")
print(f"  Total líneas: {total_lines}")
if total_lines > 0:
    pct = (covered_lines / total_lines) * 100
    print(f"  Cobertura: {pct:.1f}%")
else:
    print("  (Usando conteo de tests en su lugar)")

# Contar tests como proxy de cobertura
test_count = 0
test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
if os.path.isdir(test_dir):
    for f in os.listdir(test_dir):
        if f.startswith('test_') and f.endswith('.py'):
            with open(os.path.join(test_dir, f)) as tf:
                test_count += tf.read().count('def test_')

print(f"  Total test functions: {test_count}")
print(f"  Módulos v13: {len(modules)}")
