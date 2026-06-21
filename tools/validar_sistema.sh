#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/tpv-trabajo"
LOG="$HOME/tpv_server.log"

echo "🚀 Validación tesis TPV (suite oficial)"

cd "$ROOT" || exit 1

pkill -9 -f "python app.py" 2>/dev/null || true
pkill -9 -f "app/src/main/python/app.py" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true

echo "📡 Arrancando servidor..."
nohup env PYTHONPATH=app/src/main/python python app/src/main/python/app.py > "$LOG" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$HOME/tpv_server.pid"

echo "⏳ Esperando arranque..."
sleep 8

echo "🔎 Health check..."
curl -s http://127.0.0.1:5000/api/health || {
  echo "❌ El servidor no respondió"
  tail -n 60 "$LOG"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
}
echo

echo "🧪 Ejecutando suite oficial..."
python -m unittest discover -s tests/oficial -p "test_*.py" -v
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "❌ Fallaron tests oficiales"
  tail -n 60 "$LOG"
else
  echo "✅ Tests oficiales OK"
fi

echo "🧹 Cerrando servidor..."
kill $SERVER_PID 2>/dev/null || true
rm -f "$HOME/tpv_server.pid"
fuser -k 5000/tcp 2>/dev/null || true

exit $RESULT
