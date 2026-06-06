# Arquitectura TPV Ultra Smart v1.0.0

## Vision General

App Android hibrida: WebView + Flask via Chaquopy. Python corre embebido en el APK.

## Flujo de Datos

    [WebView] <-> [Flask :5050] <-> [SQLite]
                    |
             [IndexedDB] (cliente)
                    |
             [Supabase] (cloud, opcional)

## Backend (Python/Flask)

- app.py: Servidor principal, registra Blueprints
- database.py: Singleton SQLite, CRUD, migraciones
- decorators.py: @requiere_login, @requiere_rol
- Routes por dominio: auth, inventory, ventas, config, tienda, ia, licencias
- ia/: Subpaquete con NLP, intents, memoria, guardrails

## Frontend (JS realmente cargados por templates/index.html)

El index.html carga un conjunto acotado de scripts (el resto de archivos en
static/js/ son fuentes/módulos históricos no enlazados):

- tpv_ui_dialogs.js -> diálogos modales con estilo (tpvConfirm/tpvAlert)
- tpv_api.js         -> capa de API + caché IndexedDB
- app_3.js           -> núcleo: estado, render POS/inventario/ventas, IndexedDB
- app_4.js / app_5.js -> exportación / módulo tienda
- app_6.js           -> autenticación, login, biometría, barra de usuario
- app_7.js           -> dashboard (gráficos Chart.js)
- app_8.js           -> debugger del desarrollador
- tpv_chat.js        -> agente IA (chat personalizado, botón arrastrable)
- tpv_privacidad.js  -> gestión de privilegios por rol
- tpv_dev_metrics.js -> panel de métricas del sistema
- tpv_seguridad.js   -> panel de seguridad y biometría
- tpv_licencias.js / tpv_ventas.js
- static/css/tpv_theme.css -> design system (paleta, dark mode, componentes)

## Almacenamiento Dual

| Capa | Tecnologia | Datos |
|------|-----------|-------|
| Cliente | IndexedDB | Productos, ventas, config (sin red) |
| Servidor | SQLite | Usuarios, permisos, inventario, logs |
| Cloud | Supabase | Sync multi-dispositivo (opcional) |

## Seguridad

- Auth por password + biometria nativa (huella/rostro)
- Decoradores Python por rol en todos los endpoints
- PCI compliance para pagos
- Attestation de integridad del dispositivo


## Sistema de Templates (Jinja2)

- index.html: Template principal (19 lineas)
- partials/_head.html: Meta, CSS, PWA
- partials/_splash.html: Pantalla de carga
- partials/_license_overlay.html: Overlay de licencia
- partials/_nav_header.html: Header y navegacion
- partials/_tab_content.html: Contenido de pestanas (814 lineas)
- partials/_modals.html: Dialogos modales (6)
- partials/_scripts.html: Carga de módulos JS + scripts inline

> Nota: el backend sirve directamente `templates/index.html` (no compone los
> partials en runtime). Los partials son la fuente de mantenimiento.

## Agente IA (offline)

- ia/agent_master.py: orquestador (intents + handlers + fallback).
- ia/intent_engine.py: clasificador de intenciones por keywords + fuzzy.
- ia/handlers_staff.py: respuestas por rol (vendedor, supervisor, admin, dev).
- ia/metrics.py (clase F): consultas reales a la BD — diario, semanal, top,
  abc, stock_critico, stock_resumen, buscar_stock, categorias, conteos.
- ia/catalog.py: caché de productos (precio/costo/stock) para el agente.
- Frontend tpv_chat.js: detecta rol/nombre, saludo contextual, botón movible.
