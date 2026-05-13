# Changelog - TPV UltraSmart

## [v2.5.5] - 2026-05-14 — Models Package

### Refactor
- `models.py` (194 lineas) dividido en `models/` package:
  - `models/ventas.py` — Venta, DetalleVenta, Corte, Credito, APIResponse, PaginatedResponse, ValidationResult
  - `models/inventario.py` — Producto, Categoria, InventarioGeneral, MovimientoInventario
  - `models/sistema.py` — Usuario, Cliente, Caja, Configuracion, Log, MovimientoCaja
- Facade `models.py` preserva compatibilidad con imports existentes

### Tests
- 142/142 pasados

---

## [v2.5.4] - 2026-05-14 — Security Functions

### Features
- `sanitize_input()` — Limpieza de control chars y trimming
- `validate_email()` — Validacion regex de formato email
- `generate_api_key()` — Generacion de claves API con secrets.token_hex
- `rate_limit_key()` — Formato de clave rate limit `rl:accion:cliente`
- `get_hmac_key()`, `get_jwt_secret()`, `get_csrf_token()`, `get_session_salt()` — Secretos dinamicos

### Fixes
- `verify_password()` ahora retorna False para inputs None/empty
- Import `os` agregado en `security/crypto.py`

### Tests
- 142/142 pasados (0 pre-existing failures restantes)

---

## [v2.5.3] - 2026-05-14 — Monolith Split (4 modulos)

### Refactor
- `tpv_security.py` (234L) → `security/{crypto,validation,audit}.py`
- `output_validator.py` (257L) → `response_validators/{models,checks}.py`
- `license_manager.py` (316L) → `license/{helpers,core}.py`
- `diccionario_tpv.py` (247L) → `dictionary/{helpers,routes}.py`
- `_SQLI_PATTERNS` migrado correctamente a `security/validation.py`
- Decorators filtrados corregidos en `dictionary/helpers.py`
- `validators.py` renombrado a `response_validators/` para evitar shadowing

### Tests
- 134/142 pasados (8 pre-existing en TestSecurity, corregidos en v2.5.4)

---

## [v2.5.2] - 2026-05-14 — Module Migration (3 modulos)

### Refactor
- `agent_state.py` (216L) → `ia/state.py`
- `db_users.py` (213L) → `db/users.py`
- `db_config_inventario.py` (225L) → `db/config_inventario.py`
- Facades con re-export explicita de funciones privadas
- Import paths actualizados en dependencias

### Tests
- 142/142 pasados

---

## [v2.5.1] - 2026-05-14 — App Cleanup + JS Split + Metrics Fix

### Refactor
- `app.py` limpiado: 368 → 335 lineas (rutas duplicadas y fuera de lugar eliminadas)
- `tpv_estado_sync.js` (970L) → `tpv_estado_{persist,ui,backup}.js`
- `smart_excel_importer.js` (1332L) → `smart_excel_importer.js` + `smart_excel_compat.js`

### Fixes
- Ruta duplicada `/dev/metricas` eliminada de `metrics/routes.py`

### Tests
- 142/142 pasados
