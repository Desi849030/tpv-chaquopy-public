#!/data/data/com.termux/files/usr/bin/bash
set -e

cd app/src/main/assets/frontend

echo "Servidor iniciado en http://127.0.0.1:8080"
python3 -m http.server 8080
