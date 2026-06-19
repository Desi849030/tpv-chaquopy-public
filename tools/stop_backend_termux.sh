#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="$HOME/tpv-trabajo"
PIDFILE="$ROOT/.backend_tpv.pid"

if [ -f "$PIDFILE" ]; then
    PID="$(cat "$PIDFILE")"
    echo "Deteniendo backend TPV PID=$PID"
    kill "$PID" 2>/dev/null || true
    rm -f "$PIDFILE"
else
    echo "No existe PID guardado. Buscando procesos python app.py..."
    pkill -f "app.py" 2>/dev/null || true
fi

echo "Backend detenido."
