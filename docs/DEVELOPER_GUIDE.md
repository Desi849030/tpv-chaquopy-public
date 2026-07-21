# Guía del rol Desarrollador

## Propósito

`desarrollador` es la máxima autoridad funcional de TPV Ultra Smart. Está pensado para mantenimiento, diagnóstico, evolución del producto y recuperación operativa.

## Alcance: acceso funcional sin límites de rol

El rol **Desarrollador no tiene límites funcionales impuestos por la matriz de roles**. Su capacidad declarada es `all`, por lo que puede acceder a todos los módulos, herramientas y datos disponibles en la instalación:

- ventas, caja, cierres, gastos y reportes;
- catálogo, inventario general e inventario diario;
- usuarios, roles, privilegios y licencias;
- configuración local y sincronización Supabase;
- telemetría, métricas, logs y auditoría;
- diagnóstico de red, integridad SQLite y estado del sistema;
- motor IA, ReAct, memoria, skills, caché y guardrails;
- documentación técnica offline y referencia de API;
- consultas SQL de diagnóstico permitidas por la consola de desarrollo.

Esta regla se expresa en código como `access: ["all"]` y debe conservarse en todos los motores de autorización y en la IA.

## Acceso total no significa seguridad desactivada

El rol no está limitado por permisos de negocio, pero sigue sujeto a controles técnicos obligatorios:

1. autenticación y sesión válida;
2. protección contra secuestro o desajuste de sesión;
3. validación y sanitización de entradas;
4. auditoría de operaciones sensibles;
5. límites de integridad transaccional de SQLite;
6. gestión segura de secretos y configuración;
7. guardrails que impiden revelar credenciales o ejecutar instrucciones destructivas no confirmadas.

Estos controles protegen la instalación; no reducen el alcance funcional del Desarrollador.

## Capacidades de la IA para Desarrollador

La IA debe reconocer al Desarrollador como rol de acceso total y puede ayudar con:

- `estado del sistema` o `métricas`;
- `integridad de base de datos`;
- `logs`, `auditoría` y eventos recientes;
- `documentación` y `leer documento <nombre>`;
- `arquitectura`, `endpoints`, `schema` y `changelog`;
- inventario, ventas, usuarios, seguridad y telecomunicaciones;
- diagnóstico SQL de solo lectura;
- análisis de fallos y recomendaciones de mantenimiento.

La IA nunca debe mostrar contraseñas, tokens, claves privadas, hashes reutilizables ni secretos aunque el usuario tenga rol Desarrollador.

## Documentación offline

Al inicializar la base de datos, el backend sincroniza con SQLite todos los documentos de texto disponibles en la raíz y en `docs/`. Gradle copia el corpus al source set Python generado para que también esté completo dentro del APK. Además se crean alias estables y resúmenes esenciales de fallback. Esto permite que la IA los consulte sin conexión.

Documentos prioritarios:

- `README.md`
- `DEVELOPER_GUIDE.md`
- `ARCHITECTURE.md`
- `API_REFERENCE.md`
- `DATABASE_SCHEMA.md`
- `CONTRIBUTING.md`
- `CHECKLIST_RELEASE.md`
- `CHANGELOG.md`

Comandos de ejemplo:

```text
documentación
lee el documento DEVELOPER_GUIDE.md
muéstrame la arquitectura
abre el schema de base de datos
qué puede hacer el desarrollador
```

## Flujo recomendado de mantenimiento

```bash
git pull --ff-only origin main
python -m pip install --upgrade -r requirements.txt pytest pytest-cov
python -m pytest --cov=app/src/main/python --cov-config=.coveragerc --cov-fail-under=50
git status --short
```

Para Android:

```bash
./gradlew clean assembleDebug --no-build-cache
```

## Criterio de aceptación

Un cambio está listo cuando:

- no introduce secretos ni bases de datos en Git;
- las pruebas terminan sin fallos;
- la cobertura permanece por encima del gate;
- la documentación refleja el comportamiento real;
- el APK compila en CI;
- las operaciones sensibles quedan autenticadas y auditables.
