# Evidencia E2E — TPV Chaquopy APK

- Fecha: `2026-06-18T21:11:35`
- Base URL: `http://127.0.0.1:5050`
- Run ID: `20260618_211131`
- Restauración local: `NO`
- Sincronización remota permitida: `NO`

## Boot observado

```txt
 ✔ [KERNEL    ] : Cargando máquina virtual Chaquopy en MainActivity... [READY]
 ✔ [STORAGE   ] : Montando SQLite WAL y persistencia local... [READY]
 ✔ [CRYPTO    ] : Inicializando HMAC y SHA-256... [READY]
 ✔ [NETWORK   ] : Verificando túnel con Supabase Cloud... [READY]
 ✔ [BLUEPRINTS] : Mapeando módulos Flask... [READY]
 ✔ [AI_ENGINE ] : Cargando Motor ReAct y Tools... [READY]
 ✔ [GUARDRAILS] : Activando escudos anti SQL Injection y Anti-Slop... [READY]
 ✔ [WEBVIEW   ] : Compilando Jinja2 y Assets frontend... [READY]
 ✔ [BIOMETRICS] : Enlazando AndroidX BiometricPrompt... [READY]
 ✔ [POS_CORE  ] : Calibrando DAOs de ventas e inventario... [READY]
```

## Matriz de pruebas

| Nº | Flujo | Estado | Detalle |
|---:|---|---|---|
| 1 | Detección de bases SQLite | PASSED | 2 archivo(s) detectado(s) |
| 2 | Backup previo de SQLite | PASSED | Backup en /data/data/com.termux/files/home/tpv-trabajo/.robot_backups/e2e_20260618_211131 |
| 3 | Boot hasta pantalla de login | PASSED | Backend respondió HTTP 200 en /health |
| 4 | Auditoría de tablas SQLite | OBS | 49 tabla(s). Incidencia: audit_logs sin columna usuario |
| 5 | Login rol cajero | OBS | No validó con credenciales/ruta actual |
| 6 | Login rol admin | PASSED | HTTP 200. Token Session OK |
| 7 | Escáner biométrico | FAILED | Error servidor HTTP 500 |
| 8 | Configuración de sucursal | PASSED | HTTP 200 en /api/config |
| 9 | Alta de empleado cajero | OBS | Respuesta no concluyente |
| 10 | Importación lote Excel | PASSED | 150 SKUs enviados. HTTP 200 en /api/inventario/importar-catalogo |
| 11 | Nomenclador categorías | SKIPPED | Ruta no encontrada o método no permitido |
| 12 | Nomenclador productos | OBS | Respuesta no concluyente |
| 13 | Nomencladores CRUD | OBS | Revisar payload o rutas reales |
| 14 | Seguridad anti SQL Injection | SKIPPED | No hubo endpoint de búsqueda detectable |
| 15 | Modo oscuro por API | PASSED | HTTP 200 en /api/state |
| 16 | Despacho de venta POS | OBS | Respuesta no concluyente |
| 17 | Cobro y emisión de ticket | OBS | No se confirmó ticket |
| 18 | Login rol cajero | OBS | No validó con credenciales/ruta actual |
| 19 | Agente IA rol cajero | FAILED | Respuesta fuera de rol/leak: root access, desarrollador principal |
| 20 | Login rol admin | PASSED | HTTP 200. Token Session OK |
| 21 | Agente IA rol admin | FAILED | Respuesta fuera de rol/leak: root access, desarrollador principal |
| 22 | Login rol developer | PASSED | HTTP 200. Token Session OK |
| 23 | Agente IA rol developer | PASSED | HTTP 200. Respuesta validada |
| 24 | Login rol developer | PASSED | HTTP 200. Token Session OK |
| 25 | Telemetría desarrollador | PASSED | HTTP 200 en /api/dev/metrics |
| 26 | Telemetría sin secretos | PASSED | No se detectaron claves obvias en respuesta |
| 27 | Reporte Z de fin de turno | PASSED | HTTP 200 en /api/reportes/resumen |
| 28 | Arqueo y cierre de caja | PASSED | HTTP 200 en /api/ventas/cierre |
| 29 | Sincronización Supabase Cloud | SKIPPED | Protegida para no contaminar nube. Use --allow-remote-sync en entorno de pruebas |
| 30 | Restauración modo virgen | SKIPPED | Desactivada por --no-restore |

## Resumen

- Total registros: `30`
- Passed: `15`
- Failed: `3`
- Observaciones: `8`
- Skipped: `4`

**Estado global recomendado:** `FAILED`

## Incidencias y observaciones

### Auditoría de tablas SQLite — OBS

49 tabla(s). Incidencia: audit_logs sin columna usuario

### Login rol cajero — OBS

No validó con credenciales/ruta actual

```txt
/api/auth/login(json)->401 | /api/auth/login(form)->400
```

### Escáner biométrico — FAILED

Error servidor HTTP 500

```txt
<!doctype html>
<html lang=en>
<title>500 Internal Server Error</title>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>

```

### Alta de empleado cajero — OBS

Respuesta no concluyente

```txt
/api/usuarios/crear->400 | /api/admin/usuarios/crear->400
```

### Nomenclador productos — OBS

Respuesta no concluyente

```txt
/api/inventario/entrada->400 | /api/tools/importar/productos->400
```

### Nomencladores CRUD — OBS

Revisar payload o rutas reales

### Despacho de venta POS — OBS

Respuesta no concluyente

```txt
/api/ventas/registrar->400
```

### Cobro y emisión de ticket — OBS

No se confirmó ticket

```txt
/api/ventas/registrar->400
```

### Login rol cajero — OBS

No validó con credenciales/ruta actual

```txt
/api/auth/login(json)->401 | /api/auth/login(form)->400
```

### Agente IA rol cajero — FAILED

Respuesta fuera de rol/leak: root access, desarrollador principal

```txt
{"anon_client_id":"","autenticado":true,"intencion":"GREETING","ok":true,"request_id":"req-de5fc05b4d2c","respuesta":"Buenas noches \ud83d\udcbb Root Access concedido Desarrollador Principal. Telemetr\u00eda del sistema, integridad de BD, logs y m\u00e9tricas de telecomunicaciones listas.","rol":"desarrollador","ui_action":null,"usuario_id":"dev-001"}

```

### Agente IA rol admin — FAILED

Respuesta fuera de rol/leak: root access, desarrollador principal

```txt
{"anon_client_id":"","autenticado":true,"intencion":"GREETING","ok":true,"request_id":"req-cd0fc3e4b849","respuesta":"Buenas noches \ud83d\udcbb Root Access concedido Desarrollador Principal. Telemetr\u00eda del sistema, integridad de BD, logs y m\u00e9tricas de telecomunicaciones listas.","rol":"desarrollador","ui_action":null,"usuario_id":"dev-001"}

```

## Nota para tesis

Esta evidencia fue generada automáticamente por un robot E2E. Los flujos marcados como SKIPPED no necesariamente fallan: pueden requerir configurar la ruta real del backend en `tools/robot_config.json`.

