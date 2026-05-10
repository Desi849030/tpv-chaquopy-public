# TPV Ultra Smart v2.1.0

Sistema de Punto de Venta Profesional con IA integrada, biometria, roles multinivel y sincronizacion offline. Compilado 100% desde Android con Termux + Chaquopy.

## Caracteristicas Principales

- **Autenticacion multinivel**: Desarrollador, Administrador, Supervisor, Vendedor + biometria nativa
- **Punto de venta**: Catalogo, carrito, escaner QR, pagos, descuentos, tickets
- **Inventario**: Stock diario, alertas bajo stock, cierres de caja, comisiones
- **Gestion de productos**: CRUD completo, categorias, import/export Excel inteligente
- **IA Asistente**: Motor NLP con 150 herramientas, intents, guardrails, memoria contextual, razonamiento
- **Diccionario comercial**: Sinonimos, definiciones, correccion ortografica offline
- **Panel dev metrics**: RAM, disco, formulas inventario, KPIs en tiempo real
- **Importacion Excel**: Levenshtein fuzzy matching, 4 estrategias, validacion de filas, UTF-8
- **Busqueda con acentos**: Funcion UNACCENT SQLite para busqueda insensible a tildes
- **Tienda online**: Clientes, pedidos, notificaciones, cola offline
- **Offline-first**: WiFi local, IndexedDB (cache ilimitado) + SQLite dual
- **PWA**: Service Worker, manifest, cache inteligente
- **Seguridad**: Decoradores de rol, PCI-DSS, anti-fraud, attestation, scrypt hashing
- **Licencias**: Activacion con dias de prueba
- **Dashboard**: KPIs animados, graficos Chart.js
- **Traduccion**: Google Translate ES/EN
- **Debug**: Panel inteligente con diagnostico automatico
- **Supabase**: Sincronizacion cloud opcional

## Estadisticas del Proyecto

| Componente | Archivos | Lineas |
|-----------|----------|--------|
| Python (backend) | 62 | ~13,500 |
| JavaScript (frontend) | 38 | ~14,000 |
| CSS | 10 | ~1,400 |
| Tests | 8 | 95 tests |
| **Total** | **118+** | **~28,900** |

- **150 herramientas** del agente IA en **17 categorias**
- **95/95 tests** pasando
- **15 commits** desde v2.0.0-stable

## Jerarquia de Roles

| Rol | Permisos |
|-----|----------|
| Desarrollador | Todo sin limites + licencias + debug + dev metrics |
| Administrador | Tienda completa (NO licencias) |
| Supervisor | Solo lectura/reportes |
| Vendedor | Solo vender + IA basica |

## Categorias de Herramientas IA (150 total)

| Categoria | Cantidad | Descripcion |
|-----------|----------|-------------|
| settings | 23 | Configuracion general |
| inventario | 18 | Gestion de stock |
| tienda | 14 | Tienda y pedidos |
| analytics | 12 | Analisis y reportes |
| ventas | 11 | Transacciones |
| admin | 11 | Administracion |
| validacion | 9 | Validacion de datos |
| ia_assistant | 10 | Control del asistente IA |
| seguridad | 7 | Seguridad y fraudes |
| lealtad | 7 | Programa de puntos |
| auth | 5 | Autenticacion |
| licencia | 6 | Gestion de licencias |
| dev | 4 | Dev metrics |
| websocket | 4 | Comunicacion realtime |
| diccionario | 3 | Sinonimos y definiciones |
| importacion | 3 | Importacion Excel |
| general | 3 | Utilidades generales |

## Inicio Rapido (Termux)

    bash install.sh
    cd app/src/main/python
    python app.py

## Compilar APK

Push a main dispara build automatico en GitHub Actions.

## Estructura del Proyecto

    app/src/main/python/     Backend Flask (62 archivos, ~13,500 lineas)
    app/src/main/assets/frontend/
      templates/             Templates Jinja2 (index + 7 partials + dev panel)
      static/css/            10 archivos CSS (~1,400 lineas)
      static/js/tpv/         38 modulos JavaScript (~14,000 lineas)
    app/src/main/java/       Android (Chaquopy + WebView + Biometria)
    tests/                   Tests pytest (8 archivos, 95 tests)
    .github/workflows/       CI/CD GitHub Actions

## Tech Stack

- **Frontend**: Bootstrap 5, Chart.js, html5-qrcode
- **Backend**: Flask + Blueprints, SQLite (UNACCENT custom function)
- **Android**: Chaquopy, WebView, Biometria nativa (FingerprintManager)
- **IA**: NLP engine, intents, fuzzy matching (Levenshtein), memory, 150 tools
- **Cache**: IndexedDB (frontend) + SQLite (backend) dual sync
- **Cloud**: Supabase (opcional)
- **Testing**: pytest (95 tests)

## Cambios Recientes (v2.0.0 - v2.1.0)

- feat: Modulo diccionario_tpv con sinonimos, definiciones y correccion ortografica
- feat: 150 herramientas IA en 17 categorias (9 nuevas desde v2.0.0)
- feat: Panel dev metrics (RAM, disco, formulas inventario)
- feat: Importacion Excel 100% confiable (Levenshtein, 4 estrategias, validacion)
- feat: Migracion IndexedDB (cache ilimitado, TTL, offline fallback)
- fix: Busqueda insensible a tildes (UNACCENT SQLite custom function)
- fix: Tildes y caracteres especiales en respuestas del agente IA
- fix: Boton dark mode posicion fija en WebView
- fix: readyState invertido en catalog_and_order
- fix: CSS rutas absolutas, metas duplicadas, Bootstrap defer
- fix: 4 bugs offline/cache, 5 bugs criticos de seguridad
- refactor: Logging, silent exceptions, limpieza de prints

## Documentacion

- docs/API_REFERENCE.md
- docs/DATABASE_SCHEMA.md
- docs/ARCHITECTURE.md

## Licencia

Proyecto academico - Universidad