# CHANGELOG — TPV Ultra Smart

## [Unreleased]

### Correcciones de base de datos
- Fix de backtick en database.py L138 que causaba 56 strings desplazados
- Reemplazo de 1971 caracteres non-ASCII (em dash, flechas, box drawing, acentos)
- CHECK de roles con 6 roles: desarrollador, administrador, supervisor, vendedor, cajero, cliente
- 4 Foreign Keys a usuarios(usuario_id) en historial_ventas, inventario_diario, cierres_diario, auditoria
- PRAGMA foreign_keys = ON, journal_mode = WAL, synchronous = NORMAL

### Tests de concurrencia (5 tests en tests/unit/test_concurrency_security.py)
1. test_concurrent_sale: 2 threads, 1 exito + 1 fallo limpio con BEGIN IMMEDIATE
2. test_rollback: no registros huerfanos tras rollback
3. test_six_roles: 6 roles aceptados por CHECK constraint
4. test_5_thread_serialization: 5 threads, 3 exitos + 2 fallos limpios
5. test_fk_constraint: FK bloquea insercion con producto_id inexistente

### Fixes de compatibilidad de tests
- test_concurrency_security: TPV_FILES_DIR usa tempfile.mkdtemp() con save/restore
- test_security_and_edge_ai: seed fraud test limpia historial_ventas de hoy

### Metricas finales
- 620 tests pasan, 71 omitidos, 61% cobertura
- 17 tablas, 4 FKs, 6 roles


## [v8.9] — 2026-06-15

### 🎨 UI/UX
- **Submenús reorganizados por categorías** con headers visuales claros:
  - **Operación**: 🛒 Punto de Venta + 🏬 Tienda Online
  - **Catálogo**: 📋 Gestión de Productos + 📊 Stock e Inventario
  - **Ventas**: 💵 Operativa del Día + 📈 Histórico y Reportes
  - **Herramientas**: 💾 Datos + 🎨 Preferencias + 👔 Administración + 💻 Desarrollador
- Iconos consistentes en todos los items
- Hover con gradiente azul-índigo y transformación sutil
- Headers con borde lateral de color
- Bordes redondeados y sombras refinadas

### 🤖 Chat Gestor Universal
- El chat funciona **SIN login** (cliente anónimo) como gestor de tienda
- Responde con **DATOS REALES de la BD**:
  - Buscar productos por nombre (insensible a tildes: `cafe` = `café`)
  - Consultar precios
  - Ver ofertas activas
  - Listar categorías y productos por categoría
  - Consultar stock disponible
  - Información de horarios y tienda
- **Cambio de rol atómico** al hacer login/logout
- Burbuja arrastrable mejorada con **snap a bordes**
- Saludo neutro y contextual por rol

### 📡 Diagnóstico Telecom REAL (rol desarrollador)
- Módulo `modules/telecom_diag.py` con herramientas REALES de red:
  - Latencia HTTP a Supabase con jitter
  - Throughput de descarga real
  - DNS lookup con tiempo
  - TLS handshake (versión, cipher, certificado)
  - IP local, hostname, plataforma
  - Velocidad SQLite (IOPS)
- API REST `/api/dev/telecom/*` (solo desarrollador)
- Acceso directo desde menú **Herramientas → Desarrollador → Diagnóstico Telecom**
- Soporta tanto JWT clásicas como publishable keys de Supabase

### 🔐 Sesión Atómica por Usuario
- `decorators.py`: verificación atómica en cada request (sin caché 5min)
- `modules/auth.py`: `session.clear()` + `session_token` único al login
- `app_6.js`: limpieza completa de estado previo en login/logout
- `tpv_chat.js`: reset atómico al cambiar usuario, historial namespaced por user_id

### 🌐 Endpoints Públicos (Gestor Anónimo)
- `GET /api/publico/catalogo` — Catálogo público
- `GET /api/publico/buscar?q=cafe` — Búsqueda flexible
- `GET /api/publico/ofertas` — Productos en oferta
- `GET /api/publico/producto/<id>` — Detalle + stock
- `GET /api/publico/categorias` — Lista de categorías
- `GET /api/publico/categoria/<nombre>` — Productos de una categoría
- `GET /api/publico/tiendas-info` — Info pública

### 🐛 Bug Fixes
- `settings_other.py`: `import json` faltante
- `tpv_chat.js`: saludo neutro (sin "Root Access concedido")
- Adaptación queries a esquema real (columnas `producto_id`, `unidad_medida`, `en_oferta`)
- Búsqueda flexible insensible a tildes y mayúsculas

### 📚 Documentación
- `docs/telecom_diagnostico.md`: documentación completa del módulo telecom
- `README.md`: sección Telecom + sección Chat Universal
- `CHANGELOG.md`: este archivo

### 🧪 Tests
- `tests/test_telecom_diag.py`: 7 tests del módulo telecom (todos pasan)
- `tests/test_publico_bp.py`: tests de endpoints públicos
- `tests/test_handlers_cliente.py`: tests del gestor universal


## [v8.0] — 2026-06-14

- Refactorización general a arquitectura modular con Blueprints
- 209 rutas registradas
- Sistema de roles: cliente, vendedor, cajero, supervisor, administrador, desarrollador
- Agente IA con handlers por rol
- Sincronización bidireccional con Supabase
- PWA con Service Worker
- Soporte multiidioma (i18n)
