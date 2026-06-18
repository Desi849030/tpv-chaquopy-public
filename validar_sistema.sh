#!/bin/bash
echo "🚀 Iniciando validación total del sistema (Suite Completa)..."

# 1. Limpiar procesos previos en el puerto 5000
fuser -k 5000/tcp 2>/dev/null

# 2. Definir rutas absolutas
ROOT_DIR=$(pwd)

# 3. Arrancar servidor en background
echo "📡 Arrancando servidor en segundo plano..."
cd "$ROOT_DIR/app/src/main/python"
export PYTHONPATH=$ROOT_DIR/app/src/main/python:$PYTHONPATH
nohup python app.py > "$ROOT_DIR/server_test.log" 2>&1 &
SERVER_PID=$!

# 4. Esperar a que el servidor esté listo (la IA y DB tardan un poco)
echo "⏳ Esperando 10 segundos para inicialización completa..."
sleep 10

# 5. Ejecutar TODOS los tests usando unittest discover
echo "🧪 Ejecutando suite de pruebas completa (buscando todos los test_*.py)..."
cd "$ROOT_DIR"
python -m unittest discover -s . -p "test_*.py" -v
TEST_RESULT=$?

# 6. Resultado
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON (10/10)"
else
    echo "❌ ALGUNOS TESTS FALLARON."
    echo "--- Últimas líneas del log del servidor ---"
    tail -n 30 "$ROOT_DIR/server_test.log"
fi

# 7. Limpieza final
echo "🧹 Deteniendo servidor de pruebas..."
kill $SERVER_PID 2>/dev/null
fuser -k 5000/tcp 2>/dev/null

exit $TEST_RESULT
