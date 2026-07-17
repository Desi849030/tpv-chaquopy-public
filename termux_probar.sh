#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

C='\033[0;36m'; G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[1;34m'; N='\033[0m'
say()  { echo -e "${C}[TPV]${N} $1"; }
ok()   { echo -e "  ${G}[OK]${N} $1"; }
err()  { echo -e "  ${R}[ERROR]${N} $1"; }
warn() { echo -e "  ${Y}[!]${N} $1"; }

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_DIR="$PROJ_DIR/app/src/main/python"

echo ""
echo -e "${B}========================================${N}"
echo -e "${B}   TPV UltraSmart — Test Termux${N}"
echo -e "${B}========================================${N}"
echo ""

say "Verificando entorno..."
if ! command -v python &>/dev/null; then
  err "Python no encontrado. Ejecuta: pkg install python -y"
  exit 1
fi
ok "Python: $(python --version 2>&1)"

# Solo instalar si flask NO existe
if ! python -c "import flask" 2>/dev/null; then
  say "Instalando Flask..."
  python -m pip install --quiet flask 2>/dev/null || { err "No se pudo instalar Flask"; exit 1; }
  ok "Flask instalado"
else
  ok "Flask ya instalado ($(python -c 'import flask; print(flask.__version__)' 2>/dev/null))"
fi

# Verificar compatibilidad werkzeug
python -c "
import werkzeug
from packaging.version import Version
if Version(werkzeug.__version__) < Version('3.1'):
    print('ADVERTENCIA: werkzeug', werkzeug.__version__, 'es viejo para Python 3.14')
    import sys; sys.exit(1)
" 2>/dev/null || {
  say "Actualizando werkzeug para Python 3.14..."
  python -m pip install --quiet --upgrade werkzeug 2>/dev/null
}

rm -f "$PY_DIR/.tpv_secret_key" "$PY_DIR/tpv_datos.db-wal" "$PY_DIR/tpv_datos.db-shm" 2>/dev/null || true
ok "Secretos limpiados"

CUSTOM_PASS="${1:-}"
if [ -n "$CUSTOM_PASS" ]; then
  export TPV_DEMO_PASSWORD="$CUSTOM_PASS"
  PASS_MSG="$CUSTOM_PASS"
else
  PASS_MSG="dev2024 (por defecto)"
fi

echo ""
echo -e "${G}══════════════════════════════════════════════${N}"
echo -e "${G}  Usuario:      ${B}desarrollador${N}"
echo -e "${G}  Contraseña:   ${B}${PASS_MSG}${N}"
echo -e "${G}  URL:          ${B}http://127.0.0.1:5000${N}"
echo -e "${G}══════════════════════════════════════════════${N}"
echo ""
warn "Abre esa URL en Chrome del móvil"
warn "Para detener: Ctrl+C"
echo ""

cd "$PY_DIR"
exec python -u app.py
