# CHANGELOG — TPV Ultra Smart

## [Unreleased]

### Calidad y compatibilidad
- Gate de cobertura real >= 50% en CI.
- Suite soportada con más de 500 pruebas aisladas.
- Compatibilidad de dependencias para Chaquopy Python 3.10 y Termux Python 3.14.
- Resolución de SQLite mediante `TPV_FILES_DIR` en servicios IA y licencias.

### Documentación y repositorio
- README reorganizado con estado verificable, arquitectura, roles y comandos actuales.
- Guía formal del rol Desarrollador con acceso funcional `all`.
- Documentación curada sincronizada a SQLite para lectura offline por la IA.
- Índice de documentación, política de seguridad y plantillas de colaboración.
- Workflow actualizado a acciones mantenidas y jobs con permisos mínimos.
- Indexación recursiva de toda la documentación del repositorio para la IA.
- Eliminación de claves versionadas, backups, parches de una sola ejecución y tests obsoletos.
- Frontend de navegador resuelto directamente desde `app/src/main/assets/frontend`.
- Host y puerto configurables mediante `TPV_HOST` y `TPV_PORT`.
- Secretos runtime movidos a `TPV_FILES_DIR`, compatible con el filesystem de Android.
- Versión pública unificada en `6.13.1` para Python, Gradle, health y documentación.
- Arranque de navegador verificado con frontend real y puerto configurable.
- Conexiones SQLite pendientes corregidas; suite validada con `ResourceWarning` como error.
- Dependencia explícita entre `syncOfflineDocumentation` y `merge<Variant>PythonSources` para Gradle 8.
- Python 3.10 configurado en el job Android para compilar bytecode Chaquopy compatible.


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
