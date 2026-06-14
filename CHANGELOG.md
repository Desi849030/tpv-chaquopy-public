# Changelog — TPV UltraSmart

## v8.0.0 (9 Jun 2026) — Refactorización Profesional

### 🏗️ Arquitectura
- **app.py**: 1752 → 274 líneas (reducción 84%)
- 72 rutas embebidas extraídas a **9 blueprints** modulares
- Decoradores unificados en `decorators.py` (eliminados 80+ duplicados en 19 módulos)
- Eliminados paquetes vacíos (`services/`, `utils/`)
- `database.py` marcado como facade deprecado (38 archivos aún lo importan)

### 🗄️ Base de Datos
- Tabla `clientes` añadida al schema (faltaba, causaba error)
- Rol `cajero` en CHECK constraint de `usuarios`
- `venta_id` ya no es UNIQUE en `historial_ventas` (permite múltiples items)
- Columnas `efectivo`/`tarjeta`/`transferencia` en `cierres_caja`
- 15 queries sueltas (TBL_17..31) eliminadas del schema

### 🧠 Agente IA
- NLP: 7 → **25 intenciones** reconocidas
- `humanizer.enhance()` implementado (antes no existía, crash silencioso)
- `agent_pro.py`: 13 datos falsos hardcoded reemplazados por consultas BD real
- `agent_master.py`: 3 fallbacks hardcoded eliminados
- Keyword fallback ampliado de 7 → 24 intenciones con prioridad
- Soporte completo para rol `cajero` (personalidad Iris)

### 🔐 Seguridad
- Eliminado auto-login bypass de desarrollador en `/api/auth/me`
- Eliminado catch-all `/api/<path:p>` que silenciaba errores 404
- Secret key lee de variable de entorno `TPV_SECRET_KEY`
- SQL injection corregido en `modules/agent.py`
- Decoradores en orden correcto (`@route` antes de `@login_required`)

### 🎨 Frontend
- Panel de privilegios: botones → tarjetas táctiles grandes con iconos
- Rol Cajero añadido a selector de privilegios
- Módulo Biometría añadido a privilegios (bi-fingerprint)
- Tabla de módulos responsive (columna oculta en móvil)
- `chart.umd.min.js`: eliminada carga duplicada
- `tpv_modals.css`: añadido (existía pero no se cargaba)
- `devmetrics_cargar()` movido de inline a `tpv_dev_metrics.js`
- Iconos con colores individuales por módulo

### 📋 CI/CD
- Workflow unificado en `ci.yml` (test → build APK)
- Workflows obsoletos eliminados (`android-build.yml`, `build-apk.yml`, `main.yml`)

---

## v2.5.5 (16 May 2026)

### Added
- Agente IA Proactivo v1.0 (alertas automáticas, briefing, monitoreo background)
- Test de seguridad avanzada (31/31): SQLi, XSS, Rate Limiting, Headers
- Simulación maestra de negocio (38 pruebas)
- Stress test concurrente multi-usuario (7 pruebas)
- Auditoría completa del proyecto (52 pruebas)
- sanitize_input mejorado con HTML/SQL escaping
- Headers de seguridad HTTP (X-Content-Type, X-Frame, X-XSS, HSTS)
- BD optimizada: WAL + busy_timeout + isolation_level

### Fixed
- Login bloqueado (hash de contraseña regenerado)
- Error "no such column: costoUnitario" en catálogo IA
- Métricas del sistema (RAM, disco, inventario)
- Database is locked en operaciones concurrentes
