# TPV UltraSmart v2.5.5

[![CI — Tests & APK](https://github.com/Desi849030/tpv-chaquopy/actions/workflows/ci.yml/badge.svg)](https://github.com/Desi849030/tpv-chaquopy/actions/workflows/ci.yml)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue)
![Android minSdk 21](https://img.shields.io/badge/Android-minSdk%2021%2B-green)
![Offline first](https://img.shields.io/badge/offline-100%25-success)
![License MIT](https://img.shields.io/badge/license-MIT-lightgrey)

Sistema de Punto de Venta Profesional con IA integrada, biometria, roles multinivel y sincronizacion offline. Compilado 100% desde Android con Termux + Chaquopy (WebView + Flask embebido).

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

## Estadisticas (reales, verificadas)

- Backend: 157 archivos Python, **181 rutas Flask** registradas
- Frontend: **14 archivos JavaScript activos** + 6 hojas CSS (incl. design system)
  - Codigo heredado archivado en `docs/_legacy_js/` y `docs/_legacy_py/` (fuera del APK)
- Tests: **54 pruebas pytest verdes** + 5 skip + suite de regresion del import Excel
- Smoke test: arranque + rutas criticas + agente + SQLi (`scripts/smoke_test.py`)
- Arranque del backend (import de `app.py`): **~0.3 s**
- Peso del frontend empaquetado: ~4.9 MB (2.9 MB son librerias offline locales)
- 100% offline: todas las librerias y fuentes servidas localmente (sin CDN)

> Detalle completo de las mejoras recientes en `docs/CHANGELOG_refactor.md`.

## Arquitectura (vista general)

```
┌─────────────────────────────────────────────────────────────┐
│                      Dispositivo Android                      │
│                                                               │
│  ┌────────────────┐   callAttr("iniciar")   ┌─────────────┐  │
│  │  MainActivity   │ ───────────────────────▶│  Chaquopy   │  │
│  │   (Java)        │                          │  Python 3.10│  │
│  │                 │                          └──────┬──────┘  │
│  │  ┌───────────┐  │                                 │         │
│  │  │  WebView  │  │  HTTP 127.0.0.1:5050      ┌──────▼──────┐ │
│  │  │ (frontend)│◀─┼──────────────────────────│ Flask app.py│ │
│  │  └───────────┘  │                           │ + blueprints│ │
│  │  TPVNative      │   biometria nativa        │  (modules/) │ │
│  │  (BiometricPrompt)                          └──────┬──────┘ │
│  └────────────────┘                                   │        │
│                                              ┌─────────▼──────┐ │
│   Frontend: index.html + 14 JS + CSS         │ SQLite (18 tbl)│ │
│   IndexedDB (cache) + service-worker (offline)│ ia/ agente NLP│ │
│                                              └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
        (Termux/navegador: Flask autoarranca en 127.0.0.1:5000)
```

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

```bash
bash tpv_termux_setup.sh        # instala dependencias (Python + Flask)
bash tpv_termux_run.sh          # arranca el backend en 127.0.0.1:5000
# o manualmente:
cd app/src/main/python && python app.py
```

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

- app/src/main/python/ - Backend Flask (modular: db/, ia/, modules/, security/, sync/, metrics/, tools/)
- app/src/main/assets/ - Frontend (14 JS activos, CSS, templates, libs offline)
- app/src/main/java/ - Android (Chaquopy + WebView + Biometria nativa)
- tests/ - Tests pytest (suite estable de 54 + regresion)
- scripts/smoke_test.py - Red de seguridad: arranque + rutas + agente + SQLi
- docs/_legacy_js, docs/_legacy_py - Codigo heredado archivado (no entra al APK)
- .github/workflows/ - CI/CD GitHub Actions (test -> build APK)

## Tech Stack

- Frontend: Bootstrap 5, Chart.js, html5-qrcode
- Backend: Flask + Blueprints, SQLite
- Android: Chaquopy, WebView, Biometria nativa
- IA: NLP engine, intents, fuzzy matching, herramientas (tools/)
- Cache: IndexedDB + SQLite dual sync
- Cloud: Supabase (opcional)
- Testing: pytest (suite estable de 54) + smoke test + regresion import Excel

## Documentacion

- docs/API_REFERENCE.md
- docs/DATABASE_SCHEMA.md
- docs/ARCHITECTURE.md
- docs/CONTRIBUTING.md
- CHANGELOG.md

## Licencia

MIT License - Proyecto Academico Universidad

