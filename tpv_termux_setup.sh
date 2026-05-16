#!/bin/bash
set -e
FAILS=0
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; FAILS=$((FAILS+1)); }
step() { echo -e "\n${CYAN}--- $1 ---${NC}"; }

echo -e "\n${CYAN}=== TPV ULTRA SMART v2.5.5 — Tests ===${NC}\n"

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_DIR="$PROJ_DIR/app/src/main/python"

step "1 — Limpiando secrets temporales"
rm -f "$PYTHON_DIR/.tpv_secret" "$PYTHON_DIR/.tpv_hmac_secret" 2>/dev/null
export PYTHONPATH="$PYTHON_DIR"
ok "PYTHONPATH=$PYTHONPATH"

step "2 — Tests unitarios (142)"
cd "$PROJ_DIR"
python -m pytest tests/ -v --tb=short 2>&1 | tail -25

step "3 — Simulacion APK (38 tests)"
if [ -f "$PROJ_DIR/test_simulacion_apk_full.py" ]; then
    python "$PROJ_DIR/test_simulacion_apk_full.py" 2>&1 | tail -10
fi

echo ""
echo -e "${CYAN}=== Hecho ===${NC}"
