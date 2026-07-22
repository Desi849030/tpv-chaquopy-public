# Capas del sistema, tecnologías y modelo OSI

## Capas de arquitectura del proyecto

| Capa | Tecnologías/archivos | Responsabilidad |
|---|---|---|
| Android nativo | Java, Manifest, Gradle, Chaquopy | ciclo de vida, WebView, biometría, permisos y empaquetado |
| Presentación | HTML, CSS, JavaScript, Bootstrap | navegación, formularios, dashboard, accesibilidad y estado visual |
| API local | Flask, blueprints, JSON | rutas, sesión, autorización y contratos HTTP |
| Dominio | Python, models, database, db | ventas, inventario, usuarios, licencias y reglas |
| IA | intents, handlers, ReAct, memoria, skills | asistencia por rol, herramientas, contexto y guardrails |
| Telecom | telecom_diag, telecom_bp | DNS, TCP, TLS, RTT HTTP, P95, jitter, fallos y goodput |
| Persistencia Edge | SQLite WAL, TPV_FILES_DIR | continuidad local, auditoría, configuración y documentación |
| Sincronización | Supabase | réplica remota opcional |
| Calidad/entrega | pytest, coverage, GitHub Actions | validación, APK, artefactos y evidencia |

## Tecnologías por extensión

La IA genera el inventario dinámicamente. Puede explicar:

- `.py`: módulos, funciones, clases, métodos, firmas y rutas Flask;
- `.js`: funciones de interfaz, autenticación, ventas, inventario y debug;
- `.css`: archivos, variables CSS y media queries;
- `.html`: templates, parciales, IDs y componentes;
- `.java`/`.kt`: clases y métodos Android;
- `.gradle`: plugins, dependencias, variantes y tareas;
- `.xml`: Manifest y recursos Android;
- `.yaml`/`.yml`: OpenAPI y CI;
- `.md`: documentación y evidencia;
- `.puml`: diagramas de arquitectura.

Comandos:

```text
frontend CSS
módulos JavaScript
archivos HTML
Android Java
dependencias Gradle
tecnologías proyecto
```

## Modelo OSI aplicado

### Capa 7 — Aplicación

- Flask HTTP/REST.
- JSON API.
- Supabase REST.
- IA y documentación.
- Métricas: RTT HTTP, P95, solicitudes fallidas y goodput.

### Capa 6 — Presentación

- TLS y certificados.
- JSON y UTF-8.
- Serialización de respuestas.
- Métricas: versión TLS, cipher y bits.

### Capa 5 — Sesión

- Cookie Flask.
- token único de sesión.
- SSE.
- onboarding y autenticación.

En TCP/IP moderno estas responsabilidades suelen integrarse en aplicación/TLS.

### Capa 4 — Transporte

- TCP 443 hacia Supabase.
- TCP loopback Flask/WebView.
- Métrica: tiempo de establecimiento TCP.

No se capturan retransmisiones sin instrumentación adicional.

### Capa 3 — Red

- IPv4/IPv6.
- resolución de host a IP.
- direccionamiento local/remoto.

No se presenta HTTP como ICMP y no se ejecuta traceroute raw.

### Capa 2 — Enlace

- Wi-Fi o red celular administrada por Android.
- handover gestionado por el sistema operativo.

El runtime Python no inspecciona tramas ni MAC del medio.

### Capa 1 — Física

- radio, antena, canal, potencia y ruido.

No se mide actualmente RSSI/RSRP/RSRQ/SINR. Requiere APIs Android nativas, permisos y consentimiento.

## Flujo extremo a extremo

```text
Usuario → HTML/CSS/JS → WebView → HTTP loopback → Flask
        → dominio/IA → SQLite local
        → (opcional) DNS → TCP → TLS → HTTP Supabase
```

La venta crítica finaliza en SQLite aunque las capas WAN estén degradadas. Esa separación es el argumento central de continuidad operativa.

## Regla de discusión

Cada afirmación debe indicar:

1. capa;
2. método;
3. unidad;
4. punto de medición;
5. limitación;
6. dependencia online/offline.

La IA puede generar este mapa con `capas OSI` y el inventario completo mediante `/api/dev/project/inventory`.
