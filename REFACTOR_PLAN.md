# 🔧 Plan de Refactorización — TPV Ultra Smart v8.0
## Rama: `refactor/backend-pro`

---

## 📊 Diagnóstico del estado actual

| Métrica | Valor | Problema |
|---------|-------|----------|
| `app.py` | **1752 líneas, 72 rutas** | Archivo monolítico "god object" |
| Módulos duplicados | 14+ archivos | Misma lógica en raíz y en `modules/`, `db/`, `ia/` |
| Decoradores de auth | **2 sistemas** | `auth_decorator.py` y `decorators.py` hacen lo mismo |
| JS legacy | **10,957 líneas** | `app_3.js` a `app_8.js` — código muerto |
| Paquetes vacíos | `services/`, `utils/` | Solo tienen `__init__.py` vacío |
| Datos hardcoded | ~200 líneas | Catálogo fallback, recomendaciones, predicciones fake |
| Secret key | hardcoded | `'tpv-ultra-smart-v8-2026-nueva-sesion'` en texto plano |
| Catch-all route | silencia 404 | `@app.route('/api/<path:p>')` devuelve `ok: True` para todo |
| Auto-login bypass | activo | `/api/auth/me` auto-logea como desarrollador sin credenciales |
| Rutas duplicadas | 15+ rutas | `/api/state`, `/api/gastos`, `/api/usuarios`, etc. registradas dos veces |
| `_agent_loaded` | referenciada sin definir en scope si falla import | Crash potencial |

---

## 🎯 Plan de refactorización (5 fases)

### FASE 1: Extraer rutas de `app.py` → Blueprints (crítico)
**Objetivo**: Reducir `app.py` de 1752 → ~150 líneas (solo setup + registro)

- [ ] Mover rutas de catálogo → `modules/catalogo_bp.py`
- [ ] Mover rutas de ventas (registrar, hoy, cierre, totales) → ya están en `modules/sales.py`, eliminar duplicados
- [ ] Mover rutas de reportes → `modules/reportes_bp.py`
- [ ] Mover rutas de importación → `modules/import_bp.py`
- [ ] Mover rutas de herramientas IA → `modules/tools_bp.py`
- [ ] Mover rutas de clientes → `modules/clientes_bp.py`
- [ ] Mover rutas de diagnóstico → `modules/diag_bp.py`
- [ ] Mover rutas de privilegios/admin embebidas → usar las de `modules/admin_*`
- [ ] Mover login/logout/auth_me → `modules/auth.py` (ya existe parcialmente)
- [ ] Mover estado/config supabase → `modules/settings_bp.py`
- [ ] Eliminar catch-all `/api/<path:p>` o convertir en 404 real
- [ ] Eliminar catálogo fallback hardcoded (11 productos)

### FASE 2: Unificar módulos duplicados
- [ ] Fusionar `auth_decorator.py` + `decorators.py` → un solo `decorators.py`
- [ ] Eliminar `db_products.py` (facade de 10 líneas → importar directo)
- [ ] Eliminar `db_users.py` (facade de 7 líneas → importar directo)
- [ ] Eliminar `db_config.py` (facade de 12 líneas → importar directo)
- [ ] Eliminar `db_config_inventario.py` (facade de 2 líneas)
- [ ] Eliminar `ia_agent.py` (facade de 2 líneas)
- [ ] Eliminar `ai_routes.py` (facade de 3 líneas)
- [ ] Consolidar `database.py` (mega-facade de 30+ re-exports) → importaciones directas
- [ ] Eliminar `supabase_sync.py`/`supabase_rls.py` raíz → usar `sync/`
- [ ] Eliminar `security_*.py` raíz (5 archivos) → mover a `security/`
- [ ] Eliminar paquetes vacíos: `services/`, `utils/`

### FASE 3: Seguridad
- [ ] `secret_key` → leer de variable de entorno con fallback seguro
- [ ] Eliminar auto-login de desarrollador en `/api/auth/me`
- [ ] Convertir catch-all en 404 JSON real
- [ ] Quitar `pass` silencioso en inserción de ventas (línea del `try: except: pass`)

### FASE 4: Limpieza frontend
- [ ] Eliminar `app_3.js` a `app_8.js` (10,957 líneas de JS legacy/muerto)
- [ ] Verificar que `index.html` no los referencia

### FASE 5: Tests y validación
- [ ] Verificar que los tests existentes siguen pasando
- [ ] Actualizar imports en tests que usan `database.py` o facades
- [ ] Agregar test de smoke para la nueva estructura

---

## 📁 Estructura objetivo

```
app/src/main/python/
├── app.py                    (~150 líneas: Flask app + registro de blueprints)
├── start_server.py           (sin cambios)
├── decorators.py             (unificado: login_required, requiere_login, etc.)
├── db_connection.py          (sin cambios, es el core DAO)
├── db_ventas.py              (sin cambios, lógica real)
├── db_config_licencias.py    (sin cambios, lógica real)
├── db_config_sync.py         (sin cambios, lógica real)
├── db/                       (esquema + DAOs)
├── ia/                       (agente IA)
├── modules/                  (TODOS los blueprints)
│   ├── auth.py
│   ├── catalogo_bp.py        (NUEVO - extraído de app.py)
│   ├── clientes_bp.py        (NUEVO)
│   ├── diag_bp.py            (NUEVO)
│   ├── import_bp.py          (NUEVO)
│   ├── reportes_bp.py        (NUEVO)
│   ├── tools_bp.py           (NUEVO)
│   ├── sales.py
│   ├── inventory.py
│   ├── ...
├── models/
├── security/                 (consolidado)
├── sync/
├── tools/
├── license/
├── metrics/
└── tests/
```
