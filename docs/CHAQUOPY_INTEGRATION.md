# Integración Android–Python con Chaquopy

## Propósito

Chaquopy permite ejecutar el backend Python dentro del proceso Android. TPV Ultra Smart reutiliza Flask, SQLite e IA tanto en APK como en Termux y CI, manteniendo una sola lógica de negocio.

## Configuración real

Fuente: `app/build.gradle`.

- Plugin: `com.chaquo.python`.
- Python embebido: 3.10.
- ABI: `arm64-v8a`, `armeabi-v7a`.
- Dependencias: Flask, Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click y Six.
- Source Python: `app/src/main/python`.
- Source generado: documentación offline en `app/build/generated/pythonDocs`.

La IA puede consultar los valores actuales con:

```text
Chaquopy
integración Python Android
```

## Flujo de arranque

```text
Android MainApplication/MainActivity
    → crea runtime Chaquopy
    → publica TPV_FILES_DIR y TPV_FRONTEND_DIR
    → ejecuta start_server.py
    → configura TPV_DB_PATH
    → inicializa seguridad y SQLite
    → registra Flask/IA/Telecom
    → Flask escucha 127.0.0.1:5050
    → WebView consume HTTP loopback
```

## Puentes de datos

| Variable | Uso |
|---|---|
| `TPV_FILES_DIR` | SQLite, secretos y archivos escribibles |
| `TPV_FRONTEND_DIR` | templates y estáticos del WebView |
| `TPV_DB_PATH` | ruta común para motores IA |
| System properties Java | transferencia inicial de rutas al runtime Python |

## Ventajas

- Reutilización del backend Python.
- Operación offline.
- SQLite local.
- Mismo comportamiento en Android y Termux.
- Testing Python independiente del emulador.
- Integración con Java para biometría y ciclo de vida.

## Limitaciones

- La versión Python está condicionada por Chaquopy.
- Paquetes nativos requieren wheels Android por ABI.
- El source empaquetado es de solo lectura.
- Modelos LLM aumentan significativamente el APK y RAM.
- El servidor Flask es local; no debe exponerse como servicio público.
- Una APK debug puede tener firma inestable entre runners.

## Decisiones de diseño

- Secretos y BD se guardan en `TPV_FILES_DIR`, no junto al código.
- La interfaz usa loopback para reducir superficie de red.
- Supabase es opcional; no forma parte del camino crítico de venta.
- La documentación se copia antes de `merge<Variant>PythonSources` con dependencia Gradle explícita.
- CI configura Python 3.10 para bytecode compatible.

## Evidencia

- Workflow Android CI exitoso.
- APK generado como artefacto.
- Smoke test de Flask y frontend.
- Suite Python en Termux y GitHub Actions.
- Health API con versión y estado SQLite.
