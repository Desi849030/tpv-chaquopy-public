# Registro de Cambios


## v2.4.1 (Mayo 2026)

### Correcciones criticas (batch 1-3)
- **IA Agent**: Burbuja no aparecia — ia_assistant_ui.js era 1 linea (stub), reemplazado por core + render + network
- **Blueprint duplicados**: inventory_bp, settings_bp, tienda_bp, loyalty_bp consolidados en helpers como fuente unica
- **Excel imports**: Route /api/reconstruir-desde-productos funciona via inventory_helpers
- **MainActivity.java**: splashRoot tipo FrameLayout + import android.view.View
- **Login APK**: INSERT OR IGNORE + .dev_initialized para usuario desarrollador
- **SSE polling**: imports _sse_clientes agregados en settings_other.py
- **schema.py**: 15 queries DML eliminadas de ALL_TABLES
- **Debug endpoint**: /api/debug/test-login eliminado de auth_routes.py
- 15 fixes adicionales: _TPV_PORT, import uuid, _dev_only 403, permisos vendedor, SSE addEventListener, .catch() fallback, _admin_invVista restaurada

### Limpieza
- Archivos eliminados: config.py.deprecated, inject_rol_fix.py, ia_assistant.py, 4x *.bak_v240 (-1358 lineas)
- .gitignore: secrets runtime, backup files, *_v240*
- 142/142 tests pytest pasando
## v1.0.0 (Mayo 2026)

### Refactorizacion completa del frontend
- Modularizacion de script_5.js (5,109 lineas) en 9 modulos
- Modularizacion de script_8.js (3,022 lineas) en 8 modulos
- Renombrado de script_N.js a tpv_* descriptivos
- 27 modulos JS validados con node --check
- Renombrado de 8 CSS a convencion tpv_*.css
- Eliminacion de 17 archivos huerfanos y temporales

### Template Split
- index.html dividido en 7 partials Jinja2
- app.py actualizado a render_template()
- Template reducido de 1423 a 19 lineas

### Correcciones
- Fix permisos importacion catalogo (vendedor incluido)
- Eliminacion de burbuja dark mode (obstruia UI)
- Eliminacion de indicador offline flotante
- Restauracion de index.html completo

### Limpieza
- Eliminacion CSS duplicados
- Eliminacion backups residuales
- Limpieza raiz del repositorio

## v6.8 (Mayo 2026)

### IA Assistant
- Motor NLP con clasificacion de intents
- Guardrails anti-abuso
- Memoria contextual
- Anti-slop para respuestas de calidad

### Seguridad
- Decoradores de rol en todos los endpoints
- Autenticacion biometrica nativa
- PCI compliance para pagos

## v6.0-v6.5 (Abril-Mayo 2026)

- Dashboard KPIs animados
- Licencias con dias de prueba
- Tienda online
- Cola sincronizacion offline
- Service Worker PWA
- Traduccion ES/EN
- Panel debug inteligente

## v5.0 (Marzo 2026)

- Arquitectura Chaquopy + Flask + WebView
- Roles multinivel
- Inventario diario
- Import/export Excel
- QR etiquetas
