# Política de seguridad

## Versiones soportadas

La rama `main` recibe correcciones de seguridad. Las compilaciones o copias históricas no tienen garantía de mantenimiento.

## Reportar una vulnerabilidad

No abras un issue público con credenciales, datos personales, tokens, claves, rutas privadas o instrucciones completas de explotación.

Usa **GitHub Security Advisories** del repositorio cuando esté disponible o contacta de forma privada al mantenedor. Incluye:

- componente y versión/commit afectado;
- impacto observado;
- pasos mínimos de reproducción;
- propuesta de mitigación, si existe;
- confirmación de que no se accedió a datos de terceros.

## Controles del proyecto

- autenticación y autorización por roles;
- rol Desarrollador con acceso funcional `all`;
- sesiones con token y validación de desajustes;
- onboarding local de un solo uso sin contraseña predeterminada;
- hashing de contraseñas y migración de hashes heredados;
- sanitización XSS/SQLi;
- SQLite con integridad y WAL;
- auditoría de operaciones sensibles;
- secretos fuera del repositorio;
- CI con pruebas y gate de cobertura.

El acceso funcional total del Desarrollador no autoriza a desactivar autenticación, auditoría, protección de secretos ni validación de entradas.

## Secretos y artefactos prohibidos

Nunca se deben versionar:

- `.env` real;
- `.tpv_secret_key`, `.tpv_hmac_secret` o claves criptográficas;
- `*.db`, `*.db-wal`, `*.db-shm` o backups;
- keystores y contraseñas de firma;
- tokens de GitHub o Supabase;
- APK/AAB producidos localmente;
- logs con datos personales.

Si un secreto se publica, eliminar el archivo no es suficiente: hay que revocar y rotar el secreto inmediatamente.

> Aviso de migración: versiones históricas incluyeron claves runtime generadas dentro del árbol Python. Esas claves fueron retiradas de `main` y no deben reutilizarse. Cada instalación debe generar claves nuevas en `TPV_FILES_DIR`; cualquier integración que hubiera confiado en claves antiguas debe rotarlas.

## Dependencias

Chaquopy usa Python 3.10 y el stack Flask 2.2 fijado en `app/build.gradle`. Termux con Python 3.14 usa dependencias modernas mediante marcadores en `requirements.txt`. Toda actualización debe probar ambos caminos.
