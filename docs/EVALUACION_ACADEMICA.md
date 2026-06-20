# Evaluación Académica — TPV Ultra Smart v8.0 Rev. 14

## Resumen Ejecutivo Honesto

| Métrica | Valor | Notas |
|---|---|---|
| Tests totales | **312 pasan / 9 skipped / 0 fallos** | Suite sana |
| Cobertura global | **32%** | Sobre 9,579 statements REALES |
| Cobertura módulos IA críticos | **60-89%** | agent_master 72%, guardrails_v2 89% |
| Cobertura backend crítico | **>75%** | auth 74%, db/users 87% |
| Endpoints API | **218 rutas** | 28 blueprints |
| Bugs críticos corregidos | **9** | Ver sección "Bugs Corregidos" |

## Por qué la cobertura global no es 95%

El proyecto tiene 195 archivos Python. La mayoría son:

- **Módulos de sincronización Supabase** (210+ stmts c/u) que requieren credenciales cloud
- **Módulos de telecomunicaciones** (347 stmts) que requieren hardware específico
- **Helpers de inventario y reportes** (238+ stmts) con muchos branches de edge cases

Una cobertura del 95% requeriría simular todos esos entornos, lo cual no es realista en el plazo de tesis. **La cobertura del 32% es honesta**: cubre los flujos críticos que un jurado puede verificar en una demo en vivo.

## Mejoras Cuantificables (Rev. 14 → Rev. 14)

### Bugs críticos corregidos

| # | Bug | Impacto | Test que lo valida |
|---|---|---|---|
| 1 | Frontend roto (commit b1c0e70) | WebView en blanco | `test_frontend_assets.py` |
| 2 | "Root Access al cajero" | Security leak | `test_saludo_cajero_no_dice_root_access` |
| 3 | Login cajero1 401 | E2E fallido | `test_login_rol[cajero1-cajero]` |
| 4 | Admin no puede crear cajero | API broken | `test_admin_crea_cajero` |
| 5 | Robot E2E credenciales incorrectas | E2E fallido | Manual |
| 6 | 6 endpoints CRUD faltantes | API incompleta | `test_flujos_comerciales.py` |
| 7 | Catalogo sync NameError | HTTP 500 | `test_catalogo_sync` |
| 8 | Stock display "Agotado" | UX rota | Manual |
| 9 | Usuarios fantasmas en BD | Datos sucios | `test_login_rol` |

### Cobertura IA mejorada

| Módulo | Antes | Ahora | Delta |
|---|---|---|---|
| `ia/agent_master.py` | 27% | **72%** | +45 ptos |
| `ia/guardrails_v2.py` | 0% | **89%** | +89 ptos |
| `modules/agent_chat_bp.py` | 27% | **78%** | +51 ptos |
| `ia/agent.py` | 70% | 70% | (mantenido) |
| `ia/handlers_staff.py` | 9% | 29% | +20 ptos |
| `ia/react_core.py` | 16% | 21% | +5 ptos |
| `modules/auth.py` | 71% | **74%** | +3 ptos |
| `db/users.py` | 86% | **87%** | +1 ptos |

### Tests nuevos (123 tests)

```
tests/ia/test_react_core.py           — 13 tests del motor ReAct
tests/ia/test_agent_master.py         — 27 tests del agente por rol
tests/ia/test_handlers_staff.py       — 14 tests handlers cajero/admin/dev
tests/ia/test_memory_core.py          — 9 tests CRUD memoria
tests/ia/test_guardrails_v2.py        — 23 tests SQLi/XSS/PII/rate-limit
tests/ia/test_agent_chat_e2e.py       — 17 tests E2E /api/agent/chat
tests/e2e/test_flujos_comerciales.py  — 24 tests login/venta/usuarios
```

## Robustez de la IA

### ✅ Lo que SÍ es robusto

- **Detección de SQLi/XSS/PII**: 23 tests con 5 payloads maliciosos de cada tipo
- **Rate limiting por usuario**: Bloquea tras 20 requests/min (validado)
- **Saludo seguro por rol**: Ninguna respuesta contiene "root access" ni credenciales
- **Degradación elegante**: Si ReAct falla, cae a modo catálogo sin crashear
- **Idempotencia de ventas**: `client_txn_id` evita doble cobro (test válido)
- **Validación de prompts maliciosos**: 6 tipos (jailbreak, PII, SQLi) detectados

### ⚠️ Lo que NO es robusto (reconocido en tesis)

- **Motor ReAct completo** (255 stmts): 21% cobertura. Ciclo Thought→Action→Observation no testeado end-to-end
- **Memoria persistente** (167 stmts): 15% cobertura. save/recall/search no validados en todos los paths
- **Anti-slop / humanizer**: No validan calidad de respuestas, solo seguridad
- **Sincronización Supabase**: No testeada (requiere credenciales cloud)

## Bugs Conocidos (transparencia académica)

### Bug #1: Frontend roto por commit "QA Pass 100%"
- **Commit**: b1c0e70 (17 Jun 2026)
- **Causa**: El commit reemplazó `templates/index.html` (122KB) por placeholder de 219B
- **Fix**: Restaurado desde commit `85fa56f`
- **Lección**: CI/CD debe validar tamaño de assets críticos

### Bug #2: "Root Access concedido" al cajero
- **Causa**: Saludo hardcodeado en `_saludo_inteligente()` sin aislar por sesión
- **Detección**: Reporte E2E `e2e_20260618_211205` mostró el leak
- **Fix**: Saludos neutros por rol + logging de mismatch
- **Test**: `test_saludo_cajero_no_dice_root_access`

### Bug #3: cajero1 desactivado tras tests
- **Causa**: Tests anteriores marcaban `activo=0` y `_init_db_if_empty` no reactivaba
- **Fix**: Reactivación forzada en cada arranque
- **Test**: `test_login_rol[cajero1-cajero]`

## Recomendación para Defensa

### Mostrar en demo (5 minutos)

1. **Splash profesional**: Logo con anillos girando + mesh gradient + 10 pasos
2. **Login `desarrollador (password en consola)`**: Botón 🩺 violeta aparece
3. **Debug panel**: Click 🩺 → logs en tiempo real
4. **Catálogo**: Stock real visible (no "Agotado")
5. **Crear producto**: Emoji 🧪 → aparece en catálogo
6. **Venta**: Items + pago → ticket con idempotencia
7. **Burbuja IA**: Arrastrar 💬 por pantalla + chat con "➤ Enviar"

### No destacar

- Cobertura global 32% (es honesta pero no impresionante)
- Módulos de sync Supabase (no testeables sin credenciales)
- Líneas de código totales (infladas por código legacy)

### Reconocer limitaciones (jurado valora honestidad)

- "Cobertura global 32% porque hay 80+ módulos que requieren entornos externos"
- "Motor ReAct 21% cobertura: el ciclo completo no está testeado end-to-end"
- "Sync Supabase no testeada: requiere credenciales cloud"

## Cómo reproducir

```bash
cd ~/tpv-chaquopy
python -m pytest tests/ tests/ia/ tests/e2e/ -v   # 312 tests
coverage run -m pytest tests/ia/ tests/e2e/ tests/backend/
coverage report -m                                  # Cobertura real
```

**Fecha de evaluación**: 2026-06-19
**Suite**: 312 passed / 9 skipped / 0 failed
