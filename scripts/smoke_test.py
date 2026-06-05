#!/usr/bin/env python3
"""
Smoke test del backend TPV UltraSmart.

Arranca la app Flask en proceso (sin servidor real) usando el test_client de
Flask y comprueba que las rutas y blueprints críticos responden. Sirve como red
de seguridad para refactors: ejecutar antes y después de cada cambio.

Uso:
    cd app/src/main/python
    python ../../../../scripts/smoke_test.py

Salida: imprime un resumen y devuelve exit code 0 si todo OK, 1 si algo falla.
"""
import os
import sys

# Permitir ejecutar desde la raíz del repo o desde python/
HERE = os.path.dirname(os.path.abspath(__file__))
PY_DIR = os.path.join(HERE, "..", "app", "src", "main", "python")
PY_DIR = os.path.abspath(PY_DIR)
if os.path.isdir(PY_DIR):
    os.chdir(PY_DIR)
    sys.path.insert(0, PY_DIR)
else:
    # Asumir que ya estamos dentro de python/
    sys.path.insert(0, os.getcwd())

OK = "\033[92mOK\033[0m"
FAIL = "\033[91mFALLO\033[0m"


def main() -> int:
    fallos = []

    # 1) La app importa sin excepciones
    try:
        import app as app_module
        flask_app = app_module.app
        print(f"[{OK}] app.py importa correctamente")
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(f"[{FAIL}] app.py NO importa: {e}")
        return 1

    # 2) Número de rutas registradas
    rutas = list(flask_app.url_map.iter_rules())
    print(f"[{OK}] {len(rutas)} rutas registradas")
    if len(rutas) < 50:
        fallos.append(f"Muy pocas rutas registradas: {len(rutas)}")

    client = flask_app.test_client()

    # 3) Endpoints críticos que deben responder
    checks = [
        ("GET", "/api/health", (200,)),
        ("GET", "/", (200,)),
        ("GET", "/static/css/modulo_0.css", (200, 304)),
    ]
    for method, path, ok_codes in checks:
        try:
            resp = client.open(path, method=method)
            if resp.status_code in ok_codes:
                print(f"[{OK}] {method} {path} -> {resp.status_code}")
            else:
                print(f"[{FAIL}] {method} {path} -> {resp.status_code} (esperado {ok_codes})")
                fallos.append(f"{method} {path} -> {resp.status_code}")
        except Exception as e:  # noqa: BLE001
            print(f"[{FAIL}] {method} {path} lanzó excepción: {e}")
            fallos.append(f"{method} {path}: {e}")

    # 4) Login de prueba
    try:
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "x"})
        data = resp.get_json(silent=True) or {}
        if resp.status_code == 200 and data.get("ok"):
            print(f"[{OK}] POST /api/auth/login -> usuario '{data.get('usuario', {}).get('username')}'")
        else:
            print(f"[{FAIL}] POST /api/auth/login -> {resp.status_code} {data}")
            fallos.append("login")
    except Exception as e:  # noqa: BLE001
        print(f"[{FAIL}] login lanzó excepción: {e}")
        fallos.append(f"login: {e}")

    print("-" * 50)
    if fallos:
        print(f"RESULTADO: {len(fallos)} fallo(s)")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("RESULTADO: todo OK ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
