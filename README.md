# 🚀 TPV Ultra Smart v8.0 — Modular AI Edition (Rev. 14)

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.13-blue?style=flat-square) ![Flask](https://img.shields.io/badge/Flask-2.2.5-black?style=flat-square) ![Chaquopy](https://img.shields.io/badge/Android-Chaquopy_Native-green?style=flat-square) ![Tests](https://img.shields.io/badge/Test_Pass-312%2F312-brightgreen?style=flat-square) ![Coverage](https://img.shields.io/badge/Coverage-32%25_Honest-blue?style=flat-square)

Sistema de Punto de Venta (TPV) Híbrido de Grado Enterprise, diseñado para contenedores Android nativos vía Chaquopy con persistencia atómica local (SQLite WAL) y sincronización asíncrona hacia Supabase (PostgreSQL).

## 🏗️ Arquitectura de Núcleo (DDD)
```
[ WebView Android / Chaquopy ] ──► [ Blueprints (/modules/*.py) ] ──► [ Dominio Puro (ai_fraud.py) ]
                                                                          │
                                                                  ┌───────┴───────┐
                                                                  ▼               ▼
                                                         [ SQLite Local ]  [ Supabase Cloud ]
```
* **Resiliencia Offline-First:** Operación de caja garantizada al 100% ante pérdida de conectividad.
* **Orquestación ReAct IA:** Agente decisor autónomo acoplado a 13 herramientas del sistema.
* **Seguridad Cero-Trust:** Control de concurrencia de sesión y bloqueo anti-fuerza bruta HTTP 429.

## 🧪 Estado de Calidad (Rev. 14 — honesto)

**Suite actual:** 312 tests pasan, 9 skipped, 0 fallos.

| Métrica | Valor |
|---|---|
| Tests totales | 312 pasan / 9 skipped / 0 fallos |
| Cobertura global | 32% (sobre 9,579 statements reales) |
| Cobertura módulos IA críticos | 60% promedio (agent_master 72%, guardrails_v2 89%, agent_chat_bp 78%) |
| Cobertura backend crítico | >75% (auth 74%, db/users 87%, ventas_atomic_v10 57%) |

**Ver el detalle completo en:** [`docs/EVALUACION_ACADEMICA.md`](docs/EVALUACION_ACADEMICA.md)

## 🔐 Fixes críticos en Rev. 14

1. **Frontend restaurado**: el commit `b1c0e70` ("QA Pass 100%") había reemplazado el `templates/index.html` de 122KB por un placeholder de 219B. Restaurado desde commit `85fa56f`.
2. **Bug "Root Access al cajero"**: el agente IA respondía al cajero con "Root Access concedido" (frase reservada al desarrollador). Corregido en `modules/agent_chat_bp.py` con saludos neutros por rol.
3. **Login cajero1 401**: `_init_db_if_empty` ahora reactiva usuarios demo desactivados por tests anteriores.
4. **Admin no puede crear cajero**: `roles_permitidos` ampliado para permitir a admin y dev crear cajeros.
5. **Robot E2E con credenciales incorrectas**: `tools/robot_config.json` ahora usa credenciales reales (`cajero1`, `admin`, `desarrollador`) y puerto 5050 correcto.

## 🤖 Robustez de la IA

### Lo que sí es robusto
- **Detección de SQLi/XSS/PII**: 23 tests validan 5 payloads maliciosos de cada tipo
- **Rate limiting por usuario**: bloquea tras 20 requests/minuto
- **Saludo seguro por rol**: ninguna respuesta contiene "root access" ni credenciales
- **Degradación elegante**: si el motor ReAct falla, cae a modo catálogo sin crashear
- **Idempotencia de ventas**: `client_txn_id` evita doble cobro ante reintentos

### Lo que NO es robusto (reconocido)
- **Motor ReAct completo** (255 stmts) solo 21% de cobertura: ciclo Thought→Action→Observation no testeado end-to-end
- **Memoria persistente** (167 stmts) al 15%: ciclo save/recall/search no validado en todos los paths
- **Sincronización Supabase**: no testeada (requiere credenciales cloud)

## 🚀 Cómo ejecutar

### En Termux (móvil)

```bash
# Clonar y aplicar todos los fixes
git clone https://github.com/Desi849030/tpv-chaquopy.git
cd tpv-chaquopy
bash tpv_fix_and_run.sh          # Aplica fixes y commitea
bash tpv_fix_and_run.sh run      # Arranca backend en http://localhost:5050
```

### En navegador del móvil

Una vez arrancado el backend, abre: `http://localhost:5050`

**Usuarios demo** (todos con password `123456`):
- `admin` (administrador)
- `desarrollador` (desarrollador)
- `supervisor1` (supervisor)
- `vendedor1` (vendedor)
- `cajero1` (cajero)

### Ejecutar tests

```bash
cd ~/tpv-trabajo
python -m pytest tests/ tests/ia/ tests/e2e/ -v    # 312 tests
coverage run -m pytest tests/ia/ tests/e2e/ tests/backend/
coverage report -m                                  # Cobertura real
```

## 📦 Compilar APK

```bash
./gradlew assembleDebug
# APK resultante: app/build/outputs/apk/debug/app-debug.apk
```

## 📚 Documentación

- [`docs/EVALUACION_ACADEMICA.md`](docs/EVALUACION_ACADEMICA.md) — Evaluación honesta de calidad
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Arquitectura del sistema
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — Referencia de la API
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) — Esquema SQLite
