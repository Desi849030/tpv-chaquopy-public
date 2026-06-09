# Changelog — rama `refactor/backend-pro`

Mejoras profesionales sobre `main`. Cada punto verificado con `scripts/smoke_test.py`
y validación de sintaxis JS (`node --check`).

## Backend
- **Arranque limpio**: índices de BD corregidos (35/35, antes 27/35 con errores)
  y memoria de la IA inicializa correctamente.
- **Seguridad SQLi reforzada**: detección de tautologías `' OR '1'='1`, time-based
  (SLEEP/BENCHMARK), sentencias apiladas y comentarios. Sin falsos positivos.
- **Agente IA**: corregido import roto (`reasoning_engine` → `ia.react_core`) que
  rompía `ia/agent.py` y dejaba funciones sin definir.
- **Mocks eliminados**: `app.py` tenía endpoints mock (inventario/general,
  importar-catálogo, diario, conteo, licencias…) que **tapaban los blueprints
  reales** y devolvían datos falsos. Ahora se usan los reales → la importación de
  Excel actualiza de verdad el almacén general.
- **Sesión normalizada**: `usuario_actual()` garantiza `usuario_id` en los 8
  blueprints (evita 500 con sesiones antiguas).
- **Nuevo endpoint** `/api/dev/metrics`: RAM, almacenamiento (del directorio real,
  no la partición `/`), nº de índices y tablas de la BD. Con fallback `/proc/meminfo`
  para funcionar en el APK sin psutil.
- **Servidor multihilo** (`threaded=True`) para soportar el polling sin saturarse.
- **Rutas duplicadas** eliminadas (reconstruir-desde-productos, conteo).

## Frontend / UI-UX
- **Design system** moderno (`tpv_theme.css`): paleta índigo/cyan, sombras en capas,
  dark mode completo, foco accesible, animaciones suaves.
- **100% offline**: todas las librerías y la fuente Poppins se sirven localmente
  (sin CDN). Service worker v3 (cache-first assets, network-first código).
- **Bug crítico** corregido en `app_3.js` (token `\;` inválido) que rompía todo el
  archivo y dejaba la app sin funciones.
- **IndexedDB robusto**: apertura sin versión fija + autoreparación del store
  (resuelve `VersionError` y `object store not found`).
- **Gráficos**: corregido `Canvas is already in use` (instancias en `window.*`).
- **Tabs nuevas** integradas: Privilegios, Seguridad/Biometría, Métricas del Sistema
  (con visibilidad por rol).
- **Tabla de inventario**: inputs compactos que ya no ocultan los números.
- **Submenús** reorganizados por categoría; se corrigió que se ocultaran.
- **Diálogos con estilo** (`tpv_ui_dialogs.js`): `tpvConfirm`/`tpvAlert` reemplazan
  los `confirm`/`alert` nativos ("tipo Windows"). Logout y 12 alertas migrados.

## Biometría
- Login con **huella/rostro**: WebAuthn en navegador + puente `window.AndroidBiometric`
  para la huella nativa en el APK. Botón visible solo si el dispositivo lo permite.

## Agente IA
- Chat **personalizado**: detecta rol y nombre reales, saludo por hora del día,
  sugerencias contextuales por rol, botón flotante **arrastrable** (recuerda posición),
  indicador "escribiendo…". Envía rol/nombre al backend.
- **Bienvenida** en el login (toast con nombre + rol).

## Debug (desarrollador)
- Captura de errores JS, promesas, console y **fetch con tiempos**; estadísticas
  (peticiones, errores, lentas) e info del entorno/dispositivo al iniciar.

## CI/CD y limpieza
- Workflows: de 3 (2 rotos) a **uno** `ci.yml` (tests + APK debug/release firmado).
  Ahora también corre en ramas `refactor/**`.
- Limpieza: carpetas anidadas erróneas, backups, `database_old/`, código muerto.
- `pytest.ini` con suite estable verde (51 passed).
- `.gitignore` profesional; `scripts/smoke_test.py` como red de seguridad.

## Cómo probar
```bash
pip install -r requirements.txt
python scripts/smoke_test.py
cd app/src/main/python && python app.py   # http://127.0.0.1:5000
```
