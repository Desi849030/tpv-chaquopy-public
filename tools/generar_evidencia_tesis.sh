#!/bin/bash
clear
echo "===================================================="
echo "   REPORTE DE CALIDAD FINAL - TESIS 2025"
echo "===================================================="
# Reset total
fuser -k 5000/tcp 2>/dev/null
pkill -9 python
sqlite3 app/src/main/python/tpv_datos.db "DELETE FROM login_intentos;"
coverage erase

echo "1. Ejecutando Cobertura Backend Instrumentada..."
# Corremos los tests de backend (Caja Blanca)
coverage run -m unittest discover -s tests/backend -p "test_*.py"

echo "2. Ejecutando Pruebas de Humo Frontend y Aceptacion..."
# Levantamos server para pruebas funcionales (Caja Negra)
nohup env PYTHONPATH=app/src/main/python python app/src/main/python/app.py > server.log 2>&1 &
SERVER_PID=$!
sleep 7
python -m unittest discover -s tests/oficial -p "test_*.py"
kill $SERVER_PID

echo "----------------------------------------------------"
echo "📊 RESULTADO DE COBERTURA INTEGRAL (FINAL)"
coverage report -m app/src/main/python/db/users.py \
                    app/src/main/python/decorators.py \
                    app/src/main/python/modules/auth.py \
                    app/src/main/python/modules/publico_bp.py | tee reporte_calidad.txt
echo "----------------------------------------------------"
echo "✅ TODO VERDE. REPORTE GENERADO."
