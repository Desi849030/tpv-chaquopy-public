# TPV UltraSmart v2.5.5

Sistema de Punto de Venta Profesional con IA integrada, biometria, roles multinivel y sincronizacion offline. Compilado 100% desde Android con Termux + Chaquopy.

## Caracteristicas Principales

- Autenticacion multinivel: Desarrollador, Administrador, Supervisor, Vendedor + biometria nativa
- Punto de venta: Catalogo, carrito, escaner QR, pagos, descuentos, tickets
- Inventario: Stock diario, alertas bajo stock, cierres de caja, comisiones
- Gestion de productos: CRUD completo, categorias, import/export Excel inteligente
- IA Asistente: Motor NLP con 13 herramientas + 5 skills + 150 endpoints, intents, guardrails, memoria contextual
- Diccionario comercial: Sinonimos, definiciones, correccion ortografica offline
- Panel dev metrics: RAM, disco, formulas inventario, KPIs en tiempo real
- Importacion Excel: Levenshtein fuzzy matching, 4 estrategias, validacion UTF-8
- Tienda online: Clientes, pedidos, notificaciones, cola offline
- Offline-first: WiFi local, IndexedDB + SQLite dual
- Seguridad (9.5/10): SQLi, XSS, scrypt, JWT, RBAC, Rate Limiting, Headers, Auditoría
- Licencias: Activacion con dias de prueba
- Dashboard: KPIs animados, graficos Chart.js
- Traduccion: Google Translate ES/EN
- Supabase: Sincronizacion cloud opcional

## Estadisticas

- 142 tests unitarios + 38 simulación maestra + 7 stress test + 47 auditoría = 679+ pruebas totales
- Backend modular: 195 archivos Python, 33,718 líneas totales, 347 archivos + Agente Proactivo con monitoreo background
- Frontend: 62 modulos JavaScript
- IA Agentiva + Proactiva: 13 herramientas, 5 skills, 17 categorías, alertas automáticas, briefing

## Jerarquia de Roles

| Rol | Permisos |
|-----|----------|
| Desarrollador | Todo sin limites + licencias + debug + dev metrics |
| Administrador | Tienda completa (NO licencias) |
| Supervisor | Solo lectura/reportes |
| Vendedor | Solo vender + IA basica |

## Arquitectura Modular

Backend organizado en packages con facades backward-compatible:

- models/ - TypedDicts por dominio (ventas, inventario, sistema)
- routes/ - Blueprints Flask (ventas, admin, assistant, ai, diccionario)
- security/ - crypto, validation, audit
- license/ - helpers, core
- dictionary/ - helpers, routes
- response_validators/ - models, checks
- ia/ - agent.py, state.py
- db/ - users, config_inventario
- sync/ - supabase_sync
- metrics/ - routes

## Inicio Rapido (Termux)

bash install.sh
cd app/src/main/python
python app.py

## Compilar APK

Push a main dispara build automatico en GitHub Actions (tests + APK).

## Estructura

- app/src/main/python/ - Backend Flask (modular)
- app/src/main/assets/ - Frontend (JS, CSS, templates)
- app/src/main/java/ - Android (Chaquopy + WebView + Biometria)
- tests/ - Tests pytest (142 tests)
- .github/workflows/ - CI/CD GitHub Actions

## Tech Stack

- Frontend: Bootstrap 5, Chart.js, html5-qrcode
- Backend: Flask + Blueprints, SQLite
- Android: Chaquopy, WebView, Biometria nativa
- IA: NLP engine, intents, fuzzy matching, 150 tools
- Cache: IndexedDB + SQLite dual sync
- Cloud: Supabase (opcional)
- Testing: pytest (679+ pruebas)

## Documentacion

- docs/API_REFERENCE.md
- docs/DATABASE_SCHEMA.md
- docs/ARCHITECTURE.md
- docs/CONTRIBUTING.md
- CHANGELOG.md

## Licencia

MIT License - Proyecto Academico Universidad

