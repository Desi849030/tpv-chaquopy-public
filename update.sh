#!/bin/bash
echo "🔄 Subiendo cambios a GitHub..."
git add .
git commit -m "Actualización $(date '+%Y-%m-%d %H:%M')"
git push origin main
echo "✅ Listo! Revisa: https://github.com/Desi849030/tpv-chaquopy/actions"
