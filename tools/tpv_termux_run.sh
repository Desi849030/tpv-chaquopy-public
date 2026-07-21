#!/data/data/com.termux/files/usr/bin/bash
# TPV Ultra Smart — navegador local en Termux
set -Eeuo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
say()  { echo -e "${CYAN}==>${NC} $1"; }
ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YEL}[!]${NC} $1"; }
fail() { echo -e "  ${RED}[ERROR]${NC} $1"; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_DIR="$ROOT/app/src/main/python"
FRONTEND_DIR="$ROOT/app/src/main/assets/frontend"
DATA_DIR="${TPV_FILES_DIR:-$HOME/.local/share/tpv-ultra-smart}"
HOST="${TPV_HOST:-127.0.0.1}"
PORT="${TPV_PORT:-5000}"

command -v python >/dev/null 2>&1 || fail "Instala Python: pkg install python"
[ -f "$PY_DIR/app.py" ] || fail "No se encontró $PY_DIR/app.py"
[ -d "$FRONTEND_DIR" ] || fail "No se encontró el frontend: $FRONTEND_DIR"
mkdir -p "$DATA_DIR"

echo -e "\n${CYAN}===== TPV Ultra Smart — Termux =====${NC}\n"
ok "$(python --version 2>&1)"

say "Instalando dependencias declaradas..."
python -m pip install --quiet --upgrade -r "$ROOT/requirements.txt"
ok "Dependencias listas"

export PYTHONPATH="$PY_DIR${PYTHONPATH:+:$PYTHONPATH}"
export TPV_FILES_DIR="$DATA_DIR"
export TPV_FRONTEND_DIR="$FRONTEND_DIR"
export TPV_HOST="$HOST"
export TPV_PORT="$PORT"

say "Smoke test..."
if python "$ROOT/scripts/smoke_test.py"; then
  ok "Smoke test superado"
else
  warn "El smoke test reportó fallos; revisa la salida antes de usar datos reales."
fi

echo
say "Servidor: ${GREEN}http://${HOST}:${PORT}${NC}"
say "Datos locales: $DATA_DIR"
say "Detener: Ctrl+C"
echo
cd "$ROOT"
exec python "$PY_DIR/app.py"
