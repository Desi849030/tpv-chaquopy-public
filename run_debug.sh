#!/bin/bash
cd ~/tpv-chaquopy-public
source agent_env/bin/activate
export PYTHONPATH="$(pwd)/app/src/main/python"
export FLASK_DEBUG=1
python app/src/main/python/start_server.py
