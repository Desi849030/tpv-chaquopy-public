# Registro de Cambios — TPV UltraSmart

## v2.5.5 (2026-05-14)

### Models Package
- **Division**: `models.py` (194 lineas, 17 TypedDicts) reorganizado en `models/` package por dominio:
  - `models/ventas.py` — Venta, DetalleVenta, Corte, Credito, APIResponse, PaginatedResponse, ValidationResult
  - `models/inventario.py` — Producto, Categoria, InventarioGeneral, MovimientoInventario
  - `models/sistema.py` — Usuario, Cliente, Caja, Configuracion, Log, MovimientoCaja
- **Facade**: re-exporta todos los tipos, preservando compatibilidad
- **Impacto**: Solo `database.py` importa desde models
- Tests: 142/142

---

## v2.5.4 (2026-05-14)

### Security Functions
- **Nuevas funciones** para tests `test_security_v3.py`:
  - `security/validation.py`: `sanitize_input(val)`, `validate_email(email)`
  - `security/crypto.py`: `generate_api_key()`, `rate_limit_key()`, `get_hmac_key()`, `get_jwt_secret()`, `get_csrf_token()`, `get_session_salt()`
- **Fix**: `verify_password()` retorna `False` para inputs None/empty
- **Fix**: Import `os` en `security/crypto.py`
- Tests: 142/142

---

## v2.5.3 (2026-05-14)

### Monolith Split — 4 modulos
- **tpv_security.py** (234L) → `security/{crypto,validation,audit}.py`
- **output_validator.py** (257L) → `response_validators/{models,checks}.py`
- **license_manager.py** (316L) → `license/{helpers,core}.py`
- **diccionario_tpv.py** (247L) → `dictionary/{helpers,routes}.py`
- **Fixes**: `_SQLI_PATTERNS` migrado, decorators corregidos, shadowing resuelto
- Tests: 134/142

---

## v2.5.2 (2026-05-14)

### Module Migration — 3 modulos
- `agent_state.py` → `ia/state.py`
- `db_users.py` → `db/users.py` (re-export explicita de funciones privadas)
- `db_config_inventario.py` → `db/config_inventario.py` (imports actualizados)
- Tests: 142/142

---

## v2.5.1 (2026-05-14)

### App Cleanup
- `app.py`: 368 → 335 lineas (rutas duplicadas eliminadas)

### JS Split
- `tpv_estado_sync.js` (970L) → 3 archivos (persist, ui, backup)
- `smart_excel_importer.js` (1332L) → 2 archivos (core + compat)

### Metrics Fix
- `/dev/metricas` duplicado eliminado de `metrics/routes.py`
- Tests: 142/142
