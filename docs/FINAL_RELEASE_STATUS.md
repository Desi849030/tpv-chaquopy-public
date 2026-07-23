# Estado de cierre para entrega universitaria

## Versión candidata

- Producto: TPV Ultra Smart.
- Versión: 6.13.1.
- Especialidad: Ingeniería en Telecomunicaciones.
- Estado: candidata de entrega académica; no certificada para producción comercial.

## Validación automatizada de referencia

```text
620 passed
71 skipped
60.19% coverage
coverage gate: >= 50%
```

El porcentaje puede variar entre Python 3.11 y 3.14 por diferencias de instrumentación. La suite y el gate son la referencia reproducible.

## Logros cerrados

- arquitectura offline-first;
- Android + WebView + Chaquopy + Flask + SQLite;
- IA por roles, ReAct, memoria, herramientas y documentación;
- diagnóstico Telecom por capas;
- onboarding y credencial exclusiva del Desarrollador;
- documentación canónica sin duplicados visibles;
- explicaciones técnicas y para jurado no técnico;
- UI responsive y accesible por diseño;
- debug deduplicado en offline;
- hardening HTTP;
- CI Python y build Android;
- checksum y trazabilidad de artefactos;
- cobertura de módulos activos de seguridad y Edge AI reforzada.

## Limitaciones aceptadas y declaradas

- la APK de CI es debug mientras no exista una firma release institucional;
- RSRP/RSRQ/SINR requieren desarrollo Android nativo futuro;
- no se incluye un LLM GGUF por defecto;
- accesibilidad TalkBack requiere validación manual;
- el estado del arte necesita bibliografía externa revisada por el estudiante;
- pruebas de campo Telecom deben ejecutarse en dispositivo y redes reales;
- no se declara certificación fiscal, PCI oficial o aptitud comercial.

## Trabajo futuro, no bloqueante para tesis

1. release firmada;
2. dashboard temporal Telecom;
3. exportación CSV anonimizada;
4. TelephonyManager/NetworkCallback;
5. migraciones de schema versionadas;
6. cobertura incremental de loyalty, usuarios y proactividad;
7. evaluación cuantitativa de intents;
8. SBOM y análisis externo de seguridad.

## Regla de congelación

Después de esta versión solo se aceptan:

- correcciones reproducibles;
- mejoras documentales;
- evidencia experimental;
- ajustes de compatibilidad necesarios para compilar/instalar.

No se deben añadir módulos grandes antes de la defensa.
