#!/data/data/com.termux/files/usr/bin/bash
# Preparación reproducible de TPV Ultra Smart en Termux.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_DIR="$ROOT/app/src/main/python"
DATA_DIR="${TPV_FILES_DIR:-$HOME/.local/share/tpv-ultra-smart}"

command -v python >/dev/null 2>&1 || {
  echo "Python no está instalado. Ejecuta: pkg install python" >&2
  exit 1
}

mkdir -p "$DATA_DIR"
export PYTHONPATH="$PYTHON_DIR${PYTHONPATH:+:$PYTHONPATH}"
export TPV_FILES_DIR="$DATA_DIR"
export TPV_FRONTEND_DIR="$ROOT/app/src/main/assets/frontend"

printf '\n==> Instalando dependencias\n'
python -m pip install --upgrade -r "$ROOT/requirements.txt" pytest pytest-cov

printf '\n==> Ejecutando suite y gate de cobertura\n'
cd "$ROOT"
python -m pytest \
  --cov=app/src/main/python \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-fail-under=50

rm -f .coverage coverage.xml
printf '\nTermux listo. Arranque: bash tools/tpv_termux_run.sh\n'
