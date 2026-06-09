# Arquitectura — TPV UltraSmart v8.0

## Capas del sistema

```
┌─ Android Layer ─────────────────────────────────────────┐
│  MainActivity.java                                      │
│  ├── Chaquopy (Python 3.10 embebido)                    │
│  ├── WebView (carga frontend desde Flask)               │
│  └── TPVNative (puente JS↔Java: BiometricPrompt)        │
└─────────────────────────────────────────────────────────┘
         │ HTTP 127.0.0.1:5050
┌─ Backend Layer ─────────────────────────────────────────┐
│  app.py (274 líneas)                                    │
│  ├── Auth (login/logout/me)                             │
│  ├── _init_db_if_empty() (datos demo)                   │
│  └── Registro de 20+ Blueprints                         │
│                                                         │
│  modules/ (Blueprints)                                  │
│  ├── catalogo_bp.py     CRUD productos + catálogo       │
│  ├── ventas_core_bp.py  Registro, cierres, totales      │
│  ├── reportes_bp.py     Reportes, CSV, métricas         │
│  ├── tools_bp.py        Herramientas IA (13 tools)      │
│  ├── diag_bp.py         Health, diagnóstico, state      │
│  ├── clientes_bp.py     Registro/listado clientes       │
│  ├── import_bp.py       Importación Excel/JSON          │
│  ├── usuarios_bp.py     CRUD usuarios + privilegios     │
│  ├── agent_chat_bp.py   Chat con agente IA              │
│  ├── inventory.py       Inventario general/diario       │
│  ├── sales.py           Gastos, reportes, descuentos    │
│  ├── auth.py            Licencias, biometría            │
│  ├── settings_bp.py     Configuración + Supabase        │
│  ├── admin_bp.py        Admin + privilegios             │
│  └── ...                                                │
│                                                         │
│  ia/ (Agente IA — 36 archivos)                          │
│  ├── agent_master.py    Orquestador principal           │
│  ├── agent_pro.py       Fallback con personalidades     │
│  ├── nlp_engine.py      Clasificador TF-IDF (25 int.)  │
│  ├── tool_system.py     13 herramientas por rol         │
│  ├── handlers_*.py      Respuestas por rol              │
│  ├── react_core.py      Motor ReAct multi-paso          │
│  ├── memory_*.py        Memoria persistente SQLite      │
│  ├── catalog.py         Cache de productos (P, O)       │
│  ├── metrics.py         Queries financieras (F, M)      │
│  ├── guardrails*.py     Seguridad IA                    │
│  └── proactive_agent.py Alertas automáticas             │
│                                                         │
│  db/                    Schema + DAOs                   │
│  ├── schema.py          18 tablas (CREATE TABLE)        │
│  ├── users.py           Login, CRUD usuarios            │
│  ├── products_*.py      Inventario, catálogo            │
│  └── config_inventario  Configuración inventario        │
│                                                         │
│  decorators.py          Auth unificado                  │
│  db_connection.py       Conexión SQLite (WAL mode)      │
│  start_server.py        Arranque para Chaquopy/Termux   │
└─────────────────────────────────────────────────────────┘
         │ SQLite (WAL mode)
┌─ Data Layer ────────────────────────────────────────────┐
│  tpv_datos.db (18 tablas)                               │
│  ├── usuarios, productos, inventario_general            │
│  ├── historial_ventas, cierres_caja, gastos             │
│  ├── clientes, licencias, descuentos_config             │
│  ├── inventario_diario, entradas_productos              │
│  ├── app_state, logs_sistema, auditoria                 │
│  └── login_intentos, historial_diario, cierres_diario   │
└─────────────────────────────────────────────────────────┘
```

## Flujo de una petición

1. Usuario toca un botón en el WebView
2. JavaScript hace `fetch('/api/catalogo')`
3. Flask lo despacha al blueprint `catalogo_bp`
4. El blueprint consulta SQLite via `db_connection.obtener_conexion()`
5. Devuelve JSON al frontend
6. JavaScript actualiza el DOM

## Flujo del Agente IA

1. Usuario escribe en el chat flotante
2. `tpv_chat.js` → `POST /api/agent/chat`
3. `agent_chat_bp.py` → `AgentMaster.process()`
4. AgentMaster:
   - Detecta intención (NLP + keyword fallback)
   - Busca productos (fuzzy match + SQL)
   - Delega a handler del rol (vendedor, admin, etc.)
   - Enriquece con Skills
   - Humaniza y sanitiza
   - Guarda en memoria avanzada
5. Respuesta JSON → burbuja en el chat
