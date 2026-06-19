#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/tpv-trabajo"

echo "=================================================="
echo " TPV — EJECUCIÓN E2E COMPLETA EN UNA SOLA SESIÓN"
echo "=================================================="

echo
echo "[1/5] Deteniendo backend previo si existe..."
./tools/stop_backend_termux.sh || true

echo
echo "[2/5] Iniciando backend en segundo plano..."
./tools/start_backend_termux.sh

echo
echo "[3/5] Verificando backend..."
python tools/probar_backend_tpv.py

echo
echo "[4/5] Ejecutando robot E2E..."
python tools/robot_tesis_e2e.py \
  --config tools/robot_config.json \
  --wait 30 \
  --timeout 5 \
  --no-pause

echo
echo "[5/5] Validando que no quede backend bloqueando SQLite..."
./tools/stop_backend_termux.sh || true

echo
echo "=================================================="
echo " E2E FINALIZADO"
echo " Revisa: docs/evidencias/e2e_*/REPORTE_TESIS_E2E.md"
echo "=================================================="
