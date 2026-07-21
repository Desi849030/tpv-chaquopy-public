# Centro de documentación

Este directorio es la fuente técnica y operativa de TPV Ultra Smart. Los documentos principales se sincronizan a SQLite para que la IA del rol Desarrollador pueda consultarlos offline.

## Empieza aquí

| Documento | Audiencia | Propósito |
|---|---|---|
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Desarrollo y soporte | Alcance total del Desarrollador, IA, mantenimiento y criterios de aceptación |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Desarrollo | Capas, componentes y flujos |
| [API_REFERENCE.md](API_REFERENCE.md) | Integración | Endpoints HTTP disponibles |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Backend/datos | Tablas y relaciones SQLite |
| [BACKEND_MAP.md](BACKEND_MAP.md) | Mantenimiento | Mapa entre módulos y responsabilidades |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Colaboradores | Flujo de cambios y estándares |
| [CHECKLIST_RELEASE.md](CHECKLIST_RELEASE.md) | Release | Validaciones previas a publicación |
| [ROADMAP_10_10.md](ROADMAP_10_10.md) | Producto/calidad | Prioridades para una APK de nivel producción |
| [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) | Mantenimiento | Fuentes de verdad, organización y política de archivos |
| [telecom_diagnostico.md](telecom_diagnostico.md) | Desarrollador | Diagnóstico de red y telecomunicaciones |

## Producto y evaluación

| Documento | Propósito |
|---|---|
| [DOCUMENTACION_TESIS.md](DOCUMENTACION_TESIS.md) | Documento académico principal |
| [DEFENSA.md](DEFENSA.md) | Guion y puntos para defensa |
| [DEMO_3_MIN.md](DEMO_3_MIN.md) | Demostración breve |
| [EVALUACION_ACADEMICA.md](EVALUACION_ACADEMICA.md) | Evidencia de evaluación |
| [MATRIZ_EVALUACION_APK.md](MATRIZ_EVALUACION_APK.md) | Matriz de calidad APK |
| [evidencias/README.md](evidencias/README.md) | Alcance y reglas de la evidencia histórica |

## Reglas documentales

1. Documentar el comportamiento actual, no planes no implementados.
2. Actualizar README, arquitectura y changelog cuando cambie una capacidad pública.
3. No incluir secretos, datos personales ni credenciales reales.
4. Marcar evidencia histórica como histórica; no presentarla como estado actual.
5. Mantener `DEVELOPER_GUIDE.md` alineado con la capacidad `all` del rol Desarrollador.
6. Ejecutar pruebas cuando se modifique el cargador de documentación offline.

## Lectura desde la IA

Con sesión de Desarrollador:

```text
documentación
lee el documento DEVELOPER_GUIDE.md
lee el documento ARCHITECTURE.md
siguiente
cerrar documento
```

La tabla `documentacion` se actualiza de forma idempotente durante la inicialización de SQLite.
