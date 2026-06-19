#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="$HOME/tpv-trabajo"
APPDIR="$ROOT/app/src/main/python"
PORT="${TPV_PORT:-5050}"
LOG="$ROOT/docs/evidencias/backend_termux_${PORT}.log"

mkdir -p "$ROOT/docs/evidencias"

cd "$APPDIR"

export PYTHONPATH="$APPDIR:$PYTHONPATH"
export TPV_PORT="$PORT"

echo "=================================================="
echo " Iniciando backend TPV desde Termux"
echo " APPDIR: $APPDIR"
echo " PORT  : $PORT"
echo " LOG   : $LOG"
echo "=================================================="

nohup python app.py > "$LOG" 2>&1 &

PID=$!
echo "$PID" > "$ROOT/.backend_tpv.pid"

echo "PID: $PID"
sleep 5

echo
echo "Últimas líneas del log:"
echo "--------------------------------------------------"
tail -80 "$LOG" || true
echo "--------------------------------------------------"
echo
echo "Si no ves errores, prueba:"
echo "python tools/probar_backend_tpv.py"
