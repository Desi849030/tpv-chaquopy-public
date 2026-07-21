# Contribuir a TPV Ultra Smart

## Principios

1. Mantener operación offline-first.
2. No debilitar autenticación, autorización ni auditoría.
3. El rol `desarrollador` conserva acceso funcional `all`; los demás roles siguen menor privilegio.
4. Evitar nuevas copias o facades si puede ampliarse el módulo activo.
5. Añadir pruebas de comportamiento, no pruebas que solo importan código.
6. Mantener documentación y código sincronizados.
7. No versionar secretos, bases de datos ni artefactos compilados.

## Preparación

```bash
git clone https://github.com/Desi849030/tpv-chaquopy-public.git
cd tpv-chaquopy-public
python -m pip install --upgrade -r requirements.txt pytest pytest-cov
```

## Flujo de trabajo

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/descripcion-corta
```

Usa prefijos claros:

- `feat/` nueva capacidad;
- `fix/` corrección;
- `test/` pruebas y cobertura;
- `docs/` documentación;
- `refactor/` mejora interna sin cambio de contrato.

## Validación obligatoria

```bash
python -m pytest \
  --cov=app/src/main/python \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=50
```

Cuando el cambio afecte Android, assets o arranque Chaquopy:

```bash
./gradlew clean assembleDebug --no-build-cache
```

## Estilo de cambios

- Funciones pequeñas y nombres descriptivos.
- Manejo explícito de errores; evita `except:` en código nuevo.
- Cierra conexiones, cursores, archivos y respuestas.
- Usa consultas parametrizadas para valores.
- No construyas nombres de tabla/columna desde entradas sin whitelist.
- Mantén compatibilidad con Python 3.10 para código empaquetado por Chaquopy.
- Conserva compatibilidad de pruebas con Python 3.14 en Termux.
- Añade type hints en interfaces nuevas cuando aporten claridad.

## Base de datos

Las pruebas usan una base temporal mediante `TPV_FILES_DIR`. Nunca deben modificar una base incluida en el árbol del proyecto.

Toda migración debe ser:

- idempotente;
- compatible con instalaciones existentes;
- segura ante ejecución repetida;
- probada con base vacía y base inicializada.

## Documentación para la IA

Los documentos curados se sincronizan a la tabla `documentacion`. Si agregas una guía que la IA debe leer:

1. guárdala en `docs/`;
2. añádela a `_DOCUMENTS` en `documentation_loader.py`;
3. proporciona una copia mínima en `app/src/main/python/knowledge/` si debe estar disponible dentro del APK;
4. actualiza el mapa de comandos del agente;
5. añade una prueba que verifique la sincronización.

## Commits

Formato recomendado:

```text
feat: add inventory reconciliation
fix: close SQLite connection in metrics endpoint
test: cover developer documentation loader
docs: reorganize developer guides
```

Cada commit debe representar una unidad coherente y dejar las pruebas relevantes en verde.

## Pull Request

Incluye:

- problema resuelto;
- cambios principales;
- riesgo y compatibilidad;
- evidencia de pruebas y cobertura;
- capturas cuando cambie UI;
- documentación actualizada;
- confirmación de que no hay secretos.

Usa la plantilla ubicada en `.github/PULL_REQUEST_TEMPLATE.md`.
