# Roadmap APK 10/10 — resumen offline

Prioridades del proyecto:

1. Producción segura: rotar credencial inicial, proteger firma, auditar endpoints y probar backup/restauración.
2. Integridad: ventas idempotentes, migraciones versionadas, recuperación WAL y pruebas ante interrupciones.
3. Calidad: cero conexiones SQLite abiertas, reducir duplicación, cobertura de módulos activos >= 60%.
4. Android: pruebas API 21/objetivo, rendimiento, memoria, background y permisos.
5. UX: accesibilidad, estados offline/error, confirmaciones destructivas y ayuda por rol.
6. Operación: health checks, retención de logs, runbook, checksums y notas de release.

Una release requiere tests verdes, cobertura sobre el gate, cero secretos, APK compilado, migración/backup probados y documentación actualizada.
