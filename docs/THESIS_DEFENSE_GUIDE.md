# Guía de discusión y defensa de tesis

## Tesis central

TPV Ultra Smart desacopla el plano transaccional local de la disponibilidad WAN. Android y Flask operan en el edge; SQLite conserva ventas e inventario, mientras Supabase actúa como sincronización opcional. El módulo IA explica y opera herramientas por rol, y el módulo Telecom caracteriza la conectividad sin confundir métricas entre capas.

## Comandos de la IA para la defensa

Con rol Desarrollador:

```text
defensa completa
estructura de carpetas
módulos y funciones telecom
módulos y funciones seguridad
módulos y funciones memoria
inventario proyecto sin omitir
documentación
lee el documento TELECOM_ENGINEERING.md
telecom sin omitir
```

## Contenido que debe cubrir

### Problema

Una dependencia total de nube puede detener ventas ante latencia, fallos, handover o pérdida de conectividad.

### Solución

- Android/WebView como interfaz.
- Flask local como API edge.
- SQLite WAL como fuente transaccional local.
- Supabase opcional para sincronización.
- IA por roles para consulta y operación asistida.
- diagnóstico Telecom end-to-end.

### Ingeniería en Telecomunicaciones

- DNS y direcciones resueltas.
- establecimiento TCP.
- negociación TLS.
- RTT HTTP, mediana y P95.
- variación de RTT observada.
- solicitudes HTTP fallidas.
- goodput útil.
- clasificación heurística de calidad.
- continuidad local SQLite.

### IA

- detección de intención;
- handlers por rol;
- planificación ReAct;
- memoria persistente;
- skills y herramientas;
- caché y compactación;
- guardrails;
- lectura documental offline;
- LLM local opcional, no obligatorio.

### Seguridad

- onboarding local de un solo uso;
- identidad Desarrollador reservada;
- contraseña estricta, personal y exclusiva;
- bloqueo de reutilización en otras cuentas;
- sesiones con token;
- sanitización SQLi/XSS;
- secretos fuera del repositorio;
- auditoría.

### Calidad

- suite automatizada;
- gate de cobertura >= 50%;
- `ResourceWarning` tratado como error;
- CI antes del build APK;
- checksum y trazabilidad de artefactos;
- documentación indexada en SQLite.

## Limitaciones que deben reconocerse

- RTT HTTP no es eco ICMP.
- goodput no es capacidad física del enlace.
- solicitudes fallidas no equivalen exactamente a pérdida de paquetes.
- métricas radio RSRP/RSRQ/SINR requieren APIs Android nativas.
- un LLM GGUF no está incluido por defecto.
- la APK debug no sustituye una release firmada para distribución productiva.

Reconocer límites aumenta la credibilidad; no deben ocultarse.

## Futuras mejoras

1. release firmada estable;
2. mediciones reales Wi-Fi/celular/modo avión;
3. exportación CSV/JSON anonimizada;
4. dashboard temporal de KPIs Telecom;
5. TelephonyManager y NetworkCallback con consentimiento;
6. migraciones versionadas y recuperación probada;
7. cobertura de módulos activos >= 60%;
8. accesibilidad y pruebas en dispositivo de gama baja;
9. SBOM y análisis de dependencias;
10. modelo GGUF opcional evaluado contra consumo y tamaño.

## Regla de exhaustividad

La IA entrega respuestas extensas al Desarrollador y documentos completos por páginas. “Sin omitir” significa no eliminar información técnica autorizada; nunca incluye contraseñas, tokens, claves, hashes reutilizables o datos personales protegidos.
