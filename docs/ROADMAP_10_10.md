# Roadmap de calidad APK 10/10

Este documento prioriza mejoras verificables. “10/10” significa una APK segura, reproducible, mantenible, accesible y recuperable; no solo una interfaz atractiva.

## Estado actual

- [x] Operación offline-first.
- [x] Backend Flask embebido con Chaquopy.
- [x] SQLite local y sincronización opcional.
- [x] IA por roles con Desarrollador `all`.
- [x] Más de 500 pruebas soportadas.
- [x] Gate de cobertura >= 50%.
- [x] CI que bloquea el APK cuando Python falla.
- [x] Documentación offline para IA.
- [x] Diagnóstico telecom por capas con metodología, unidades y limitaciones explícitas.
- [x] Cero `ResourceWarning` de SQLite en la suite soportada.
- [ ] Release firmado y reproducible en CI.
- [ ] Cobertura >= 60% en módulos activos.
- [ ] Auditoría de accesibilidad y rendimiento Android.

## P0 — Antes de producción

### Seguridad

- Rotar la credencial inicial de Desarrollador en el primer inicio.
- Impedir contraseñas demo en builds release.
- Verificar que el keystore y sus contraseñas solo estén en GitHub Secrets.
- Revisar endpoints mutables: autenticación, rol, CSRF y auditoría.
- Ejecutar análisis de secretos y dependencias en CI.
- Validar backup/restauración cifrada con una base real anonimizada.

### Integridad

- Probar apagado durante venta, cierre e importación.
- Garantizar idempotencia mediante IDs de transacción.
- Añadir migraciones versionadas y rollback documentado.
- Verificar recuperación de WAL y corrupción controlada.

## P1 — Calidad profesional

### Código

- Cerrar todas las conexiones SQLite de forma determinista.
- Eliminar módulos duplicados solo después de confirmar que no están registrados.
- Reducir gradualmente `app.py` y `database.py` sin crear nuevas copias.
- Definir contratos de respuesta comunes y errores estables.
- Sustituir `except:` nuevos por excepciones específicas y logging.

### Pruebas

- Subir cobertura de módulos activos a 60%, después a 70%.
- Priorizar `loyalty_routes`, usuarios, catálogo, ventas, seguridad y recuperación.
- Añadir pruebas de migración desde versiones publicadas.
- Añadir smoke test de APK en emulador.
- Ejecutar matriz Python 3.10/3.14 donde sea viable.

### Android

- Probar API 21, API objetivo y un dispositivo de gama baja.
- Medir tiempo de arranque, RAM, tamaño APK y latencia de venta.
- Validar rotación, retorno desde background y proceso terminado.
- Revisar permisos, network security config y backup rules.

## P2 — Experiencia de usuario

- Accesibilidad: contraste, TalkBack, tamaño táctil y escalado de fuente.
- Estados vacíos, carga, offline y error consistentes.
- Confirmación para acciones destructivas.
- Recuperación clara ante sesión expirada o sincronización pendiente.
- Exportación/importación con progreso y resumen de errores.
- Manual integrado por rol y ayuda contextual.

## P3 — Operación y observabilidad

- Métricas locales sin datos personales.
- Exportación de diagnóstico con consentimiento.
- Política de retención de logs.
- Health checks de SQLite, espacio disponible y versión de schema.
- Runbook de incidentes y recuperación.
- Notas de release y artefactos con checksum.

## Definición de terminado

Una release candidata cumple:

```text
[ ] tests sin fallos
[ ] cobertura >= gate
[ ] cero secretos detectados
[ ] cero warnings críticos de recursos
[ ] APK debug y release compilados
[ ] migración y rollback probados
[ ] backup y restauración probados
[ ] accesibilidad y rendimiento revisados
[ ] documentación y changelog actualizados
[ ] checksum y notas de release publicados
```
