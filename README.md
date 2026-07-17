# TPV Ultra Smart v6.0 — Agente IA con Chaquopy

Sistema de Punto de Venta con agente conversacional IA, ejecutándose
completamente offline en Android vía Chaquopy (Python 3.14).

## Arquitectura

```
app.py (Flask) ←→ ia/agent.py ←→ ia/handlers*.py
                        ↕
                   ia/db_utils.py ←→ tpv_datos.db (SQLite)
                        ↕
                   v13 modules (9)
```

## Módulos v13 (9/9 integrados)

| Módulo | Función | Ubicación |
|--------|---------|-----------|
| `intent_router` | Detección de intención por keywords | `ia/intent_router.py` |
| `compaction` | Compactación de historial largo | `ia/compaction.py` |
| `skill_registry` | Registro dinámico de habilidades | `ia/skill_registry.py` |
| `denial_tracking` | Seguimiento de respuestas negativas | `ia/denial_tracking.py` |
| `error_formatter` | Formateo amigable de errores | `ia/error_formatter.py` |
| `task_manager` | Gestor de tareas multi-paso | `ia/task_manager.py` |
| `hooks` | Pre/post hooks del pipeline | `ia/hooks.py` |
| `result_cache` | Cache de resultados por query | `ia/result_cache.py` |
| `response_budget` | Límite de tokens en respuesta | `ia/response_budget.py` |

### Pipeline del Agente

```
process_question()
  ├→ intent_router (detectar intención)
  ├→ result_cache (verificar cache)
  ├→ compaction (si historial > umbral)
  ├→ agentic gateway (ReAct, si disponible)
  │   └→ response_budget (trim respuesta)
  └→ fallback: Agent.process()
      ├→ hooks pre (pre-procesamiento)
      ├→ dispatch por rol:
      │   handle_cliente | handle_vendedor | handle_cajero
      │   handle_supervisor | handle_admin | handle_dev
      ├→ error_formatter (si hay error)
      └→ result_cache (guardar resultado)
```

## Roles del Agente

- **Cliente**: Consultas de precio, stock, compras, devoluciones
- **Vendedor**: Reportes de ventas, inventario, promociones
- **Cajero**: Cobros, tickets, corte de caja
- **Supervisor**: Supervisión, devoluciones, configuración
- **Admin**: Panel administrativo, reportes ejecutivos
- **Dev**: Debug, logs, métricas del sistema

## Estructura de Archivos

```
app/src/main/python/
├── app.py                    # Servidor Flask principal (79KB)
├── ia/
│   ├── agent.py              # Agente IA con v13 integrado
│   ├── db_utils.py           # Utilidades DB con cache v13
│   ├── handlers.py           # Re-export de handlers
│   ├── handlers_base.py      # Handlers base
│   ├── handlers_cliente.py   # Handler rol cliente
│   ├── handlers_staff.py     # Handlers staff (vendedor, cajero, etc.)
│   ├── intent_router.py      # v13
│   ├── compaction.py         # v13
│   ├── skill_registry.py     # v13
│   ├── denial_tracking.py    # v13
│   ├── error_formatter.py    # v13
│   ├── task_manager.py       # v13
│   ├── hooks.py              # v13
│   ├── result_cache.py       # v13
│   └── response_budget.py    # v13
├── tests/
│   ├── test_v13_modules.py   # Tests de los 9 módulos v13
│   ├── test_agent_roles_v12.py
│   ├── test_e2e_pipeline.py
│   └── ...
├── database.py
├── db_connection.py
├── ia_assistant.py
├── decorators.py
└── ...
```

## Ejecutar

```bash
cd app/src/main/python
python app.py
# → http://localhost:5000
# Login: desarrollador / dev2024
```

## Aplicar Patches

```bash
# Crear módulos v13
python patch_v13_agent_10_10.py

# Integrar en agent.py + db_utils.py
python patch_v13c_integrate.py
python patch_v13d_integrate.py

# Ejecutar tests
python tests/test_v13_modules.py
```

## Características

- 100% offline — sin dependencias de API externa para funciones core
- Multi-rol con dispatch inteligente
- Pipeline agentic (ReAct) con fallback clásico
- 9 módulos v13 no-invasivos (try/except con flags _HAS_*)
- Cache de resultados para respuestas rápidas
- Detección de intención por keywords
- Compactación automática de historial
- Gestor de tareas multi-paso
- Formateo profesional de errores
- Budget de tokens para respuestas concisas
