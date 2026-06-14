#!/bin/bash
cd ~/tpv-chaquopy/app/src/main/python
pkill -f "python3 app.py" 2>/dev/null
sleep 1
nohup python3 app.py > ~/tpv_server.log 2>&1 &
sleep 3
echo "✅ TPV corriendo en http://localhost:5000"
echo "📋 Log: ~/tpv_server.log"
curl -s http://localhost:5000/api/health
