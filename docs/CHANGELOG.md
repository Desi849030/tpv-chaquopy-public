# Registro de Cambios

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
