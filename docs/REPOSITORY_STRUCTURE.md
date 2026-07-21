# Organización del repositorio

## Fuentes de verdad

| Área | Ubicación |
|---|---|
| Configuración Android | `app/build.gradle`, `app/src/main/AndroidManifest.xml` |
| Frontend WebView | `app/src/main/assets/frontend/` |
| Backend Flask | `app/src/main/python/app.py` y blueprints registrados |
| Persistencia | `database.py`, `db_connection.py`, `db/` |
| Agente IA | `app/src/main/python/ia/` |
| Seguridad | `security/`, `security_*.py`, `SECURITY.md` |
| Documentación | `README.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/` |
| Pruebas soportadas | `tests/unit/`, `tests/ia/`, `app/src/main/python/tests/` según `pytest.ini` |
| CI | `.github/workflows/android-ci.yml` |

## Directorios

```text
.github/       Automatización, CODEOWNERS y plantillas
app/           Proyecto Android y runtime Python
  src/main/
    assets/    Frontend real empaquetado
    java/      Integración Android
    python/    Backend, dominio, IA y documentación mínima offline
docs/          Documentación completa y evidencia histórica etiquetada
scripts/       Automatización general mantenida
tests/         Pruebas soportadas y suites auxiliares
tools/         Operación Termux, diagnóstico y robots E2E
diagramas/     Material visual de arquitectura/tesis
gradle/        Gradle Wrapper
```

## Política de archivos

No se versionan:

- secretos (`.tpv_*`, `.env` real, tokens, keystores);
- bases SQLite o WAL;
- cobertura generada;
- APK/AAB y directorios build;
- backups con sufijos `.backup`, `.bak` u `.old`;
- scripts `patch_*.py` de aplicación única;
- enlaces simbólicos absolutos de una máquina;
- pruebas generadas obsoletas fuera de la suite soportada.

Los ejemplos se nombran con sufijo `.example`, como `supabase_config.example.json`.

## Compatibilidad y deuda

El backend conserva algunos facades porque existen importaciones históricas. No deben eliminarse solo por tener pocas líneas. Para retirar un módulo:

1. buscar importaciones estáticas y dinámicas;
2. revisar blueprints registrados;
3. ejecutar suite y smoke de navegador;
4. compilar APK;
5. documentar la eliminación en CHANGELOG.

## Evidencia histórica

`docs/evidencias/` se conserva por trazabilidad académica. Cada reporte debe tratarse como histórico y asociarse a su commit; nunca sustituye el resultado de CI actual.

## Documentación consumida por la IA

`documentation_loader.py` indexa:

- documentos de texto en la raíz;
- todos los documentos soportados dentro de `docs/`, recursivamente;
- el corpus generado por `syncOfflineDocumentation` dentro del APK;
- copias esenciales de `app/src/main/python/knowledge/` como fallback.

Los nombres relativos, por ejemplo `docs/evidencias/.../REPORTE_TESIS_E2E.md`, evitan colisiones. La IA del Desarrollador puede buscar y abrir cualquier entrada sincronizada.
