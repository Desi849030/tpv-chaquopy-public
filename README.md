# TPV UltraSmart v8.0

[![CI — Tests & APK](https://github.com/Desi849030/tpv-chaquopy/actions/workflows/ci.yml/badge.svg)](https://github.com/Desi849030/tpv-chaquopy/actions/workflows/ci.yml)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue)
![Android minSdk 21](https://img.shields.io/badge/Android-minSdk%2021%2B-green)
![Offline first](https://img.shields.io/badge/offline-100%25-success)
![License MIT](https://img.shields.io/badge/license-MIT-lightgrey)

Sistema de Punto de Venta profesional con IA integrada, biometría, roles multinivel y sincronización offline-first. Compilado 100% desde Android con Termux + Chaquopy (WebView + Flask embebido).

---

## ✨ Características

### Punto de Venta
- Catálogo de productos con CRUD completo, categorías e imágenes
- Carrito, escáner QR, múltiples métodos de pago
- Cierres de caja con desglose efectivo/tarjeta/transferencia
- Descuentos configurables (% y fijo)
- Importación inteligente desde Excel con fuzzy matching

### Roles y Seguridad
- **5 roles**: Desarrollador, Administrador, Supervisor, Vendedor, Cajero
- Privilegios configurables por rol (25 módulos, incl. biometría)
- Autenticación con scrypt KDF + bloqueo anti-brute force
- Biometría nativa Android (BiometricPrompt) / WebAuthn en navegador
- Guardrails: SQLi, XSS, PCI-DSS, rate limiting, auditoría

### Agente IA (100% offline)
- Motor NLP con **25 intenciones** (TF-IDF + Softmax)
- 13 herramientas por rol (finanzas, ABC, EOQ, predicciones, etc.)
- Memoria avanzada persistente en SQLite
- Motor ReAct para razonamiento multi-paso
- Handlers especializados por rol con datos REALES de BD
- Chat flotante arrastrable con sugerencias contextuales
- Agente proactivo: alerta stock crítico sin preguntar

### Infraestructura
- **Offline-first**: librerías y fuentes locales (sin CDN)
- Sincronización opcional con Supabase (nube)
- Design system propio con dark mode
- Internacionalización ES/EN

---

## 📊 Estadísticas

| Métrica | Valor |
|---------|-------|
| Backend Python | ~160 archivos, 18 tablas SQLite |
| Blueprints Flask | 20+ (modulares) |
| Frontend | 14 JS activos + 6 CSS |
| NLP intenciones | 25 |
| Herramientas IA | 13 por rol |
| Tests pytest | 54+ verdes |
| Arranque backend | ~0.3s |
| Peso frontend | ~4.9 MB (2.9 MB libs offline) |

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│                    Dispositivo Android                    │
│                                                          │
│  ┌──────────────┐  callAttr("iniciar")  ┌────────────┐  │
│  │ MainActivity  │─────────────────────▶│  Chaquopy   │  │
│  │   (Java)      │                      │ Python 3.10 │  │
│  │               │                      └──────┬──────┘  │
│  │ ┌──────────┐  │                             │         │
│  │ │ WebView  │  │  HTTP 127.0.0.1:5050  ┌─────▼──────┐  │
│  │ │(frontend)│◀─┼──────────────────────│ Flask      │  │
│  │ └──────────┘  │                      │ app.py     │  │
│  │ TPVNative     │  biometría nativa    │ +blueprints│  │
│  │(BiometricPrompt)                     └─────┬──────┘  │
│  └──────────────┘                             │         │
│                                        ┌──────▼───────┐  │
│  Frontend: index.html + 14 JS + CSS   │SQLite 18 tbl │  │
│  IndexedDB + service-worker            │ia/ agente NLP│  │
│                                        └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Backend modular (app/src/main/python/)

```
app.py                 ← 274 líneas: setup + auth + registro de blueprints
├── modules/           ← 20+ blueprints (catalogo, ventas, reportes, tools, etc.)
├── ia/                ← Agente IA (36 archivos: NLP, ReAct, handlers, memoria)
├── db/                ← Schema + DAOs (users, products, inventario)
├── security/          ← Crypto, validation, audit
├── sync/              ← Supabase sync
├── tools/             ← 13 herramientas IA
├── models/            ← TypedDicts (ventas, inventario, sistema)
├── metrics/           ← Métricas del sistema
└── decorators.py      ← Auth unificado (login_required, role_required)
```

---

## 🔐 Jerarquía de Roles

| Rol | Nivel | Permisos |
|-----|-------|----------|
| Desarrollador | 0 | Todo sin límites + debug + privilegios + licencias |
| Administrador | 1 | Tienda completa (no debug/privilegios) |
| Supervisor | 2 | Ventas, reportes, inventario, catálogo |
| Vendedor | 3 | Vender + catálogo + IA básica |
| Cajero | 3 | Cobros + catálogo + biometría |

---

## 🚀 Inicio Rápido

### Termux (Android)
```bash
cd app/src/main/python
pip install flask
python app.py
# Abrir http://127.0.0.1:5000
# Login: desarrollador / 123456
```

### Compilar APK
Push a `main` dispara el workflow CI:
1. **test** — pytest + smoke test
2. **build** — APK debug + release firmado → artefactos descargables

---

## 📁 Estructura del proyecto

```
.github/workflows/ci.yml        ← CI/CD unificado (test → build APK)
app/src/main/python/             ← Backend Flask modular
app/src/main/assets/frontend/    ← Frontend (JS, CSS, templates, libs offline)
app/src/main/java/               ← Android (Chaquopy + WebView + Biometría)
tests/                           ← Tests pytest (54+)
scripts/smoke_test.py            ← Smoke test (arranque + rutas + agente)
docs/                            ← Documentación técnica
```

## 🛠️ Tech Stack

- **Frontend**: Bootstrap 5, Chart.js, html5-qrcode, SheetJS (Excel)
- **Backend**: Flask + Blueprints, SQLite (WAL mode)
- **Android**: Chaquopy, WebView, BiometricPrompt
- **IA**: NLP TF-IDF, ReAct engine, fuzzy matching, 13 tools
- **Cache**: IndexedDB + SQLite dual sync
- **Cloud**: Supabase (opcional)
- **CI/CD**: GitHub Actions (test → build APK)

## 📄 Licencia

MIT License — Proyecto Académico Universidad

---

## Estado actual del sprint
Mejoras recientes implementadas:

- Protección de endpoints de ventas con autenticación
- Validación atómica de stock en registro de ventas
- Healthcheck en `/health` y `/api/health`
- Headers de seguridad básicos
- Tests críticos automatizados
- CI básica en GitHub Actions

## Ejecución en desarrollo
Backend Flask local:
- URL: `http://127.0.0.1:5000`

Healthcheck:
- `GET /health`
- `GET /api/health`

## Documentación técnica
- `docs/DEFENSA.md`
- `docs/openapi.yaml`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE_SCHEMA.md`
