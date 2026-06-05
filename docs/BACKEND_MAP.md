# Mapa del backend — archivos planos vs paquetes

> Aclaración de la estructura de `app/src/main/python/` tras la revisión.
> Objetivo: que nadie vuelva a confundir "lógica de negocio" con "duplicado".

## Patrón real del proyecto

El backend usa, intencionadamente, **dos capas con el mismo nombre**:

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| Lógica de negocio | `python/ai_fraud.py`, `ai_analytics.py`, `ai_predictor.py` | Cálculos, queries, algoritmos. **Sin Flask.** |
| Rutas (blueprint) | `python/modules/ai_fraud.py`, etc. | Endpoints HTTP que **llaman** a la lógica plana. |

Ejemplo: `modules/ai_fraud.py` define la ruta `/api/ai/fraud/dashboard` y dentro hace
`from ai_fraud import get_fraud_dashboard`. **No es un duplicado**: es separación
correcta entre la ruta y la lógica. Conviene renombrarlo en el futuro (p. ej.
`modules/ai_fraud_routes.py`) para que el nombre lo deje claro, pero **no es urgente**
y tocarlo ahora implica cambiar imports en varios sitios.

## Código muerto eliminado ✅

| Archivo | Motivo |
|---------|--------|
| `models.py` | Era un *facade* `from models import ...`, pero existe el paquete `models/`. En Python el paquete **siempre gana**, así que el archivo nunca se cargaba (sombreado). |
| `security.py` | Igual: existe el paquete `security/` que exporta todo lo que el plano definía. Sombreado, nunca cargado. |

Verificado: `import models` y `import security` resuelven al paquete; eliminar los
archivos planos no cambia nada. Smoke test OK tras el borrado.

## Pendiente / a vigilar ⚠️

### `supabase_sync.py` (plano) vs `sync/supabase_sync.py` (paquete)
- **Conviven y divergen.** El plano es un *stub v6.0* con `setup_supabase()` y
  `sincronizar_todo()` que devuelven valores fijos. El paquete `sync/` es la
  implementación real y completa.
- `app.py` y `mock_routes.py` importan del **plano** (`from supabase_sync import
  setup_supabase, sincronizar_todo`).
- Los módulos modernos (`modules/settings_*`, `modules/admin_helpers`, etc.) importan
  del **paquete** (`from sync.supabase_sync import ...`).
- ⚠️ **Riesgo**: `setup_supabase()` solo existe en el plano; el paquete no lo tiene.
  Por eso **no se ha redirigido todavía** (rompería `app.py`).
- **Plan recomendado** (cuando se haga el refactor de `app.py` a factory):
  1. Añadir `setup_supabase()` al paquete `sync/supabase_sync.py` (o a `sync/config.py`).
  2. Cambiar los imports de `app.py`/`mock_routes.py` a `from sync.supabase_sync import ...`.
  3. Eliminar el plano `supabase_sync.py`.

### `ai_agent.py` (plano, 2 líneas)
- Es un *facade* legítimo: `from ia.agent import process_question`, usado por
  `modules/settings_other.py`. **Se conserva** porque sí está en uso y no hay conflicto
  de paquete (no existe `ai_agent/`). Bajo coste, no molesta.

### Otros agentes IA dispersos
- Existen `ia_agent.py` (facade), `ia/agent.py`, `ia/agent_core.py`, `ia/agent_master.py`,
  `ia/agent_pro.py`, `agent/tpv_agent.py`, `modules/agent.py`.
- `app.py` usa `from ia.agent_master import agent`. Consolidar esto es trabajo del
  bloque "Agente IA", no de la limpieza de duplicados.

## Regla para el futuro

- **Lógica de negocio** → archivo plano o paquete de dominio, sin Flask.
- **Rutas** → siempre en `modules/<dominio>_*.py` como blueprint.
- **Nunca** crear un `X.py` y un paquete `X/` a la vez (el archivo queda sombreado).
