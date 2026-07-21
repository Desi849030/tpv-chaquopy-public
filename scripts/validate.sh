#!/usr/bin/env bash
# Local equivalent of the Python quality job in GitHub Actions.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m py_compile \
  app/src/main/python/app.py \
  app/src/main/python/database.py \
  app/src/main/python/documentation_loader.py

python -m pytest \
  --cov=app/src/main/python \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-fail-under=50

echo "Validation successful"
