# Estado del arte y posicionamiento técnico

## Alcance

Comparación conceptual de enfoques relevantes para un TPV móvil offline-first con IA edge y diagnóstico de telecomunicaciones. Para una memoria académica final, esta sección debe complementarse con bibliografía científica, normas y referencias institucionales en el formato exigido por la universidad.

## Enfoques comparados

| Enfoque | Fortaleza | Limitación frecuente | Respuesta del proyecto |
|---|---|---|---|
| POS cloud puro | centralización y acceso remoto | dependencia WAN | SQLite local + sincronización opcional |
| POS Android local | continuidad y baja latencia | poca observabilidad/inteligencia | IA por roles + Telecom integrado |
| PWA | portabilidad | acceso nativo restringido | WebView + Chaquopy + biometría Java |
| Chatbot cloud | lenguaje flexible | privacidad, costo y falta de offline | intents/ReAct/memoria local; LLM opcional |
| Edge AI | privacidad y respuesta local | recursos limitados | motor modular liviano y explicable |
| Monitor de red separado | métricas técnicas | no correlaciona operación comercial | diagnóstico dentro del TPV |
| Sincronización eventual | tolerancia a desconexión | conflictos y consistencia | SQLite fuente local + sync controlada |

## Brecha identificada

Existe una brecha entre:

1. continuidad transaccional local;
2. asistencia inteligente explicable;
3. observabilidad de la conectividad;
4. integración Android reproducible;
5. evidencia académica trazable.

TPV Ultra Smart integra esos elementos en una sola APK educativa.

## Diferenciadores

- La venta finaliza localmente aunque falle WAN.
- La IA conoce rol, herramientas, documentos y estructura del proyecto.
- El Desarrollador puede consultar código con AST sin ejecutar módulos.
- Telecom declara método, unidad y limitación.
- Chaquopy reutiliza Python en Android, Termux y CI.
- Documentación completa disponible offline.
- Tests bloquean el APK si no se supera el gate.

## Relación con paradigmas actuales

### Edge computing

La transacción y la IA base se ejecutan cerca del usuario. La nube amplía, pero no determina, la disponibilidad.

### Offline-first

Se diseña primero el estado local y luego la sincronización. No es simplemente una caché temporal.

### IA explicable

La respuesta puede indicar intención, herramienta, fuente, módulo y limitación. El LLM no es requisito para la operación.

### Observabilidad end-to-end

Se separan DNS, TCP, TLS y HTTP. Las métricas radio no implementadas se declaran como trabajo futuro.

## Limitaciones frente a soluciones industriales

- No incluye certificación fiscal por país.
- No implementa actualmente EMV/contactless real.
- No mide RSRP, RSRQ o SINR sin módulo Android nativo.
- No incluye un modelo LLM en el APK base.
- Requiere release firmada estable para distribución formal.
- El estudio experimental de campo debe realizarse en dispositivo real.

## Futuras líneas de investigación

- correlación QoS–tiempo de sincronización;
- handover Wi-Fi/celular con NetworkCallback;
- RSRP/RSRQ/SINR con TelephonyManager y consentimiento;
- conflictos de sincronización multi-terminal;
- evaluación cuantitativa de IA por intención;
- consumo energético y memoria del edge AI;
- seguridad de backups y aprovisionamiento;
- pruebas con emulación de latencia/pérdida.

## Recomendación bibliográfica

La versión final de tesis debe citar fuentes verificables sobre:

- edge computing;
- offline-first/local-first software;
- QoS/QoE;
- modelos OSI y TCP/IP;
- TLS;
- SQLite/WAL;
- sistemas POS móviles;
- IA explicable y agentes;
- Android WebView/Chaquopy.

La IA puede explicar esta comparación, pero no debe inventar autores, DOI, normas o referencias no incorporadas y verificadas por el estudiante.
