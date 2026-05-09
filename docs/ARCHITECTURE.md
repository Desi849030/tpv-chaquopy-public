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

## Frontend (27 modulos JS)

- tpv_estado_shim.js -> tpvState inicial (shim anti-undefined)
- tpv_estado_sync.js -> IndexedDB + sincronizacion servidor
- tpv_autenticacion.js -> Login, roles, tabs
- tpv_tienda_cliente.js -> App tienda online independiente
- tpv_gestion_productos.js -> CRUD + import Excel (2,766 lineas)

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
- partials/_scripts.html: Carga de 27 modulos JS + scripts inline
