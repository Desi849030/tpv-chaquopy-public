# Diagnóstico de Telecomunicaciones

Módulo académico y operativo para evaluar el comportamiento end-to-end de la conectividad usada por TPV Ultra Smart. Está disponible exclusivamente para el rol **Desarrollador**.

## Objetivo de ingeniería

Separar y medir fenómenos observables por capa. El diagrama fuente está en `diagramas/trabajo4/11_diagnostico_telecom.puml`.



| Plano/capa | Medición | Unidad |
|---|---|---|
| Endpoint local | IP, hostname, plataforma | texto/IP |
| Resolución | `getaddrinfo` y direcciones | ms |
| Transporte | establecimiento TCP | ms |
| Seguridad | negociación TLS, versión y cipher | ms/bits |
| Aplicación | RTT de solicitud HTTP | ms |
| Variación | desviación estándar de RTT HTTP | ms |
| Disponibilidad | solicitudes HTTP fallidas | % |
| Transferencia | goodput de muestra HTTP | Mbps, KiB/s |
| Plano local | lecturas SQLite e integridad | ops/s |

## Terminología rigurosa

- **RTT HTTP**: tiempo completo de una solicitud de aplicación. Incluye red, TLS reutilizado o nuevo, servidor y procesamiento. No es ping ICMP.
- **Jitter observado**: desviación estándar de las muestras de RTT HTTP. No representa jitter RTP.
- **Solicitudes fallidas**: porcentaje de intentos HTTP sin respuesta válida. No equivale exactamente a pérdida física de paquetes.
- **Goodput HTTP**: bytes útiles recibidos por tiempo. No equivale a capacidad nominal del enlace ni a throughput de capa 2.
- **P95**: percentil 95 interpolado de las muestras de RTT.

Estas distinciones evitan conclusiones técnicamente incorrectas durante la defensa.

## Acceso

- Chat IA del Desarrollador.
- Menú **Herramientas → Desarrollador → Diagnóstico Telecom**.
- API `/api/dev/telecom/*` con sesión de Desarrollador.

Otros roles reciben HTTP `403`.

## Comandos de IA

```text
diagnóstico completo
mide latencia y jitter
mide throughput
resuelve DNS
analiza TLS
muestra mi IP
velocidad SQLite
```

La respuesta completa informa metodología, unidades y limitaciones.

## API

| Método | Endpoint | Resultado |
|---|---|---|
| GET | `/api/dev/telecom/red` | Endpoint local |
| GET | `/api/dev/telecom/dns?host=example.com` | Resolución DNS |
| GET | `/api/dev/telecom/latencia?intentos=5` | RTT HTTP, P95, jitter, fallos y clasificación |
| GET | `/api/dev/telecom/throughput?bytes=100000` | Goodput HTTP acotado |
| GET | `/api/dev/telecom/tls` | TCP, TLS, cipher y certificado |
| GET | `/api/dev/telecom/sqlite` | Plano local SQLite |
| GET | `/api/dev/telecom/full` | Diagnóstico agregado |
| GET | `/api/dev/telecom/metodologia` | Definiciones y limitaciones |

Parámetros limitados por seguridad:

- `intentos`: 1–10.
- `bytes`: 1 KiB–1 MB.
- `host`: máximo 253 caracteres, sin URL, path, query ni credenciales.

## Clasificación de calidad

La clasificación es una heurística del proyecto para interacción TPV, no un estándar regulatorio.

Puntaje inicial: 100.

### Penalización por RTT HTTP

| RTT | Penalización |
|---|---:|
| <= 80 ms | 0 |
| 80–150 ms | 10 |
| 150–300 ms | 25 |
| > 300 ms | 45 |

### Penalización por jitter observado

| Jitter | Penalización |
|---|---:|
| <= 10 ms | 0 |
| 10–25 ms | 5 |
| 25–50 ms | 15 |
| > 50 ms | 30 |

### Penalización por solicitudes fallidas

| Fallos | Penalización |
|---|---:|
| 0% | 0 |
| 0–2% | 5 |
| 2–5% | 20 |
| > 5% | 40 |

| Puntaje | Estado |
|---|---|
| 90–100 | excelente |
| 75–89 | buena |
| 50–74 | degradada |
| 0–49 | crítica |

Una red con puntaje >= 50 se considera operable para el TPV, recordando que las ventas locales no dependen de Internet.

## Diseño offline-first

La conectividad remota puede estar degradada o ausente y el sistema sigue operando con SQLite. En ese caso:

- red local y SQLite continúan medibles;
- pruebas Supabase indican `offline` o no disponibles;
- no se inventan valores de latencia, jitter o pérdida;
- sincronización queda pendiente;
- la venta local no debe bloquearse.

## Reproducibilidad

Para registrar una evidencia:

1. Anotar commit, dispositivo, Android, interfaz y operador.
2. Ejecutar al menos tres diagnósticos.
3. Mantener número de intentos y tamaño de muestra.
4. Guardar timestamp UTC y JSON completo.
5. No comparar redes con parámetros distintos.
6. Explicar carga del servidor, radio y condiciones del entorno.

## Limitaciones

- Android puede restringir información de gateway, DNS o interfaz sin APIs nativas adicionales.
- Supabase aporta procesamiento remoto, por lo que RTT y goodput son end-to-end.
- Una muestra pequeña no caracteriza toda la capacidad del canal.
- No se implementa captura de paquetes, ICMP raw, RSSI celular, RSRP, RSRQ, SINR ni identificación de celda porque requieren permisos/APIs específicas.
- Para investigación radio avanzada se necesitaría un módulo Android nativo con `TelephonyManager` y consentimiento explícito.

## Privacidad y seguridad

- Solo Desarrollador.
- No se devuelve la API key.
- No se almacenan tokens en el reporte.
- Se limitan intentos y bytes.
- Los diagnósticos no deben incluir IMSI, IMEI, número telefónico ni identificadores personales.
