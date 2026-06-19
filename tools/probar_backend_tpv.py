#!/usr/bin/env python3
from urllib.request import urlopen
from urllib.error import HTTPError
import time

ports = [5050, 5000, 5001, 8000, 8080, 8888, 3000]
paths = ["/", "/login", "/health", "/api/health", "/status", "/api/status"]

print("Buscando backend TPV local...\n")

found = []

for port in ports:
    for path in paths:
        url = f"http://127.0.0.1:{port}{path}"
        try:
            start = time.time()
            r = urlopen(url, timeout=2)
            elapsed = round(time.time() - start, 2)
            print(f"OK   {url} -> HTTP {r.status} en {elapsed}s")
            found.append((port, path, r.status))
        except HTTPError as e:
            print(f"HTTP {url} -> {e.code}")
            found.append((port, path, e.code))
        except Exception as e:
            print(f"NO   {url} -> {type(e).__name__}")

print("\nResultado:")
if found:
    print("Backend detectable. Usa uno de estos puertos:")
    for port, path, status in found:
        print(f"  http://127.0.0.1:{port}{path} -> HTTP {status}")
else:
    print("No se detectó backend local accesible desde Termux.")
    print("Abre la APK, espera al login y prueba de nuevo.")
