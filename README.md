# 🚀 TPV Ultra Smart v8.0 — Rev. 14 (Tesis)

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square) ![Flask](https://img.shields.io/badge/Flask-2.2.5-black?style=flat-square) ![Chaquopy](https://img.shields.io/badge/Android-Chaquopy-green?style=flat-square) ![Tests](https://img.shields.io/badge/Tests-541%20pass-brightgreen?style=flat-square) ![Coverage](https://img.shields.io/badge/Coverage-41%25%20real-orange?style=flat-square)

Sistema de Punto de Venta (TPV) híbrido de grado enterprise para Android nativo vía Chaquopy, con persistencia atómica local (SQLite WAL), sincronización asíncrona a Supabase, y motor de IA ReAct para asistencia conversacional por rol.

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Funcionalidades](#funcionalidades)
- [Roles de Usuario](#roles-de-usuario)
- [Instalación](#instalación)
- [Tests](#tests)
- [Documentación de Tesis](#documentación-de-tesis)

## Arquitectura

```
[ WebView Android / Chaquopy ] ──► [ Blueprints Flask (28) ] ──► [ Dominio IA ReAct ]
                                                                        │
                                                                ┌───────┴───────┐
                                                                ▼               ▼
                                                       [ SQLite WAL ]  [ Supabase Cloud ]
```

- **Offline-first**: Operación de caja garantizada al 100% sin conectividad
- **Orquestación ReAct IA**: Agente decisor acoplado a 141+ herramientas
- **Seguridad Cero-Trust**: scrypt KDF + rate limiting + guardrails SQLi/XSS/PII
- **Atomicidad v10**: Ventas idempotentes con `client_txn_id`

## Funcionalidades

### Punto de Venta
- Catálogo con stock en tiempo real
- Ventas atómicas con idempotencia (v10)
- Múltiples métodos de pago
- Tickets con QR de verificación

### Gestión
- CRUD productos, categorías, tiendas, usuarios, clientes
- Inventario general + asignación a vendedores
- Importación masiva desde Excel
- Nomenclador de monedas (USD, EUR, CUP, MXN)

### IA Conversacional
- Agente ReAct con 141+ herramientas
- 5 roles: cliente, cajero, vendedor, supervisor, admin, desarrollador
- Detección de intenciones multi-intent
- Memoria persistente SQLite
- Guardrails anti SQLi/XSS/PII + rate limiting

### Seguridad
- scrypt KDF (N=16384) para passwords
- Bloqueo anti-fuerza bruta (5 intentos / 10 min)
- Rate limiting por usuario (20 req/min)
- Headers de seguridad (CSP, X-Frame-Options, etc.)
- Audit logs completos

### Debug (solo desarrollador)
- Botón 🩺 violeta abajo izquierda
- Tecla F1 para toggle (desktop)
- Panel con logs en tiempo real
- Telemetría del sistema

## Roles de Usuario

| Rol | Permisos | Debug |
|---|---|---|
| `desarrollador` | Acceso total + telemetría | ✅ 🩺 + F1 |
| `administrador` | CRUD + reportes | ❌ |
| `supervisor` | Dashboard + ABC | ❌ |
| `vendedor` | TPV + inventario | ❌ |
| `cajero` | Caja + arqueo | ❌ |
| `cliente` | Catálogo público | ❌ |

## Instalación

### En Termux (móvil)

```bash
# Clonar
git clone https://github.com/Desi849030/tpv-chaquopy.git ~/tpv-chaquopy
cd ~/tpv-chaquopy

# Aplicar fixes (en orden)
python fix_integral_v5.py
python fix_demo_final.py

# Arrancar backend
cd app/src/main/python
nohup env TPV_PORT=5050 python app.py > ~/tpv_server.log 2>&1 &
echo $! > ~/tpv_server.pid

# Abrir en Chrome (modo incógnito)
# http://localhost:5050
```

### Usuarios demo

La contraseña demo se muestra al arrancar el servidor en la consola.
Para establecerla manualmente:

```bash
export TPV_DEMO_PASSWORD="tu-password-segura"
python app.py
```

Si no se establece, se usa `demo-tpv-2026` como fallback.

| Usuario | Rol |
|---|---|
| `desarrollador` | acceso total + debug |
| `admin` | administrador |
| `supervisor1` | supervisor |
| `vendedor1` | vendedor |
| `cajero1` | cajero |

### Compilar APK

```bash
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

## Tests

```bash
# Suite completa (312 tests)
python -m pytest tests/ tests/ia/ tests/e2e/ -v

# Cobertura
coverage run -m pytest tests/ia/ tests/e2e/ tests/backend/
coverage report -m
```

### Resultados

| Métrica | Valor |
|---|---|
| Tests pasan | 312 |
| Tests skipped | 9 |
| Tests fallidos | 0 |
| Cobertura global | 32% (honesta) |
| Cobertura IA crítica | 60-89% |
| Cobertura backend crítico | >75% |

## Documentación de Tesis

- [`docs/DOCUMENTACION_TESIS.md`](docs/DOCUMENTACION_TESIS.md) — Documentación completa
- [`docs/EVALUACION_ACADEMICA.md`](docs/EVALUACION_ACADEMICA.md) — Evaluación honesta
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Arquitectura del sistema
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — Referencia API (218 rutas)
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) — Esquema SQLite (49 tablas)

## Bugs Críticos Corregidos (Rev. 14)

1. ✅ Frontend roto (commit b1c0e70) — restaurado 122KB
2. ✅ Bug "Root Access al cajero" — saludos neutros por rol
3. ✅ Login cajero1 401 — reactivación automática
4. ✅ Admin no podía crear cajeros — roles_permitidos ampliado
5. ✅ 6 endpoints CRUD faltantes — blueprint reescrito
6. ✅ Catalogo sync NameError — import + función agregados
7. ✅ Splash profesional con mesh gradient + SVG animado
8. ✅ Chat con botón Enviar grande + drag Pointer Events
9. ✅ Debug panel exclusivo desarrollador (botón 🩺 + F1)

## Stack Tecnológico

- **Backend**: Python 3.10, Flask 2.2.5, SQLite WAL, scrypt KDF
- **Frontend**: HTML5, JS modular, Bootstrap 5, Service Worker PWA
- **Android**: Chaquopy 15.0.1, AndroidX BiometricPrompt, WebView
- **IA**: Motor ReAct propio, NLP fuzzy, Guardrails v2
- **Cloud**: Supabase (PostgreSQL + RLS) — opcional

## Licencia

MIT
