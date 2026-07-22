# Referencia de API — TPV Ultra Smart v6.13.1

> Documento autogenerado a partir de decoradores Flask `route/get/post/put/delete/patch`.
> Total de endpoints declarados: **350** en **48** módulos.
> Generado: 2026-07-22

> Los permisos dependen de los decoradores y controles de sesión de cada función.

## Índice de módulos

- [`ai_routes.py`](#ai-routes) — 12 endpoints
- [`api_routes.py`](#api-routes) — 2 endpoints
- [`app.py`](#app) — 77 endpoints
- [`dictionary/routes.py`](#dictionaryroutes) — 5 endpoints
- [`ia/proactive_routes.py`](#iaproactive-routes) — 3 endpoints
- [`ia_assistant_routes.py`](#ia-assistant-routes) — 5 endpoints
- [`loyalty_routes.py`](#loyalty-routes) — 8 endpoints
- [`modules/admin_licencias.py`](#admin-licencias) — 4 endpoints
- [`modules/admin_privilegios.py`](#admin-privilegios) — 3 endpoints
- [`modules/admin_usuarios.py`](#admin-usuarios) — 4 endpoints
- [`modules/agent.py`](#agent) — 2 endpoints
- [`modules/agent_chat_bp.py`](#agent-chat-bp) — 3 endpoints
- [`modules/ai_analytics.py`](#ai-analytics) — 6 endpoints
- [`modules/ai_dashboard.py`](#ai-dashboard) — 2 endpoints
- [`modules/ai_fraud.py`](#ai-fraud) — 2 endpoints
- [`modules/ai_predictor.py`](#ai-predictor) — 2 endpoints
- [`modules/ai_shortcuts_bp.py`](#ai-shortcuts-bp) — 4 endpoints
- [`modules/assistant_chat.py`](#assistant-chat) — 6 endpoints
- [`modules/assistant_memory.py`](#assistant-memory) — 5 endpoints
- [`modules/auth.py`](#auth) — 15 endpoints
- [`modules/catalogo_bp.py`](#catalogo-bp) — 8 endpoints
- [`modules/clientes_bp.py`](#clientes-bp) — 2 endpoints
- [`modules/diag_bp.py`](#diag-bp) — 13 endpoints
- [`modules/docs_dev_bp.py`](#docs-dev-bp) — 1 endpoints
- [`modules/i18n_bp.py`](#i18n-bp) — 2 endpoints
- [`modules/inventory.py`](#inventory) — 17 endpoints
- [`modules/metrics.py`](#metrics) — 1 endpoints
- [`modules/project_intelligence_bp.py`](#project-intelligence-bp) — 5 endpoints
- [`modules/publico_bp.py`](#publico-bp) — 8 endpoints
- [`modules/reportes_bp.py`](#reportes-bp) — 5 endpoints
- [`modules/settings_other.py`](#settings-other) — 7 endpoints
- [`modules/settings_supabase.py`](#settings-supabase) — 11 endpoints
- [`modules/system.py`](#system) — 9 endpoints
- [`modules/telecom_bp.py`](#telecom-bp) — 8 endpoints
- [`modules/tests_info_bp.py`](#tests-info-bp) — 3 endpoints
- [`modules/tienda_bp.py`](#tienda-bp) — 3 endpoints
- [`modules/tools_bp.py`](#tools-bp) — 19 endpoints
- [`modules/usuarios_bp.py`](#usuarios-bp) — 5 endpoints
- [`modules/ventas_atomic_v10.py`](#ventas-atomic-v10) — 5 endpoints
- [`modules/ventas_descuentos.py`](#ventas-descuentos) — 3 endpoints
- [`modules/ventas_gastos.py`](#ventas-gastos) — 3 endpoints
- [`modules/ventas_historial.py`](#ventas-historial) — 3 endpoints
- [`pwa_routes.py`](#pwa-routes) — 3 endpoints
- [`rol_display.py`](#rol-display) — 1 endpoints
- [`security_routes.py`](#security-routes) — 8 endpoints
- [`security_websocket.py`](#security-websocket) — 4 endpoints
- [`server.py`](#server) — 5 endpoints
- [`tienda_routes.py`](#tienda-routes) — 18 endpoints

---

## ai_routes
<a name="ai-routes"></a>
Archivo: `app/src/main/python/ai_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/predictor` | `predictor` | Alias para compatibilidad. |
| GET | `/predict/dashboard` | `predict_dashboard` |  |
| GET | `/fraud` | `fraud` | Alias para compatibilidad. |
| GET | `/fraud/dashboard` | `fraud_dashboard` |  |
| GET | `/analytics` | `analytics` | Endpoint combinado para compatibilidad. |
| GET | `/analytics/abc` | `analytics_abc` |  |
| GET | `/analytics/cross-selling` | `analytics_cross_selling` |  |
| GET | `/analytics/prices` | `analytics_prices` |  |
| GET | `/prices` | `prices` | Alias para compatibilidad. |
| GET | `/kpis` | `kpis` |  |
| GET | `/dashboard` | `general_dashboard` | Dashboard general llamado por ia_cargarTodo(). |
| GET | `/kpis` | `general_kpis` | KPIs generales llamado por ia_cargarKPIs(). |

## api_routes
<a name="api-routes"></a>
Archivo: `app/src/main/python/api_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/health` | `api_health` |  |
| GET | `/api/config/publica` | `api_config_publica` |  |

## app
<a name="app"></a>
Archivo: `app/src/main/python/app.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/metrics` | `api_metrics` |  |
| GET | `/api/notificaciones` | `api_notificaciones` |  |
| GET | `/api/seguridad/check` | `api_seguridad_check` |  |
| POST | `/api/db/backup` | `api_db_backup` |  |
| GET | `/api/qr/<producto_id>` | `api_qr` |  |
| GET | `/api/reportes/exportar` | `api_reportes_exportar` |  |
| GET | `/` | `index` | Sirve index.html buscando en la carpeta del proyecto y subcarpetas. |
| GET | `/<path:filename>` | `serve_static` | Sirve archivos .js, .css etc buscando en la carpeta del proyecto y subcarpetas. |
| GET | `/api/setup/status` | `api_setup_status` |  |
| POST | `/api/setup/developer` | `api_setup_developer` |  |
| POST | `/api/auth/login` | `api_login` |  |
| POST | `/api/auth/logout` | `api_logout` |  |
| GET | `/api/auth/me` | `api_me` |  |
| POST | `/api/auth/cambiar-password` | `api_cambiar_password` |  |
| GET | `/api/privilegios/<rol>` | `api_get_privilegios` |  |
| PUT | `/api/privilegios/<rol>` | `api_set_privilegios` |  |
| POST | `/api/privilegios/<rol>/restablecer` | `api_reset_privilegios` |  |
| POST | `/api/usuarios/crear` | `api_crear_usuario` |  |
| GET | `/api/usuarios` | `api_listar_usuarios` |  |
| DELETE | `/api/usuarios/<usuario_id>` | `api_desactivar_usuario` |  |
| POST | `/api/usuarios/<usuario_id>/reset-password` | `api_reset_password` |  |
| GET | `/api/licencias` | `api_listar_licencias` |  |
| POST | `/api/licencias/crear` | `api_crear_licencia` |  |
| DELETE | `/api/licencias/<licencia_id>` | `api_desactivar_licencia` |  |
| GET | `/api/licencias/verificar/<admin_id>` | `api_verificar_licencia` |  |
| GET | `/api/state` | `get_state` |  |
| POST | `/api/state` | `save_state` |  |
| POST | `/api/inventario/entrada` | `api_entrada_producto` |  |
| GET | `/api/inventario/general` | `api_inventario_general` |  |
| POST | `/api/inventario/importar-catalogo` | `api_importar_catalogo` | Importa catálogo → inventario_general. Nuevos: stock 0. Existentes: conserva stock. |
| POST | `/api/inventario/general/eliminar` | `api_eliminar_inventario_general` | Elimina producto del almacén cuando se borra del catálogo. |
| POST | `/api/catalogo/sync-desde-inventario` | `api_sync_desde_inventario` | Unifica inventario_general→productos y devuelve catálogo completo. |
| POST | `/api/sincronizar-completo` | `api_sincronizar_completo` |  |
| POST | `/api/stock/masivo` | `api_stock_masivo` | Carga stock a múltiples productos del almacén en una sola llamada. |
| POST | `/api/limpiar-tablas` | `api_limpiar_tablas` |  |
| POST | `/api/reconstruir-desde-productos` | `api_reconstruir_desde_productos` |  |
| GET | `/api/inventario/entradas` | `api_historial_entradas` |  |
| POST | `/api/inventario/asignar-diario` | `api_asignar_inventario` |  |
| GET | `/api/inventario/diario/<vendedor_id>` | `api_inventario_diario` |  |
| POST | `/api/inventario/diario/conteo` | `api_conteo_vendedor` |  |
| POST | `/api/inventario/diario/cierre` | `api_cierre_vendedor` |  |
| POST | `/api/inventario/cierre-admin` | `api_cierre_admin` |  |
| GET | `/api/catalogo` | `api_get_catalogo` | Devuelve el catálogo de productos para todos los roles. |
| POST | `/api/catalogo/sync` | `api_sync_catalogo` | El admin sincroniza su lista de productos al servidor (source of truth). |
| POST | `/api/inventario/diario/limpiar` | `api_limpiar_inventarios` |  |
| GET | `/api/inventario/diario/historial/<vendedor_id>` | `api_historial_cierres` | Lista los cierres de un vendedor ordenados por fecha descendente. |
| GET | `/api/gastos` | `api_listar_gastos` |  |
| POST | `/api/gastos` | `api_crear_gasto` |  |
| DELETE | `/api/gastos/<gasto_id>` | `api_eliminar_gasto` |  |
| GET | `/api/reportes/ventas` | `api_reporte_ventas` |  |
| GET | `/api/reportes/resumen` | `api_resumen` |  |
| GET | `/api/reportes/ganancias` | `api_ganancias` |  |
| GET | `/api/dev/metrics` | `api_dev_metrics_fallback` | Métricas de sistema: RAM, disco, BD. Fallback si diag_bp no carga. |
| GET | `/api/status` | `get_status` |  |
| GET | `/api/ping` | `api_ping` |  |
| GET | `/api/backup` | `export_backup` |  |
| GET | `/api/supabase/config` | `get_supabase_config` | Retorna config actual (la config se persiste en disco automaticamente). |
| POST | `/api/supabase/config` | `save_supabase_config` | Guarda config de Supabase y la persiste a disco (no hay que reescribir). |
| POST | `/api/supabase/sync-all` | `sync_all` |  |
| POST | `/api/supabase/test` | `test_supabase` |  |
| POST | `/api/supabase/push` | `push_supabase` |  |
| POST | `/api/supabase/pull` | `pull_supabase` |  |
| GET | `/api/sse` | `api_sse` | Stream de eventos en tiempo real para el cliente autenticado. |
| POST | `/api/auth/auto-backup` | `api_auto_backup` | Guarda backup automático al cerrar sesión + sync Supabase si disponible. |
| GET | `/api/descuentos` | `api_listar_descuentos` |  |
| POST | `/api/descuentos` | `api_crear_descuento` |  |
| DELETE | `/api/descuentos/<int:did>` | `api_eliminar_descuento` |  |
| POST | `/api/supabase/sync-full` | `api_supabase_sync_full` | Sincroniza ventas, inventario, productos y pedidos a Supabase. |
| GET | `/api/supabase/estado` | `api_supabase_estado` | Estado de tablas Supabase — usado por el debug panel. |
| POST | `/api/supabase/setup` | `api_supabase_setup` | Crea/verifica todas las tablas en Supabase dinámicamente. |
| GET | `/api/supabase/sql` | `api_supabase_sql` | Devuelve el SQL completo + SQL por tabla individual. |
| GET | `/api/historial/diario` | `api_historial_get` | Obtiene historial diario (SQLite local + Supabase si disponible). |
| POST | `/api/historial/diario` | `api_historial_post` | Guarda un snapshot diario en SQLite + Supabase. |
| GET | `/api/historial/diario/<fecha>` | `api_historial_detalle` | Detalle de un día específico del historial. |
| GET | `/api/debug/health` | `api_debug_health` | Health check completo del sistema para el debug panel. |
| GET | `/api/dev/metrics` | `api_dev_metrics` |  |
| GET | `/api/security/dashboard` | `api_security_dashboard` |  |

## dictionary/routes
<a name="dictionaryroutes"></a>
Archivo: `app/src/main/python/dictionary/routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/diccionario/sinonimos` | `api_sinonimos` |  |
| GET | `/api/diccionario/definicion` | `api_definicion` |  |
| GET | `/api/diccionario/definicion` | `api_definicion` |  |
| GET | `/api/diccionario/corregir` | `api_corregir` |  |
| GET | `/api/diccionario/corregir` | `api_corregir` |  |

## ia/proactive_routes
<a name="iaproactive-routes"></a>
Archivo: `app/src/main/python/ia/proactive_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/ia/alerts` | `get_alerts` | Obtener todas las alertas proactivas. |
| GET | `/api/ia/briefing` | `get_briefing` | Obtener briefing proactivo. |
| POST | `/api/ia/alerts/start` | `start_monitor` | Iniciar monitoreo en segundo plano. |

## ia_assistant_routes
<a name="ia-assistant-routes"></a>
Archivo: `app/src/main/python/ia_assistant_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/ping` | `ping` | Ping rapido para verificar que el modulo IA esta vivo. |
| POST | `/chat` | `chat` |  |
| POST | `/role` | `set_role` |  |
| GET | `/alerts` | `alerts` |  |
| GET | `/status` | `status` |  |

## loyalty_routes
<a name="loyalty-routes"></a>
Archivo: `app/src/main/python/loyalty_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/status` | `status` |  |
| POST | `/enroll` | `enroll` |  |
| GET | `/points` | `get_points` |  |
| POST | `/points/add` | `add_points` |  |
| POST | `/points/redeem` | `redeem` |  |
| GET | `/history` | `get_history` |  |
| POST | `/headless/order` | `headless_order` |  |
| GET | `/leaderboard` | `leaderboard` |  |

## admin_licencias
<a name="admin-licencias"></a>
Archivo: `app/src/main/python/modules/admin_licencias.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/licencias` | `api_listar_licencias` |  |
| POST | `/api/licencias/crear` | `api_crear_licencia` |  |
| DELETE | `/api/licencias/<licencia_id>` | `api_desactivar_licencia` |  |
| GET | `/api/licencias/verificar/<admin_id>` | `api_verificar_licencia` |  |

## admin_privilegios
<a name="admin-privilegios"></a>
Archivo: `app/src/main/python/modules/admin_privilegios.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/privilegios/<rol>` | `api_get_privilegios` |  |
| PUT | `/api/privilegios/<rol>` | `api_set_privilegios` |  |
| POST | `/api/privilegios/<rol>/restablecer` | `api_reset_privilegios` |  |

## admin_usuarios
<a name="admin-usuarios"></a>
Archivo: `app/src/main/python/modules/admin_usuarios.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/api/usuarios/crear` | `api_crear_usuario` |  |
| GET | `/api/usuarios` | `api_listar_usuarios` |  |
| DELETE | `/api/usuarios/<usuario_id>` | `api_desactivar_usuario` |  |
| POST | `/api/usuarios/<usuario_id>/reset-password` | `api_reset_password` |  |

## agent
<a name="agent"></a>
Archivo: `app/src/main/python/modules/agent.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/agent/query` | `agent_query` |  |
| GET | `/agent/suggestions` | `agent_suggestions` |  |

## agent_chat_bp
<a name="agent-chat-bp"></a>
Archivo: `app/src/main/python/modules/agent_chat_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/api/agent/chat` | `agent_chat` |  |
| GET | `/api/agent/status` | `agent_status` |  |
| GET | `/api/agent/identity` | `agent_identity` | El frontend llama esto al cargar la página para saber quién es el usuario. |

## ai_analytics
<a name="ai-analytics"></a>
Archivo: `app/src/main/python/modules/ai_analytics.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/analytics` | `analytics` | Endpoint combinado para compatibilidad. |
| GET | `/analytics/abc` | `analytics_abc` |  |
| GET | `/analytics/cross-selling` | `analytics_cross_selling` |  |
| GET | `/analytics/prices` | `analytics_prices` |  |
| GET | `/prices` | `prices` | Alias para compatibilidad. |
| GET | `/kpis` | `kpis` |  |

## ai_dashboard
<a name="ai-dashboard"></a>
Archivo: `app/src/main/python/modules/ai_dashboard.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/dashboard` | `general_dashboard` | Dashboard general llamado por ia_cargarTodo(). |
| GET | `/kpis` | `general_kpis` | KPIs generales llamado por ia_cargarKPIs(). |

## ai_fraud
<a name="ai-fraud"></a>
Archivo: `app/src/main/python/modules/ai_fraud.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/fraud` | `fraud` | Alias para compatibilidad. |
| GET | `/fraud/dashboard` | `fraud_dashboard` |  |

## ai_predictor
<a name="ai-predictor"></a>
Archivo: `app/src/main/python/modules/ai_predictor.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/predictor` | `predictor` | Alias para compatibilidad. |
| GET | `/predict/dashboard` | `predict_dashboard` |  |

## ai_shortcuts_bp
<a name="ai-shortcuts-bp"></a>
Archivo: `app/src/main/python/modules/ai_shortcuts_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/ai/shortcut/top-ventas-hoy` | `top_ventas_hoy` |  |
| GET | `/api/ai/shortcut/alerta-stock` | `alerta_stock` |  |
| GET | `/api/ai/shortcut/resumen-dia` | `resumen_dia` |  |
| POST | `/api/ai/shortcut/detect` | `detect` |  |

## assistant_chat
<a name="assistant-chat"></a>
Archivo: `app/src/main/python/modules/assistant_chat.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/ping` | `ping` |  |
| POST | `/public-chat` | `public_chat` |  |
| POST | `/chat` | `chat` |  |
| POST | `/role` | `set_role` |  |
| GET | `/alerts` | `alerts` |  |
| GET | `/status` | `status` |  |

## assistant_memory
<a name="assistant-memory"></a>
Archivo: `app/src/main/python/modules/assistant_memory.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/memory/recall` | `memory_recall` |  |
| POST | `/memory/search` | `memory_search` |  |
| POST | `/memory/save` | `memory_save` |  |
| POST | `/memory/forget` | `memory_forget` |  |
| GET | `/memory/summary` | `memory_summary` |  |

## auth
<a name="auth"></a>
Archivo: `app/src/main/python/modules/auth.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/auth/bio/registrar` | `api_bio_registrar` | Emite un token de dispositivo para login biométrico. |
| POST | `/auth/bio/login` | `api_bio_login` | Login canjeando un token de dispositivo (tras BiometricPrompt OK). |
| POST | `/auth/bio/revocar` | `api_bio_revocar` | Revoca los tokens biométricos del usuario actual (o uno por device). |
| POST | `/auth/login` | `api_login` | Login atomico con session_token unico. |
| POST | `/auth/logout` | `api_logout` |  |
| GET | `/auth/me` | `api_me` |  |
| POST | `/auth/cambiar-password` | `api_cambiar_password` |  |
| POST | `/usuarios/crear` | `api_crear_usuario` |  |
| GET | `/usuarios` | `api_listar_usuarios` |  |
| DELETE | `/usuarios/<usuario_id>` | `api_desactivar_usuario` |  |
| POST | `/usuarios/<usuario_id>/reset-password` | `api_reset_password` |  |
| GET | `/licencias` | `api_listar_licencias` |  |
| POST | `/licencias/crear` | `api_crear_licencia` |  |
| DELETE | `/licencias/<licencia_id>` | `api_desactivar_licencia` |  |
| GET | `/licencias/verificar/<admin_id>` | `api_verificar_licencia` |  |

## catalogo_bp
<a name="catalogo-bp"></a>
Archivo: `app/src/main/python/modules/catalogo_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/productos` | `api_listar_productos` |  |
| POST | `/productos/crear` | `api_crear_producto` |  |
| DELETE | `/productos/<producto_id>` | `api_eliminar_producto` |  |
| PUT | `/productos/<producto_id>` | `api_actualizar_producto` |  |
| GET | `/categorias` | `api_listar_categorias_admin` |  |
| POST | `/categorias/crear` | `api_crear_categoria` |  |
| GET | `/nomenclador` | `api_nomenclador` |  |
| POST | `/catalogo/sync` | `api_catalogo_sync` |  |

## clientes_bp
<a name="clientes-bp"></a>
Archivo: `app/src/main/python/modules/clientes_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/api/clientes/registrar` | `registrar_cliente` |  |
| GET | `/api/clientes` | `listar_clientes` |  |

## diag_bp
<a name="diag-bp"></a>
Archivo: `app/src/main/python/modules/diag_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/health` | `health` |  |
| GET | `/api/dev/metrics` | `dev_metrics` | Métricas de sistema (RAM, disco, BD) — solo roles elevados. |
| GET | `/api/diag/crashlog` | `diag_crashlog` | Devuelve el contenido de crash.log. |
| GET | `/api/diag/info` | `diag_info` | Info del entorno para diagnóstico. |
| POST | `/api/auth/auto-backup` | `auto_backup` | Backup automático periódico. |
| POST | `/api/db/backup` | `backup_bd` | Backup manual de la BD. |
| GET | `/api/seguridad/check` | `seguridad_check` | Verificación de seguridad del sistema. |
| GET | `/api/notificaciones` | `notificaciones` | Notificaciones inteligentes. |
| GET | `/api/qr/<producto_id>` | `generar_qr` | Genera datos para código QR de un producto. |
| POST | `/api/sincronizar-completo` | `sincronizar_completo` |  |
| GET | `/api/pedidos` | `api_pedidos` | Lista pedidos (tienda online). Filtra por estado si se pasa ?estado=. |
| GET | `/api/state` | `api_get_state` | Obtener estado persistido de la app. |
| POST | `/api/state` | `api_save_state` | Guardar estado de la app en BD. |

## docs_dev_bp
<a name="docs-dev-bp"></a>
Archivo: `app/src/main/python/modules/docs_dev_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/dev/docs` | `api_dev_docs` | Return live structure and SQLite-indexed docs without stale hardcoded counts. |

## i18n_bp
<a name="i18n-bp"></a>
Archivo: `app/src/main/python/modules/i18n_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/i18n/dict` | `get_dict` | Devuelve el diccionario completo ES/EN. |
| POST | `/api/i18n/reload` | `reload_dict` | Fuerza recarga del diccionario (útil tras editar el JSON). |

## inventory
<a name="inventory"></a>
Archivo: `app/src/main/python/modules/inventory.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/inventario/entrada` | `api_entrada_producto` |  |
| GET | `/inventario/general` | `api_inventario_general` |  |
| POST | `/inventario/importar-catalogo` | `api_importar_catalogo` |  |
| POST | `/inventario/general/eliminar` | `api_eliminar_inventario_general` |  |
| POST | `/catalogo/sync-desde-inventario` | `api_sync_desde_inventario` |  |
| POST | `/sincronizar-completo` | `api_sincronizar_completo` |  |
| POST | `/stock/masivo` | `api_stock_masivo` |  |
| POST | `/limpiar-tablas` | `api_limpiar_tablas` |  |
| POST | `/reconstruir-desde-productos` | `api_reconstruir_desde_productos` |  |
| GET | `/inventario/entradas` | `api_historial_entradas` |  |
| POST | `/inventario/asignar-diario` | `api_asignar_inventario` |  |
| GET | `/inventario/diario/<vendedor_id>` | `api_inventario_diario` |  |
| POST | `/inventario/diario/conteo` | `api_conteo_vendedor` |  |
| POST | `/inventario/diario/cierre` | `api_cierre_vendedor` |  |
| POST | `/inventario/cierre-admin` | `api_cierre_admin` |  |
| POST | `/inventario/diario/limpiar` | `api_limpiar_inventarios` |  |
| GET | `/inventario/diario/historial/<vendedor_id>` | `api_historial_cierres` |  |

## metrics
<a name="metrics"></a>
Archivo: `app/src/main/python/modules/metrics.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/dashboard/kpis` | `api_kpis_dashboard` |  |

## project_intelligence_bp
<a name="project-intelligence-bp"></a>
Archivo: `app/src/main/python/modules/project_intelligence_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/dev/project/summary` | `project_summary` |  |
| GET | `/api/dev/project/inventory` | `project_full_inventory` | Return the complete AST inventory without conversational truncation. |
| GET | `/api/dev/project/modules` | `project_modules` |  |
| GET | `/api/dev/project/structure` | `project_structure` |  |
| GET | `/api/dev/project/thesis` | `project_thesis` |  |

## publico_bp
<a name="publico-bp"></a>
Archivo: `app/src/main/python/modules/publico_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/publico/identity` | `api_publico_identity` | Devuelve identidad persistente del visitante anónimo o usuario actual. |
| GET | `/api/publico/catalogo` | `api_publico_catalogo` | Catálogo público de productos activos. |
| GET | `/api/publico/buscar` | `api_publico_buscar` | Busca productos por nombre/categoría. Ej: ?q=cafe. |
| GET | `/api/publico/ofertas` | `api_publico_ofertas` | Productos en oferta. |
| GET | `/api/publico/producto/<producto_id>` | `api_publico_producto_detalle` | Detalle de un producto + stock disponible. |
| GET | `/api/publico/categorias` | `api_publico_categorias` | Lista de categorías con conteo. |
| GET | `/api/publico/categoria/<nombre>` | `api_publico_categoria` | Productos de una categoría específica. |
| GET | `/api/publico/tiendas-info` | `api_publico_tiendas_info` | Info pública (al no haber tabla tiendas, devuelve info estática). |

## reportes_bp
<a name="reportes-bp"></a>
Archivo: `app/src/main/python/modules/reportes_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/reportes/ventas` | `reporte_ventas` | Reporte de ventas con filtros por fecha. |
| GET | `/api/reportes/exportar` | `exportar_csv` | Exporta ventas a CSV. |
| GET | `/api/reportes/resumen` | `reporte_resumen` | Resumen general para dashboard. |
| GET | `/api/reportes/ganancias` | `reporte_ganancias` | Ganancias/ingresos por día para roles staff. |
| GET | `/api/metrics` | `metrics` | Métricas rápidas para el dashboard. |

## settings_other
<a name="settings-other"></a>
Archivo: `app/src/main/python/modules/settings_other.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/sse` | `api_sse` |  |
| GET | `/api/biometric/check` | `api_biometric_check` |  |
| POST | `/api/biometric/setup` | `api_biometric_setup` |  |
| POST | `/api/payment/tokenize` | `api_payment_tokenize` |  |
| GET | `/api/branch/info` | `api_branch_info` |  |
| POST | `/api/branch/filter` | `api_branch_filter` |  |
| POST | `/api/ia/chat/secure` | `ia_chat_secure` |  |

## settings_supabase
<a name="settings-supabase"></a>
Archivo: `app/src/main/python/modules/settings_supabase.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/supabase/config` | `get_supabase_config` |  |
| POST | `/api/supabase/config` | `save_supabase_config` |  |
| POST | `/api/supabase/sync` | `sync_alias` |  |
| POST | `/api/supabase/sync-all` | `sync_all` |  |
| POST | `/api/supabase/test` | `test_supabase` |  |
| POST | `/api/supabase/push` | `push_supabase` |  |
| POST | `/api/supabase/pull` | `pull_supabase` |  |
| POST | `/api/supabase/sync-full` | `api_supabase_sync_full` |  |
| GET | `/api/supabase/estado` | `api_supabase_estado` |  |
| POST | `/api/supabase/setup` | `api_supabase_setup` |  |
| GET | `/api/supabase/sql` | `api_supabase_sql` |  |

## system
<a name="system"></a>
Archivo: `app/src/main/python/modules/system.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/status` | `api_status` | Endpoint público de status del servidor. |
| GET | `/backup/export` | `api_export_backup` | Exporta backup completo en JSON. |
| POST | `/backup/import` | `api_import_backup` | Importa backup desde JSON. |
| GET | `/historial/diario` | `api_historial_get` | Obtiene historial diario local. |
| POST | `/historial/diario` | `api_historial_post` | Guarda snapshot diario. |
| GET | `/logs` | `api_logs` | Obtiene logs recientes del sistema. |
| POST | `/logs/limpiar` | `api_limpiar_logs` | Limpia logs antiguos (>30 días). |
| GET | `/config` | `api_get_config` | Obtiene configuración del sistema. |
| POST | `/config` | `api_update_config` | Actualiza configuración del sistema. |

## telecom_bp
<a name="telecom-bp"></a>
Archivo: `app/src/main/python/modules/telecom_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/dev/telecom/latencia` | `api_latencia` |  |
| GET | `/api/dev/telecom/throughput` | `api_throughput` |  |
| GET | `/api/dev/telecom/dns` | `api_dns` |  |
| GET | `/api/dev/telecom/tls` | `api_tls` |  |
| GET | `/api/dev/telecom/red` | `api_red` |  |
| GET | `/api/dev/telecom/sqlite` | `api_sqlite` |  |
| GET | `/api/dev/telecom/full` | `api_full` |  |
| GET | `/api/dev/telecom/metodologia` | `api_metodologia` |  |

## tests_info_bp
<a name="tests-info-bp"></a>
Archivo: `app/src/main/python/modules/tests_info_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/tests/resultados` | `api_test_results` |  |
| GET | `/api/tests/cobertura` | `api_test_coverage` |  |
| GET | `/api/tests/resumen` | `api_test_summary` |  |

## tienda_bp
<a name="tienda-bp"></a>
Archivo: `app/src/main/python/modules/tienda_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/tiendas` | `api_tiendas` |  |
| POST | `/api/tiendas` | `api_crear_tienda` |  |
| DELETE | `/api/tiendas/<tienda_id>` | `api_eliminar_tienda` |  |

## tools_bp
<a name="tools-bp"></a>
Archivo: `app/src/main/python/modules/tools_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/tools/finanzas` | `tool_finanzas` | Balance financiero real desde BD. |
| GET | `/api/tools/stock` | `tool_stock` | Estado de inventario desde BD. |
| GET | `/api/tools/recomendar` | `tool_recomendar` | Recomendaciones IA basadas en datos. |
| GET | `/api/tools/prediccion` | `tool_prediccion` | Predicción de ventas basada en histórico. |
| GET | `/api/tools/abc` | `tool_abc` | Análisis ABC de productos basado en ventas reales. |
| GET | `/api/tools/admin/status` | `tool_admin_status` |  |
| GET | `/api/tools/analytic/resumen` | `tool_analytic_resumen` |  |
| POST | `/api/tools/auth/verify` | `tool_auth_verify` |  |
| GET | `/api/tools/general/info` | `tool_general_info` |  |
| GET | `/api/tools/ia/status` | `tool_ia_status` |  |
| POST | `/api/tools/importar/productos` | `tool_importar_productos` |  |
| GET | `/api/tools/inventario/resumen` | `tool_inventario_resumen` |  |
| GET | `/api/tools/lealtad/resumen` | `tool_lealtad_resumen` |  |
| GET | `/api/tools/licencia/info` | `tool_licencia_info` |  |
| GET | `/api/tools/seguridad/resumen` | `tool_seguridad_resumen` |  |
| GET | `/api/tools/setting/list` | `tool_setting_list` |  |
| GET | `/api/tools/tienda/resumen` | `tool_tienda_resumen` |  |
| GET | `/api/tools/validacion/check` | `tool_validacion_check` |  |
| POST | `/api/tools/venta/estadisticas` | `tool_venta_estadisticas` |  |

## usuarios_bp
<a name="usuarios-bp"></a>
Archivo: `app/src/main/python/modules/usuarios_bp.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/admin/privilegios` | `admin_privilegios` | Devuelve jerarquía + permisos + usuarios. |
| GET | `/api/usuarios` | `listar_usuarios` | Lista usuarios del sistema. |
| POST | `/api/admin/usuarios/crear` | `admin_crear_usuario` | Crear un nuevo usuario. |
| PUT, POST | `/api/admin/usuarios/<uid>/toggle` | `admin_toggle` | Activar/desactivar usuario. |
| DELETE | `/api/admin/usuarios/<uid>` | `admin_delete` | Eliminar usuario (soft delete). |

## ventas_atomic_v10
<a name="ventas-atomic-v10"></a>
Archivo: `app/src/main/python/modules/ventas_atomic_v10.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/api/ventas/registrar` | `registrar_venta` |  |
| GET | `/api/ventas/hoy` | `ventas_hoy` |  |
| POST | `/api/ventas/cierre` | `cierre_caja` |  |
| GET | `/api/ventas/cierres` | `listar_cierres` |  |
| GET | `/api/ventas/totales` | `totales_ventas` |  |

## ventas_descuentos
<a name="ventas-descuentos"></a>
Archivo: `app/src/main/python/modules/ventas_descuentos.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/descuentos` | `api_listar_descuentos` |  |
| POST | `/api/descuentos` | `api_crear_descuento` |  |
| DELETE | `/api/descuentos/<int:did>` | `api_eliminar_descuento` |  |

## ventas_gastos
<a name="ventas-gastos"></a>
Archivo: `app/src/main/python/modules/ventas_gastos.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/gastos` | `api_listar_gastos` |  |
| POST | `/api/gastos` | `api_crear_gasto` |  |
| DELETE | `/api/gastos/<gasto_id>` | `api_eliminar_gasto` |  |

## ventas_historial
<a name="ventas-historial"></a>
Archivo: `app/src/main/python/modules/ventas_historial.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/historial/diario` | `api_historial_get` |  |
| POST | `/api/historial/diario` | `api_historial_post` |  |
| GET | `/api/historial/diario/<fecha>` | `api_historial_detalle` |  |

## pwa_routes
<a name="pwa-routes"></a>
Archivo: `app/src/main/python/pwa_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/manifest.json` | `pwa_manifest` |  |
| GET | `/service-worker.js` | `pwa_service_worker` |  |
| GET | `/pwa-icon-<int:size>.png` | `pwa_icono` |  |

## rol_display
<a name="rol-display"></a>
Archivo: `app/src/main/python/rol_display.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/api/roles/nombres` | `obtener_nombres_roles` |  |

## security_routes
<a name="security-routes"></a>
Archivo: `app/src/main/python/security_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/pci/tokenize` | `pci_tokenize` |  |
| POST | `/pci/mask` | `pci_mask` |  |
| GET | `/pci/audit` | `pci_audit` |  |
| GET | `/het/status` | `het_status` |  |
| GET | `/het/alerts` | `het_alerts` |  |
| GET | `/omnichannel/status` | `omnichannel_status` |  |
| GET | `/ws/status` | `ws_status` |  |
| GET | `/dashboard` | `dashboard` |  |

## security_websocket
<a name="security-websocket"></a>
Archivo: `app/src/main/python/security_websocket.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/ws/events/<tid>` | `ws_events` |  |
| POST | `/ws/register` | `ws_register` |  |
| POST | `/ws/unregister` | `ws_unregister` |  |
| GET | `/ws/terminals` | `ws_list` |  |

## server
<a name="server"></a>
Archivo: `app/src/main/python/server.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/` | `index` |  |
| GET | `/activar_ia` | `activar_ia` |  |
| GET | `/estado_ia` | `estado_ia` |  |
| POST | `/chat` | `chat` |  |
| POST | `/chat_stream` | `chat_stream` |  |

## tienda_routes
<a name="tienda-routes"></a>
Archivo: `app/src/main/python/tienda_routes.py`

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| POST | `/api/clientes/registrar` | `api_registrar_cliente` |  |
| POST | `/api/clientes/login` | `api_login_cliente` |  |
| GET | `/api/clientes/<cliente_id>` | `api_perfil_cliente` | Perfil público del cliente (para la tienda). |
| PATCH | `/api/clientes/<cliente_id>` | `api_actualizar_cliente` | El cliente actualiza su perfil (nombre, teléfono, imagen). |
| GET | `/api/clientes` | `api_listar_clientes` |  |
| GET | `/api/productos` | `api_listar_productos` |  |
| GET | `/api/productos/<producto_id>` | `api_producto_detalle` |  |
| POST | `/api/productos/<producto_id>/imagen` | `api_subir_imagen_producto` |  |
| POST | `/api/productos/qr` | `api_generar_qr_productos` |  |
| GET | `/api/tiendas` | `api_listar_tiendas` |  |
| POST | `/api/tiendas` | `api_crear_tienda` |  |
| DELETE | `/api/tiendas/<tienda_id>` | `api_eliminar_tienda` |  |
| PATCH | `/api/tiendas/<tienda_id>` | `api_actualizar_tienda` | Admin actualiza nombre e imagen de su tienda. |
| POST | `/api/pedidos` | `api_crear_pedido` |  |
| GET | `/api/pedidos` | `api_listar_pedidos` |  |
| GET | `/api/pedidos/<pedido_id>` | `api_obtener_pedido` |  |
| PATCH | `/api/pedidos/<pedido_id>/estado` | `api_actualizar_estado_pedido` |  |
| GET | `/api/pedidos/resumen` | `api_resumen_pedidos` |  |
