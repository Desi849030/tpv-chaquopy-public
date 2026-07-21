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
import atexit
import os
import shutil
import sys
import tempfile

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
    smoke_dir = None
    if os.environ.get("TPV_SMOKE_USE_RUNTIME_DB") != "1":
        smoke_dir = tempfile.mkdtemp(prefix="tpv-smoke-")
        atexit.register(shutil.rmtree, smoke_dir, ignore_errors=True)
        os.environ["TPV_FILES_DIR"] = smoke_dir
        os.environ["TPV_DEMO_PASSWORD"] = "smoke-only-password"

    # 1) La app importa e inicializa un entorno aislado sin excepciones.
    try:
        import app as app_module
        from database import crear_tablas
        from tienda_routes import crear_tablas_tienda

        crear_tablas()
        crear_tablas_tienda()
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

    # 4) Contrato de autenticación. Nunca se usan credenciales hardcodeadas:
    # una instalación persistente puede haber rotado la contraseña inicial.
    try:
        rejected = client.post(
            "/api/auth/login",
            json={"username": "__smoke_invalid__", "password": "invalid"},
        )
        if rejected.status_code == 401:
            print(f"[{OK}] POST /api/auth/login rechaza credenciales inválidas")
        else:
            print(f"[{FAIL}] login inválido -> {rejected.status_code}")
            fallos.append("login-invalid-contract")

        smoke_user = os.environ.get("TPV_SMOKE_USERNAME", "").strip()
        smoke_password = os.environ.get("TPV_SMOKE_PASSWORD", "")
        if smoke_user and smoke_password:
            accepted = client.post(
                "/api/auth/login",
                json={"username": smoke_user, "password": smoke_password},
            )
            data = accepted.get_json(silent=True) or {}
            if accepted.status_code == 200 and data.get("ok"):
                print(f"[{OK}] login positivo verificado para '{smoke_user}'")
            else:
                print(f"[{FAIL}] login positivo -> {accepted.status_code} {data}")
                fallos.append("login-positive-contract")
        else:
            print(f"[{OK}] login positivo omitido (TPV_SMOKE_USERNAME/PASSWORD no configurados)")
    except Exception as e:  # noqa: BLE001
        print(f"[{FAIL}] login lanzó excepción: {e}")
        fallos.append(f"login: {e}")

    # 5) Agente IA responde (protege contra regresiones del import de ia.agent)
    try:
        resp = client.post("/api/agent/chat", json={"mensaje": "hola", "rol": "vendedor"})
        data = resp.get_json(silent=True) or {}
        respuesta = data.get("respuesta") or data.get("answer") or data.get("response") or ""
        if resp.status_code == 200 and respuesta:
            print(f"[{OK}] POST /api/agent/chat -> respuesta de {len(str(respuesta))} chars")
        else:
            print(f"[{FAIL}] POST /api/agent/chat -> {resp.status_code} (respuesta vacía)")
            fallos.append("agent/chat")
    except Exception as e:  # noqa: BLE001
        print(f"[{FAIL}] agent/chat lanzó excepción: {e}")
        fallos.append(f"agent/chat: {e}")

    # 6) Detección SQLi activa (protege el fix de seguridad)
    try:
        from security import check_sql_injection
        if check_sql_injection("1' OR '1'='1") and not check_sql_injection("Juan Perez"):
            print(f"[{OK}] check_sql_injection detecta ataques sin falsos positivos")
        else:
            print(f"[{FAIL}] check_sql_injection no funciona como se espera")
            fallos.append("sqli")
    except Exception as e:  # noqa: BLE001
        print(f"[{FAIL}] check_sql_injection lanzó excepción: {e}")
        fallos.append(f"sqli: {e}")

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
