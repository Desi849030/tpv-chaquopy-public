"""Import smoke test for production modules.

Import failures previously hid complete blueprints from the running application.
This test protects the public module graph (including the decorators regression).
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "app" / "src" / "main" / "python"


def _production_modules():
    modules = []
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC)
        if "tests" in rel.parts or path.name.startswith("patch_"):
            continue
        if path.name in {"server.py", "start_server.py", "migrar_tablas_tienda.py"}:
            continue
        # This package references files which are not present in the public tree.
        if rel.parts[0] == "agent":
            continue
        parts = rel.with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            modules.append(".".join(parts))
    return sorted(set(modules))


@pytest.mark.parametrize("module_name", _production_modules())
def test_production_module_imports(module_name):
    module = importlib.import_module(module_name)
    assert module is not None
