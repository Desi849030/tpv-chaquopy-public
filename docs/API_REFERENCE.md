# 📡 Referencia de API — TPV Ultra Smart v8.0

> **Documento autogenerado** a partir del código fuente.  
> Total de endpoints: **210** en **37** módulos.  
> Generado: 2026-06-12

> ⚠️ Las rutas se extraen de los decoradores `@bp.route(...)`. Los permisos por
> rol dependen de `@login_required` / `@requiere_rol` de cada función.

## Índice de módulos

- [`app.py`](#app) — 5 endpoints
- [`dictionary/routes.py`](#dictionaryroutes) — 5 endpoints
- [`ia/proactive_routes.py`](#iaproactive-routes) — 3 endpoints
- [`modules/admin_licencias.py`](#admin-licencias) — 4 endpoints
- [`modules/admin_privilegios.py`](#admin-privilegios) — 3 endpoints
- [`modules/admin_usuarios.py`](#admin-usuarios) — 4 endpoints
- [`modules/agent.py`](#agent) — 2 endpoints
- [`modules/agent_chat_bp.py`](#agent-chat-bp) — 2 endpoints
- [`modules/ai_analytics.py`](#ai-analytics) — 6 endpoints
- [`modules/ai_dashboard.py`](#ai-dashboard) — 2 endpoints
- [`modules/ai_fraud.py`](#ai-fraud) — 2 endpoints
- [`modules/ai_predictor.py`](#ai-predictor) — 2 endpoints
- [`modules/assistant_chat.py`](#assistant-chat) — 6 endpoints
- [`modules/assistant_memory.py`](#assistant-memory) — 5 endpoints
- [`modules/auth.py`](#auth) — 12 endpoints
- [`modules/catalogo_bp.py`](#catalogo-bp) — 10 endpoints
- [`modules/clientes_bp.py`](#clientes-bp) — 2 endpoints
- [`modules/diag_bp.py`](#diag-bp) — 13 endpoints
- [`modules/import_bp.py`](#import-bp) — 2 endpoints
- [`modules/inventory.py`](#inventory) — 17 endpoints
- [`modules/metrics.py`](#metrics) — 1 endpoints
- [`modules/reportes_bp.py`](#reportes-bp) — 4 endpoints
- [`modules/sales.py`](#sales) — 7 endpoints
- [`modules/settings_other.py`](#settings-other) — 7 endpoints
- [`modules/settings_supabase.py`](#settings-supabase) — 11 endpoints
- [`modules/system.py`](#system) — 9 endpoints
- [`modules/tienda_bp.py`](#tienda-bp) — 2 endpoints
- [`modules/tools_bp.py`](#tools-bp) — 19 endpoints
- [`modules/usuarios_bp.py`](#usuarios-bp) — 5 endpoints
- [`modules/ventas.py`](#ventas) — 8 endpoints
- [`modules/ventas_core_bp.py`](#ventas-core-bp) — 5 endpoints
- [`modules/ventas_descuentos.py`](#ventas-descuentos) — 3 endpoints
- [`modules/ventas_gastos.py`](#ventas-gastos) — 3 endpoints
- [`modules/ventas_historial.py`](#ventas-historial) — 3 endpoints
- [`modules/ventas_reportes.py`](#ventas-reportes) — 4 endpoints
- [`security_routes.py`](#security-routes) — 8 endpoints
- [`security_websocket.py`](#security-websocket) — 4 endpoints

---

## app
<a name="app"></a>
Archivo: `app/src/main/python/app.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/` | `index` |  |
| GET | `/static/<path:f>` | `static_serve` |  |
| POST | `/api/auth/login` | `login` |  |
| POST | `/api/auth/logout` | `logout` |  |
| GET | `/api/auth/me` | `auth_me` |  |

## dictionary/routes
<a name="dictionaryroutes"></a>
Archivo: `app/src/main/python/dictionary/routes.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/diccionario/sinonimos` | `api_sinonimos` |  |
| GET | `/api/diccionario/definicion` | `api_definicion` |  |
| GET | `/api/diccionario/definicion` | `api_definicion` |  |
| GET | `/api/diccionario/corregir` | `api_corregir` |  |
| GET | `/api/diccionario/corregir` | `api_corregir` |  |

## ia/proactive_routes
<a name="iaproactive-routes"></a>
Archivo: `app/src/main/python/ia/proactive_routes.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/ia/alerts` | `get_alerts` | Obtener todas las alertas proactivas. |
| GET | `/api/ia/briefing` | `get_briefing` | Obtener briefing proactivo. |
| POST | `/api/ia/alerts/start` | `start_monitor` | Iniciar monitoreo en segundo plano. |

## admin_licencias
<a name="admin-licencias"></a>
Archivo: `app/src/main/python/modules/admin_licencias.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/licencias` | `api_listar_licencias` |  |
| POST | `/api/licencias/crear` | `api_crear_licencia` |  |
| DELETE | `/api/licencias/<licencia_id>` | `api_desactivar_licencia` |  |
| GET | `/api/licencias/verificar/<admin_id>` | `api_verificar_licencia` |  |

## admin_privilegios
<a name="admin-privilegios"></a>
Archivo: `app/src/main/python/modules/admin_privilegios.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/privilegios/<rol>` | `api_get_privilegios` |  |
| PUT | `/api/privilegios/<rol>` | `api_set_privilegios` |  |
| POST | `/api/privilegios/<rol>/restablecer` | `api_reset_privilegios` |  |

## admin_usuarios
<a name="admin-usuarios"></a>
Archivo: `app/src/main/python/modules/admin_usuarios.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/api/usuarios/crear` | `api_crear_usuario` |  |
| GET | `/api/usuarios` | `api_listar_usuarios` |  |
| DELETE | `/api/usuarios/<usuario_id>` | `api_desactivar_usuario` |  |
| POST | `/api/usuarios/<usuario_id>/reset-password` | `api_reset_password` |  |

## agent
<a name="agent"></a>
Archivo: `app/src/main/python/modules/agent.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/agent/query` | `agent_query` |  |
| GET | `/agent/suggestions` | `agent_suggestions` |  |

## agent_chat_bp
<a name="agent-chat-bp"></a>
Archivo: `app/src/main/python/modules/agent_chat_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/api/agent/chat` | `agent_chat` | Chat con el agente IA. |
| GET | `/api/agent/status` | `agent_status` | Estado del agente IA. |

## ai_analytics
<a name="ai-analytics"></a>
Archivo: `app/src/main/python/modules/ai_analytics.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| GET | `/dashboard` | `general_dashboard` | Dashboard general llamado por ia_cargarTodo(). |
| GET | `/kpis` | `general_kpis` | KPIs generales llamado por ia_cargarKPIs(). |

## ai_fraud
<a name="ai-fraud"></a>
Archivo: `app/src/main/python/modules/ai_fraud.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/fraud` | `fraud` | Alias para compatibilidad. |
| GET | `/fraud/dashboard` | `fraud_dashboard` |  |

## ai_predictor
<a name="ai-predictor"></a>
Archivo: `app/src/main/python/modules/ai_predictor.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/predictor` | `predictor` | Alias para compatibilidad. |
| GET | `/predict/dashboard` | `predict_dashboard` |  |

## assistant_chat
<a name="assistant-chat"></a>
Archivo: `app/src/main/python/modules/assistant_chat.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| POST | `/memory/recall` | `memory_recall` |  |
| POST | `/memory/search` | `memory_search` |  |
| POST | `/memory/save` | `memory_save` |  |
| POST | `/memory/forget` | `memory_forget` |  |
| GET | `/memory/summary` | `memory_summary` |  |

## auth
<a name="auth"></a>
Archivo: `app/src/main/python/modules/auth.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/auth/login` | `api_login` |  |
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
|--------|------|---------|-------------|
| GET | `/api/catalogo` | `catalogo` | Lista el catálogo de productos activos desde la BD. |
| POST | `/api/catalogo/crear` | `catalogo_crear` | Crear un producto desde el catálogo. |
| PUT | `/api/catalogo/actualizar/<producto_id>` | `catalogo_actualizar` | Actualizar nombre/precio/foto de un producto. |
| DELETE | `/api/catalogo/eliminar/<producto_id>` | `catalogo_eliminar` | Soft-delete de un producto. |
| POST | `/api/catalogo/sync` | `catalogo_sync` | Sincroniza catálogo completo (guardar fotos sin resetear stock). |
| POST | `/api/productos/precio` | `actualizar_precio_producto` | Actualiza precio de venta y/o costo de un producto. |
| POST | `/api/productos` | `crear_producto` | Crear un nuevo producto (vía CRUD genérico). |
| PUT | `/api/productos/<producto_id>` | `actualizar_producto` | Actualizar un producto existente. |
| DELETE | `/api/productos/<producto_id>` | `eliminar_producto` | Soft-delete de producto. |
| POST | `/api/reconstruir-desde-productos` | `reconstruir_desde_productos` | Reconstruye inventario desde lista de productos del frontend. |

## clientes_bp
<a name="clientes-bp"></a>
Archivo: `app/src/main/python/modules/clientes_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/api/clientes/registrar` | `registrar_cliente` |  |
| GET | `/api/clientes` | `listar_clientes` |  |

## diag_bp
<a name="diag-bp"></a>
Archivo: `app/src/main/python/modules/diag_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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

## import_bp
<a name="import-bp"></a>
Archivo: `app/src/main/python/modules/import_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/api/importar/excel` | `importar_excel` | Importa productos desde JSON (simula carga de Excel). |
| POST | `/api/importar/previsualizar` | `previsualizar` | Previsualiza datos antes de importar. |

## inventory
<a name="inventory"></a>
Archivo: `app/src/main/python/modules/inventory.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| GET | `/dashboard/kpis` | `api_kpis_dashboard` |  |

## reportes_bp
<a name="reportes-bp"></a>
Archivo: `app/src/main/python/modules/reportes_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/reportes/ventas` | `reporte_ventas` | Reporte de ventas con filtros por fecha. |
| GET | `/api/reportes/exportar` | `exportar_csv` | Exporta ventas a CSV. |
| GET | `/api/reportes/resumen` | `reporte_resumen` | Resumen general para dashboard. |
| GET | `/api/metrics` | `metrics` | Métricas rápidas para el dashboard. |

## sales
<a name="sales"></a>
Archivo: `app/src/main/python/modules/sales.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/gastos` | `api_listar_gastos` |  |
| POST | `/gastos` | `api_crear_gasto` |  |
| DELETE | `/gastos/<gasto_id>` | `api_eliminar_gasto` |  |
| GET | `/reportes/ventas` | `api_reporte_ventas` |  |
| GET | `/reportes/resumen` | `api_resumen` |  |
| GET | `/reportes/ganancias` | `api_ganancias` |  |
| GET | `/descuentos` | `api_listar_descuentos` |  |

## settings_other
<a name="settings-other"></a>
Archivo: `app/src/main/python/modules/settings_other.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| GET | `/status` | `api_status` | Endpoint público de status del servidor. |
| GET | `/backup/export` | `api_export_backup` | Exporta backup completo en JSON. |
| POST | `/backup/import` | `api_import_backup` | Importa backup desde JSON. |
| GET | `/historial/diario` | `api_historial_get` | Obtiene historial diario local. |
| POST | `/historial/diario` | `api_historial_post` | Guarda snapshot diario. |
| GET | `/logs` | `api_logs` | Obtiene logs recientes del sistema. |
| POST | `/logs/limpiar` | `api_limpiar_logs` | Limpia logs antiguos (>30 días). |
| GET | `/config` | `api_get_config` | Obtiene configuración del sistema. |
| POST | `/config` | `api_update_config` | Actualiza configuración del sistema. |

## tienda_bp
<a name="tienda-bp"></a>
Archivo: `app/src/main/python/modules/tienda_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/tiendas` | `api_tiendas` | Lista tiendas configuradas. |
| POST | `/api/tiendas` | `api_crear_tienda` | Crear/actualizar tienda. |

## tools_bp
<a name="tools-bp"></a>
Archivo: `app/src/main/python/modules/tools_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| GET | `/api/admin/privilegios` | `admin_privilegios` | Devuelve jerarquía + permisos + usuarios. |
| GET | `/api/usuarios` | `listar_usuarios` | Lista usuarios del sistema. |
| POST | `/api/admin/usuarios/crear` | `admin_crear_usuario` | Crear un nuevo usuario. |
| PUT, POST | `/api/admin/usuarios/<uid>/toggle` | `admin_toggle` | Activar/desactivar usuario. |
| DELETE | `/api/admin/usuarios/<uid>` | `admin_delete` | Eliminar usuario (soft delete). |

## ventas
<a name="ventas"></a>
Archivo: `app/src/main/python/modules/ventas.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/gastos` | `api_gastos` |  |
| POST | `/gastos` | `api_crear_gasto` |  |
| DELETE | `/gastos/<gasto_id>` | `api_eliminar_gasto` |  |
| GET | `/cierres` | `api_cierres` |  |
| POST | `/cierres/cerrar-dia` | `api_cerrar_dia` | Cierra el día actual para el vendedor o admin. |
| GET | `/reportes/ventas` | `api_reporte_ventas` |  |
| GET | `/reportes/resumen` | `api_resumen_ventas` |  |
| GET | `/reportes/ganancias` | `api_ganancias` |  |

## ventas_core_bp
<a name="ventas-core-bp"></a>
Archivo: `app/src/main/python/modules/ventas_core_bp.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| POST | `/api/ventas/registrar` | `registrar_venta` | Registra una venta en la BD. |
| GET | `/api/ventas/hoy` | `ventas_hoy` | Ventas del día actual. |
| POST | `/api/ventas/cierre` | `cierre_caja` | Cierre de caja del día. |
| GET | `/api/ventas/cierres` | `listar_cierres` | Lista cierres de caja. |
| GET | `/api/ventas/totales` | `totales_ventas` | Resumen de totales hoy/mes. |

## ventas_descuentos
<a name="ventas-descuentos"></a>
Archivo: `app/src/main/python/modules/ventas_descuentos.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/descuentos` | `api_listar_descuentos` |  |
| POST | `/api/descuentos` | `api_crear_descuento` |  |
| DELETE | `/api/descuentos/<int:did>` | `api_eliminar_descuento` |  |

## ventas_gastos
<a name="ventas-gastos"></a>
Archivo: `app/src/main/python/modules/ventas_gastos.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/gastos` | `api_listar_gastos` |  |
| POST | `/api/gastos` | `api_crear_gasto` |  |
| DELETE | `/api/gastos/<gasto_id>` | `api_eliminar_gasto` |  |

## ventas_historial
<a name="ventas-historial"></a>
Archivo: `app/src/main/python/modules/ventas_historial.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/historial/diario` | `api_historial_get` |  |
| POST | `/api/historial/diario` | `api_historial_post` |  |
| GET | `/api/historial/diario/<fecha>` | `api_historial_detalle` |  |

## ventas_reportes
<a name="ventas-reportes"></a>
Archivo: `app/src/main/python/modules/ventas_reportes.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/api/reportes/ventas` | `api_reporte_ventas` |  |
| GET | `/api/reportes/resumen` | `api_resumen` |  |
| GET | `/api/reportes/ganancias` | `api_ganancias` |  |
| GET | `/api/dashboard/data` | `api_dashboard_data` |  |

## security_routes
<a name="security-routes"></a>
Archivo: `app/src/main/python/security_routes.py`

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
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
|--------|------|---------|-------------|
| GET | `/ws/events/<tid>` | `ws_events` |  |
| POST | `/ws/register` | `ws_register` |  |
| POST | `/ws/unregister` | `ws_unregister` |  |
| GET | `/ws/terminals` | `ws_list` |  |
