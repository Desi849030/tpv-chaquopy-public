# Python heredado (no se usa en el backend)

Esta carpeta contiene **15 módulos Python que ningún archivo importa**.
Se movieron aquí en la limpieza de FASE 1 (junio 2026) **sin borrarlos**.

## Archivos y por qué sobran
- `mock_routes.py` — endpoints falsos antiguos; ya se sirven los blueprints reales de `modules/`.
- `tpv_rutas.py` — detección de rutas para Pydroid 3 (obsoleto; ahora se usa `start_server.iniciar()`).
- `modules__inventory_*.py` (catalogo, crud, diario, other) — versiones viejas; la lógica viva está en `modules/inventory.py` + `*_helpers.py`.
- `modules__loyalty_core.py`, `modules__loyalty_extra.py` — sustituidos por `modules/loyalty_helpers.py`.
- `modules__settings_state.py` — sustituido por `modules/settings_helpers.py`.
- `modules__tienda_*.py` (clientes, other, productos, tiendas) — sustituidos por `modules/tienda_bp.py` + helpers.
- `sync__async_sync.py` — motor de sync no referenciado.
- `ia__agent_routes.py` — rutas de agente no registradas (el agente vivo es `ia/agent_master.py` vía `modules/agent.py`).

## Verificación hecha
Tras mover estos archivos: `scripts/smoke_test.py` ✅ (181 rutas) y `pytest` ✅ (54 tests).

## ¿Puedo borrar esta carpeta?
Sí. Está **fuera** de `app/src/main/python/`, así que Chaquopy no la empaqueta
en el APK. Solo ocupa espacio en el repo.

> ⚠️ NO está aquí `start_server.py`: ese SÍ lo usa Java (`MainActivity` llama
> `getModule("start_server").callAttr("iniciar", ...)`), aunque ningún `.py` lo importe.
