#!/bin/bash
set -e
cd "$(dirname "$0")/.."
python3 -m py_compile app/src/main/python/app.py
python3 -m py_compile app/src/main/python/db_connection.py
python3 -m pytest tests/test_basic.py tests/mocks/test_routes.py -q --tb=short 2>/dev/null || exit 1
echo OK
