#!/bin/bash
cd ~/tpv-chaquopy-public

echo "Encendiendo entorno..."
source agent_env/bin/activate

echo "Configurando IA..."
export LLAMA_CPP_LIB="$(pwd)/agent_env/lib/python3.14/site-packages/llama_cpp/lib/libllama.so"
export LD_LIBRARY_PATH="$(pwd)/agent_env/lib/python3.14/site-packages/llama_cpp/lib/:$LD_LIBRARY_PATH"
export PYTHONPATH="$(pwd)/app/src/main/python"

echo "Arrancando servidor web en segundo plano..."
nohup python app/src/main/python/server.py > server.log 2>&1 &

sleep 2
echo "¡Listo! Abre Chrome y ve a: http://127.0.0.1:5000"
