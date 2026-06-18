#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/tpv-trabajo"
LOG="$HOME/tpv_server.log"

echo "🚀 Validación de cobertura - suite oficial"

cd "$ROOT" || exit 1

pkill -9 -f "python app.py" 2>/dev/null || true
pkill -9 -f "app/src/main/python/app.py" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
sleep 2

echo "📡 Arrancando servidor..."
nohup env PYTHONPATH=app/src/main/python python app/src/main/python/app.py > "$LOG" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$HOME/tpv_server.pid"

echo "⏳ Esperando arranque..."
sleep 8

echo "🔎 Health check..."
curl -s http://127.0.0.1:5000/api/health || {
  echo
  echo "❌ El servidor no respondió"
  tail -n 60 "$LOG"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
}
echo

echo "🧪 Ejecutando cobertura..."
coverage erase
coverage run -m unittest discover -s tests/oficial -p "test_*.py"
RESULT=$?

echo "📊 Reporte de cobertura:"
coverage report -m
COV_RESULT=$?

echo "🧹 Cerrando servidor..."
kill $SERVER_PID 2>/dev/null || true
rm -f "$HOME/tpv_server.pid"
fuser -k 5000/tcp 2>/dev/null || true

if [ $RESULT -ne 0 ]; then
  echo "❌ Fallaron las pruebas"
  exit $RESULT
fi

if [ $COV_RESULT -ne 0 ]; then
  echo "❌ Falló el reporte de cobertura"
  exit $COV_RESULT
fi

echo "✅ Validación y cobertura completadas"
