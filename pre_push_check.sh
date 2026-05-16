#!/bin/bash
# PROTOCOLO PRE-PUSH - TPV UltraSmart
# Ejecutar SIEMPRE antes de git push

echo "╔══════════════════════════════════════════════════╗"
echo "║   🔍 PROTOCOLO PRE-PUSH v1.0                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

export PYTHONPATH="$HOME/tpv-chaquopy/app/src/main/python:$PYTHONPATH"
FAILS=0

# 1. Sintaxis Python
echo "1️⃣  Sintaxis Python..."
find . -name "*.py" -not -path "./.git/*" -not -path "./venv/*" -exec python -m py_compile {} \; 2>&1 | grep -c "Error" && FAILS=$((FAILS+1)) || echo "   ✅ OK"

# 2. Tests unitarios
echo "2️⃣  Tests unitarios (142)..."
python -m pytest tests/ -q --tb=line 2>&1 | tail -1
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

# 3. Simulación rápida
echo "3️⃣  Simulación rápida (75)..."
python test_simulacion_apk.py 2>&1 | grep -c "^  ❌" || echo "   ✅ OK"
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

# 4. Simulación maestra
echo "4️⃣  Simulación maestra (38)..."
python test_simulacion_apk_full.py 2>&1 | grep -c "^  ❌" || echo "   ✅ OK"
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

# 5. Stress test
echo "5️⃣  Stress test (7)..."
python test_stress_concurrente.py 2>&1 | grep -c "^  ❌" || echo "   ✅ OK"
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

# 5.5 Importación dinámica
echo "5.5️⃣ Importación dinámica..."
python test_importacion_dinamica.py 2>&1 | grep -c "^  ❌" || echo "   ✅ OK"
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

# 6. Auditoría completa
echo "6️⃣  Auditoría completa (52)..."
python test_auditoria_completa.py 2>&1 | grep -c "^  ❌" || echo "   ✅ OK"
if [ ${PIPESTATUS[0]} -ne 0 ]; then FAILS=$((FAILS+1)); fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
if [ $FAILS -eq 0 ]; then
    echo "║   ✅ TODO OK - PUEDES HACER PUSH                ║"
    echo "╚══════════════════════════════════════════════════╝"
    exit 0
else
    echo "║   ❌ $FAILS FALLOS - CORRIGE ANTES DE PUSH       ║"
    echo "╚══════════════════════════════════════════════════╝"
    exit 1
fi
