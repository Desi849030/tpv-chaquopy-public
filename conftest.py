"""Global pytest isolation and collection policy for the supported suite."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

_TEST_DATA_DIR = tempfile.mkdtemp(prefix="tpv-tests-")
os.environ["TPV_TESTING"] = "1"
os.environ["TPV_FILES_DIR"] = _TEST_DATA_DIR
os.environ["TPV_DB_PATH"] = str(Path(_TEST_DATA_DIR) / "tpv_datos.db")
os.environ.setdefault("TPV_SECRET_KEY", "coverage-test-secret")
os.environ.setdefault("TPV_DEMO_PASSWORD", "dev2024")

# Legacy generated tests either mutate sys.modules globally or target removed
# modules. They remain in the repository as historical artifacts, not CI tests.
collect_ignore = [
    "app/src/main/python/tests/test_pure_modules_v3.py",
    "tests/ia/test_handlers_staff.py",
]


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)
