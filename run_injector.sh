#!/bin/bash
cd ~/tpv-chaquopy-public
source agent_env/bin/activate
export LLAMA_CPP_LIB="$(pwd)/agent_env/lib/python3.14/site-packages/llama_cpp/lib/libllama.so"
export LD_LIBRARY_PATH="$(pwd)/agent_env/lib/python3.14/site-packages/llama_cpp/lib/:$LD_LIBRARY_PATH"
export PYTHONPATH="$(pwd)/app/src/main/python"
python app/src/main/python/ai_injector.py
