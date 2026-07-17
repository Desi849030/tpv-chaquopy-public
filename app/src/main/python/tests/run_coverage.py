#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecuta tests con cobertura y genera reporte.
Uso:  cd app/src/main/python && python tests/run_coverage.py
"""
import os, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

def main():
    print("=" * 60)
    print("  TPV Ultra Smart — Tests + Cobertura")
    print("=" * 60)

    # Intentar instalar coverage si no existe
    try:
        import coverage
    except ImportError:
        print("Instalando coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage", "-q"],
                       capture_output=True)

    # Ejecutar pytest con cobertura
    test_files = [
        "tests/test_agent_roles_v12.py",
        "tests/test_coverage_boost.py",
        "tests/test_e2e_pipeline.py",
        "tests/test_smart_coverage.py",,
    ]
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v", "--tb=short",
        f"--cov=ia",
        f"--cov-report=term-missing",
        f"--cov-report=html:{os.path.join(BASE, 'htmlcov')}",
    ]

    print(f"\nEjecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PARENT, capture_output=False)

    # Resumen
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("  TODOS LOS TESTS PASARON")
    else:
        print(f"  HUBO ERRORES (exit code: {result.returncode})")
    print("=" * 60)

    # Intentar obtener porcentaje de cobertura
    try:
        import coverage
        cov = coverage.Coverage()
        # No podemos leer el .coverage de pytest, pero el reporte HTML ya se generó
        html_dir = os.path.join(BASE, 'htmlcov', 'index.html')
        if os.path.exists(html_dir):
            print(f"\nReporte HTML: {html_dir}")
    except Exception:
        pass

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
