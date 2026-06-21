#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
#  TPV UltraSmart — Arranque y prueba en Termux
#  Uso:  bash tpv_termux_run.sh
#  Luego abre en el navegador del móvil:  http://127.0.0.1:5050
# ============================================================================
set -e

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
say()  { echo -e "${CYAN}==>${NC} $1"; }
ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YEL}[!]${NC} $1"; }

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_DIR="$PROJ_DIR/app/src/main/python"

echo -e "\n${CYAN}===== TPV UltraSmart — Termux =====${NC}\n"

# 1) Comprobar Python
say "Comprobando Python..."
if ! command -v python >/dev/null 2>&1; then
  warn "Python no está instalado. Ejecuta:  pkg install python -y"
  exit 1
fi
ok "$(python --version 2>&1)"

# 2) Instalar dependencias (solo Flask y compañía)
say "Instalando dependencias (Flask)..."
python -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
if [ -f "$PROJ_DIR/requirements.txt" ]; then
  python -m pip install --quiet -r "$PROJ_DIR/requirements.txt" || \
    python -m pip install --quiet flask==2.2.5 werkzeug==2.2.3 jinja2==3.1.2 \
      markupsafe==2.1.3 itsdangerous==2.1.2 click==8.1.7 six==1.16.0
fi
ok "Dependencias listas"

# 3) Limpiar secretos generados en runs anteriores
rm -f "$PY_DIR/.tpv_secret" "$PY_DIR/.tpv_hmac_secret" 2>/dev/null || true

# 4) Smoke test rápido (verifica que arranca antes de servir)
say "Smoke test (arranque + rutas + agente + SQLi)..."
if python "$PROJ_DIR/scripts/smoke_test.py"; then
  ok "Smoke test superado"
else
  warn "El smoke test reportó fallos (ver arriba). Se intentará arrancar igualmente."
fi

# 5) Arrancar el servidor Flask
PORT="${TPV_PORT:-5050}"
echo ""
say "Arrancando servidor en ${GREEN}http://127.0.0.1:${PORT}${NC}"
say "Abre esa dirección en el navegador del móvil (Chrome/Firefox)."
say "Para detener: pulsa ${YEL}Ctrl+C${NC}"
echo ""
cd "$PY_DIR"
exec env TPV_PORT="$PORT" python app.py
