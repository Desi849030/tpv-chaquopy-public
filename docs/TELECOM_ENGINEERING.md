# Enfoque de Ingeniería en Telecomunicaciones

## Título técnico sugerido

**Sistema TPV móvil offline-first con agente inteligente y diagnóstico end-to-end de conectividad para continuidad operativa en redes variables.**

## Problema

Los comercios móviles o pequeños operan sobre enlaces Wi-Fi/celulares con latencia, variación, interrupciones y capacidad variables. Un TPV dependiente de nube puede detener ventas ante degradación del enlace. El proyecto aplica una arquitectura edge/offline-first: la transacción crítica permanece local y la conectividad se mide y utiliza para sincronización no bloqueante.

## Aporte de telecomunicaciones

1. Observación por capas de DNS, TCP, TLS y HTTP.
2. Medición de RTT de aplicación, percentil 95 y variación.
3. Estimación de disponibilidad mediante solicitudes fallidas.
4. Medición de goodput útil de aplicación.
5. Correlación entre conectividad remota y continuidad local SQLite.
6. Clasificación reproducible de calidad para operación TPV.
7. Separación rigurosa entre métricas de aplicación y magnitudes de capa física.
8. Exposición segura mediante API y agente IA para soporte técnico.

## Relación con el modelo TCP/IP

| Capa | Elemento del proyecto |
|---|---|
| Acceso | Wi-Fi/celular administrado por Android; fuera del alcance Python directo |
| Internet | Direcciones IPv4/IPv6 resueltas y endpoint local |
| Transporte | Tiempo de conexión TCP |
| Seguridad sobre transporte | TLS, cipher, bits y certificado |
| Aplicación | HTTP REST Supabase, RTT, disponibilidad y goodput |
| Edge/local | Flask loopback y SQLite, independientes del enlace WAN |

## Hipótesis demostrable

> Si la conectividad WAN falla o se degrada, el TPV mantiene las operaciones esenciales localmente y conserva datos para sincronización posterior; el módulo de diagnóstico identifica la capa observable afectada sin confundir RTT HTTP con ICMP ni goodput con capacidad física.

## Variables experimentales

### Independientes

- interfaz de acceso;
- condición online/offline;
- operador o red;
- hora y carga;
- número de intentos;
- tamaño de muestra HTTP.

### Dependientes

- RTT mínimo, medio, mediano, estable en caliente (`latencia_warm_ms`) y P95;
- desviación estándar de RTT (`jitter_ms`) y variación absoluta consecutiva RFC 3550 (`jitter_rfc3550_ms`);
- reducción porcentual de latencia de aplicación por reutilización TLS (`HTTP Keep-Alive`, `1 RTT` frente a petición HTTPS en frío `TCP + TLS 1.3 + HTTP`);
- porcentaje de solicitudes fallidas;
- goodput útil de aplicación en Mbps y KiB/s;
- tiempos desagregados de resolución DNS (`getaddrinfo`), transporte TCP (`SYN/SYN-ACK`) y negociación TLS;
- tiempo de lectura e integridad del plano local SQLite WAL (`ops/s`, `PRAGMA quick_check`);
- continuidad funcional transaccional e idempotencia ante reintentos (`client_txn_id`).

## Campaña reproducible desde Termux (Wi-Fi vs. 4G/LTE)

El repositorio incluye el instrumento `tools/medir_red_tesis.py` (sin dependencias externas fuera de la biblioteca estándar de Python) para generar mediciones auditables JSON y tablas Markdown en `docs/mediciones_campo/`:

```bash
# 1. Con Wi-Fi activo en el dispositivo Android:
python tools/medir_red_tesis.py --etiqueta wifi_wlan0 --muestras 20

# 2. Desactivando Wi-Fi y operando sobre Datos Móviles (4G/LTE):
python tools/medir_red_tesis.py --etiqueta lte_datos_moviles --muestras 20

# 3. Generación automática de tabla comparativa consolidada:
python tools/medir_red_tesis.py --comparar
```

### Controladas

- versión APK y commit;
- dispositivo;
- endpoint Supabase;
- timeout;
- intentos;
- bytes objetivo;
- conjunto de pruebas funcionales.

## Procedimiento de laboratorio

1. Instalar la APK identificada por versión y checksum.
2. Registrar dispositivo, Android, red e interfaz.
3. Ejecutar diagnóstico completo tres veces.
4. Exportar JSON con timestamp UTC.
5. Ejecutar una venta local.
6. Activar modo avión.
7. repetir diagnóstico y confirmar degradación WAN sin datos inventados.
8. Ejecutar otra venta local.
9. restaurar conectividad y comprobar sincronización.
10. comparar muestras usando la misma configuración.

## Criterios de aceptación

- La API rechaza roles distintos de Desarrollador.
- `intentos` se limita a 1–10.
- La muestra se limita a 1 KiB–1 MB.
- Offline produce estado explícito, no valores falsos.
- Toda conexión y respuesta se cierra.
- El diagnóstico distingue método, unidad y limitación.
- La venta local funciona sin WAN.
- La documentación está disponible offline para la IA.

## Defensa oral

Puntos clave:

- No se presenta un HTTP GET como ping ICMP.
- Jitter es variación de muestras de RTT HTTP, no jitter RTP.
- Solicitudes fallidas no equivalen exactamente a pérdida de paquetes de capa 3.
- Goodput HTTP no es ancho de banda nominal.
- La arquitectura edge desacopla disponibilidad comercial de disponibilidad WAN.
- TLS forma parte del costo end-to-end y se mide por separado de TCP.
- SQLite representa el plano de continuidad local.

## Extensiones futuras

- TelephonyManager nativo para tipo de red, RSRP, RSRQ, RSSI y SINR con permisos adecuados.
- NetworkCallback para handover Wi-Fi/celular.
- series temporales y exportación CSV anonimizada.
- correlación QoS–tiempo de sincronización.
- pruebas controladas con emulación de latencia, pérdida y limitación de ancho de banda.
- métricas IPv6 y Happy Eyeballs.
