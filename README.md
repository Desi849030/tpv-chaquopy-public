# TPV UltraSmart v2.5.5

Sistema de Punto de Venta Profesional con IA integrada, biometria, roles multinivel y sincronizacion offline. Compilado 100% desde Android con Termux + Chaquopy.

## Caracteristicas Principales

- Autenticacion multinivel: Desarrollador, Administrador, Supervisor, Vendedor, Cajero
- Biometria en el login: huella/rostro (WebAuthn en navegador + puente Android nativo en APK)
- Bienvenida personalizada por nombre, rol y hora del dia
- Punto de venta: Catalogo, carrito, escaner QR, pagos, descuentos, tickets
- Inventario: Stock diario, alertas bajo stock, cierres de caja, comisiones
- Gestion de productos: CRUD completo, categorias, import/export Excel inteligente
- IA Asistente: motor NLP con herramientas y memoria; chat personalizado por rol,
  boton flotante arrastrable, sugerencias contextuales, 100% offline
- Privilegios por rol: activar/desactivar modulos por rol (admin/desarrollador)
- Seguridad y Biometria: panel PCI-DSS, HET (anti-amenazas), WebSocket
- Panel de Metricas del Sistema: RAM, almacenamiento real y tablas de la BD
- Importacion Excel: fuzzy matching, validacion UTF-8 (actualiza almacen real)
- Tienda online: Clientes, pedidos, notificaciones, cola offline
- Offline-first: librerias y fuentes locales (sin CDN), IndexedDB + SQLite
- Seguridad: SQLi reforzado (tautologias/time-based), XSS, RBAC, auditoria
- Diseño moderno: design system propio, dark mode completo, dialogos con estilo
- Debug del desarrollador: captura de errores/fetch con tiempos y estadisticas
- Licencias, Dashboard con graficos, traduccion ES/EN, Supabase opcional

## Estadisticas (reales)

- Backend: ~172 archivos Python, 177 rutas Flask registradas
- Frontend: 86 archivos JavaScript + 6 hojas CSS (incl. design system)
- Tests: suite estable de 51 pruebas verdes + 5 skip (ver `pytest.ini`)
- Smoke test: arranque + rutas críticas + agente + SQLi (`scripts/smoke_test.py`)
- 100% offline: todas las librerías y fuentes servidas localmente (sin CDN)

> Detalle completo de las mejoras recientes en `docs/CHANGELOG_refactor.md`.

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

Push a `main` dispara el workflow `.github/workflows/ci.yml`:

1. **test** — instala deps, corre la suite estable de pytest y el smoke test.
2. **build** — (solo si test pasa) genera APK debug + release firmado y los
   sube como artefactos descargables.

Probar el backend en local / Termux antes de subir:

```bash
pip install -r requirements.txt
python scripts/smoke_test.py      # red de seguridad: arranque + rutas + agente
python -m pytest                  # suite estable
cd app/src/main/python && python app.py   # abrir http://127.0.0.1:5050
```

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

