# TPV Ultra Smart v6.9

Sistema de Punto de Venta Profesional con IA integrada, biometria, roles multinivel y sincronizacion offline.

## Caracteristicas Principales

- **Autenticacion multinivel**: Desarrollador, Administrador, Supervisor, Vendedor + biometria
- **Punto de venta**: Catalogo, carrito, escaner QR, pagos, descuentos
- **Inventario**: Stock diario, cierres de caja, comisiones
- **Gestion de productos**: CRUD, categorias, import/export Excel
- **IA Asistente**: Motor NLP, intents, guardrails, memoria, anti-slop
- **Tienda online**: Clientes, pedidos, notificaciones, cola offline
- **Offline**: WiFi local, IndexedDB + SQLite dual
- **PWA**: Service Worker, manifest, cache
- **Seguridad**: Decoradores de rol, PCI, anti-fraud, attestation
- **Licencias**: Activacion con dias de prueba
- **Dashboard**: KPIs animados, graficos
- **Traduccion**: Google Translate ES/EN
- **Debug**: Panel inteligente con diagnostico automatico
- **Supabase**: Sincronizacion cloud opcional

## Inicio Rapido (Termux)

    bash install.sh
    cd app/src/main/python/
    python app.py

## Compilar APK

Push a main dispara build automatico en GitHub Actions.

## Estructura

    app/src/main/python/     Backend Flask (50+ archivos, ~10,400 lineas)
    app/src/main/assets/frontend/
      templates/index.html   Template principal Jinja2
      static/css/tpv/        8 archivos CSS (~1,200 lineas)
      static/js/tpv/         27 modulos JavaScript (~11,600 lineas)
    app/src/main/java/       Android (Chaquopy + WebView)
    docs/                    Documentacion
    tests/                   Tests pytest (8 archivos)

## Jerarquia de Roles

    Desarrollador  -> Todo sin limites + licencias + debug
    Administrador -> Tienda completa (NO licencias)
    Supervisor    -> Solo lectura/reportes
    Vendedor      -> Solo vender

## Tech Stack

- **Frontend**: Bootstrap 5, Chart.js, html5-qrcode
- **Backend**: Flask + Blueprints, SQLite
- **Android**: Chaquopy, WebView, Biometria nativa
- **IA**: NLP engine, intents, fuzzy matching, memory
- **Cloud**: Supabase (opcional)

## Documentacion

- docs/API_REFERENCE.md
- docs/DATABASE_SCHEMA.md
- docs/ARCHITECTURE.md
- docs/CHANGELOG.md
