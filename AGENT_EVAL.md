# 🧠 Evaluación del Agente IA — TPV Ultra Smart v8.0

## Puntuación actual: 6/10

---

## ✅ Fortalezas (lo que funciona bien)
1. **Arquitectura modular** — 36 archivos en `ia/`, bien separados por responsabilidad
2. **3 niveles de agente** (AgentMaster > AgentPro > AgentCore) con degradación elegante
3. **Handlers por rol** — respuestas diferenciadas para cliente/vendedor/supervisor/admin/dev
4. **Fuzzy match** — búsqueda difusa de productos sin dependencias externas
5. **Memoria avanzada** persistente en SQLite + contexto enriquecido
6. **Motor ReAct** para razonamiento multi-paso
7. **Anti-slop** — detecta y acorta respuestas genéricas repetidas
8. **Skills por dominio** — enriquecimiento contextual (finanzas, inventario, etc.)
9. **Chat proactivo** — avisa de stock crítico al abrir la app
10. **Acciones ejecutables** — el chat puede hacer backup, sincronizar, importar (con confirmación)

## ❌ Debilidades críticas encontradas

### 1. AgentPro devuelve DATOS FALSOS (hardcoded)
`agent_pro.py` líneas 78-108: responde con "$3,250", "12 transacciones", "89 productos" — 
**datos inventados**, no consulta la BD. Si AgentMaster falla, AgentPro toma el control
y engaña al usuario con números falsos.

### 2. Humanizer NO tiene método `enhance()`
`agent_master.py` llama `self.humanizer.enhance(resp, role)` en el paso 7, pero 
`humanizer.py` solo tiene `sanitize_text()` y `human_help()`. Esto causa una excepción
silenciada por el `try/except`, dejando la respuesta sin humanizar.

### 3. NLP Engine con solo 7 intenciones
El clasificador solo reconoce: FINANCE, STOCK, TRENDS, GREETING, OFFERS, SALES, RECOMMEND.
Faltan intenciones críticas: HELP, GOODBYE, PRODUCT_SEARCH, STOCK_QUERY, 
TOP_PRODUCTS, CATEGORIES, LOGIN, PAYMENT, HISTORY, SCHEDULE, LOYALTY, ABC, 
PREDICTIONS, ROTATION, EXPENSES, DASHBOARD, STATUS, EOQ.

### 4. Decoradores mal puestos en proactive_routes.py
`@login_required` está ANTES de `@proactive_bp.route(...)`, lo que significa que
el decorador se aplica a la función sin registrarla como ruta primero.

### 5. modules/agent.py redefine `requiere_login` localmente
Tiene su propia versión de `requiere_login` y `usuario_actual`, ignorando las
de `decorators.py`. Además tiene `@login_required` + `@requiere_login` en la
misma ruta (doble verificación redundante).

### 6. Catalog.py usa ruta DB incorrecta
`catalog.py` usa `DB_PATH = os.path.join(..., 'data', 'tpv.db')` — una ruta que
no existe. El catálogo P y O en handlers funcionan con otro mecanismo.

### 7. `agent_core.py` — saludo fijo "cafetería"
Dice "Bienvenido a nuestra cafetería ☕" — esto es para un TPV genérico, no una cafetería.

### 8. Sin intención STOCK_QUERY + CATEGORIES en agent_master
`_generate_response()` intenta manejar `STOCK_QUERY` y `CATEGORIES` pero el NLP
nunca las genera. Solo funcionan por el keyword fallback parcial.

---

## 🔧 Plan de fortalecimiento aplicado

### F1: NLP con 20+ intenciones
### F2: Humanizer con enhance() real
### F3: AgentPro conectado a BD real (eliminar datos fake)
### F4: Decoradores corregidos en proactive_routes y modules/agent
### F5: Nuevas intenciones: HELP, GOODBYE, STOCK_QUERY, TOP_PRODUCTS, etc.
