"""AgentMaster - Agente IA del TPV Ultra Smart v8.0
Integra: memoria avanzada, ReAct reasoning, handlers por rol,
fuzzy match, skills, role guidance, metricas, guide manager y state."""
import json, random, time, logging
from datetime import datetime
from ia.nlp_engine import NLPEngine
from ia.tool_system import TOOLS
from ia.humanizer import Humanizer

# --- Modulos avanzados con importacion segura ---
# Memoria avanzada (SQLite persistente)
try:
    from ia.memory_advanced import (
        extract_and_save, get_enriched_context, get_summary as mem_summary,
        cleanup as mem_cleanup, recall, search as mem_search,
        forget as mem_forget, save as mem_save, init as mem_init
    )
    _HAS_ADV_MEMORY = True
except Exception:
    _HAS_ADV_MEMORY = False

# Motor ReAct para razonamiento complejo
try:
    from ia.react_core import ReActEngine
    _HAS_REACT = True
except Exception:
    _HAS_REACT = False

# Handlers especializados por rol
try:
    from ia.handlers import (
        handle_cliente, handle_vendedor, handle_supervisor,
        handle_admin, handle_dev
    )
    _HAS_HANDLERS = True
except Exception:
    _HAS_HANDLERS = False

if not _HAS_HANDLERS:
    try:
        from ia.handlers_cliente import handle_cliente
        from ia.handlers_staff import handle_vendedor, handle_supervisor, handle_admin, handle_dev
        _HAS_HANDLERS = True
    except Exception:
        _HAS_HANDLERS = False

# Fuzzy match para busqueda de productos
try:
    from ia.fuzzy_match import fuzzy_score, best_match, quick_search, contains_frustration
    _HAS_FUZZY = True
except Exception:
    _HAS_FUZZY = False

# Skills (enriquecimiento de respuestas por dominio)
try:
    from ia.skills import get_registry as get_skill_registry
    _HAS_SKILLS = True
except Exception:
    _HAS_SKILLS = False

# Role guidance (misiones y guias por rol)
try:
    from ia.role_guidance import ROLE_MISSIONS, SCREEN_GUIDES
    _HAS_ROLE_GUIDANCE = True
except Exception:
    _HAS_ROLE_GUIDANCE = False

# Guide manager (guia contextual)
try:
    from ia.guide_manager import GuideManager
    _HAS_GUIDE = True
except Exception:
    _HAS_GUIDE = False

# Metricas financieras y analiticas
try:
    from ia.metrics import F, M
    _HAS_METRICS = True
except Exception:
    _HAS_METRICS = False

# State management (sesiones de agente persistentes)
try:
    from ia.state import create_session, get_session, update_step, complete_session, get_active_sessions
    _HAS_STATE = True
except Exception:
    _HAS_STATE = False

logger = logging.getLogger(__name__)


class AgentMaster:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS
        # Memoria basica (fallback si memoria avanzada no esta disponible)
        self.sessions = {}

        # Inicializar memoria avanzada
        self.adv_memory_ok = _HAS_ADV_MEMORY
        if self.adv_memory_ok:
            try:
                mem_init()
                logger.info("[AgentMaster] Memoria avanzada (SQLite) activa")
            except Exception as e:
                self.adv_memory_ok = False
                logger.warning("[AgentMaster] Memoria avanzada no disponible: %s", e)

        # Motor ReAct
        self.react_engine = None
        if _HAS_REACT:
            try:
                self.react_engine = ReActEngine()
                logger.info("[AgentMaster] Motor ReAct cargado (%d herramientas)",
                            self.react_engine.get_status().get('tools_loaded', 0))
            except Exception as e:
                logger.warning("[AgentMaster] ReAct no disponible: %s", e)

        # Skills registry
        self.skill_registry = None
        if _HAS_SKILLS:
            try:
                self.skill_registry = get_skill_registry()
                logger.info("[AgentMaster] Skills registry activo (%d skills)",
                            len(self.skill_registry.skills))
            except Exception as e:
                logger.warning("[AgentMaster] Skills no disponible: %s", e)

        # Guide manager (se inicializa por rol al procesar)
        self._guide_managers = {}

        # Metricas de uso del IA (contador en memoria)
        self._usage_metrics = {
            'total_queries': 0,
            'by_role': {},
            'by_intent': {},
            'by_hour': {},
            'start_time': datetime.now().isoformat(),
            'errors': 0,
            'avg_response_time_ms': 0,
            '_total_time_ms': 0
        }

        # Mapa de roles a iconos
        self.role_icons = {
            'desarrollador': '🔧', 'administrador': '📊',
            'supervisor': '👁️', 'vendedor': '💼',
            'cajero': '💵', 'cliente': '🛍️'
        }

        # Privilegios por rol
        self.privilegios = {
            'desarrollador': ['sistema', 'seguridad', 'usuarios', 'privilegios', 'bd', 'logs', 'ventas', 'inventario', 'productos', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'administrador': ['ventas', 'inventario', 'productos', 'usuarios', 'reportes', 'metricas', 'catalogo', 'clientes'],
            'supervisor': ['ventas', 'productos', 'reportes', 'metricas', 'catalogo'],
            'vendedor': ['ventas', 'catalogo', 'clientes'],
            'cajero': ['ventas', 'catalogo']
        }

        # Handlers por rol
        self._role_handlers = {}
        if _HAS_HANDLERS:
            self._role_handlers = {
                'cliente': handle_cliente,
                'vendedor': handle_vendedor,
                'supervisor': handle_supervisor,
                'administrador': handle_admin,
                'desarrollador': handle_dev,
            }

        logger.info("[AgentMaster] v8.0 inicializado - Memoria:%s ReAct:%s Handlers:%s Fuzzy:%s Skills:%s RoleGuide:%s Metrics:%s State:%s",
                    self.adv_memory_ok, _HAS_REACT, _HAS_HANDLERS, _HAS_FUZZY,
                    _HAS_SKILLS, _HAS_ROLE_GUIDANCE, _HAS_METRICS, _HAS_STATE)

    # ----------------------------------------------------------------
    # Metodo principal: procesar mensaje del usuario
    # ----------------------------------------------------------------
    def process(self, text, role='vendedor', user_name='', session_id=None):
        t_start = time.time()
        if not session_id:
            session_id = f"sess_{random.randint(100000, 999999)}"

        icon = self.role_icons.get(role, '🤖')
        poderes = self.privilegios.get(role, ['catalogo', 'ventas'])

        # 1. Recuperar contexto enriquecido de memoria avanzada
        enriched_ctx = {}
        if self.adv_memory_ok:
            try:
                enriched_ctx = get_enriched_context(session_id, text or '')
            except Exception:
                enriched_ctx = {}

        # 2. Busqueda rapida de productos en BD (con fuzzy match)
        product_results = None
        if text and len(text) > 2:
            product_results = self._search_products(text, role, icon)

        # 3. Detectar intencion (NLP + fallback keywords)
        intent, conf = self.nlp.predict_intent(text) if text else (None, 0)
        # Fallback con keywords si NLP tiene baja confianza
        if not intent or conf < 0.6:
            intent, conf = self._keyword_fallback(text)
        intent_str = str(intent) if intent else ''

        # 4. Buscar herramientas relevantes
        tools = self._find_relevant_tools(text, role)

        # 5. Generar respuesta
        resp = self._generate_response(
            text, intent_str, role, user_name, icon, poderes, tools,
            product_results, enriched_ctx, session_id
        )

        # 6. Enriquecer respuesta con Skills
        if self.skill_registry:
            try:
                resp = self.skill_registry.enrich_response(resp, text or '', role, context=enriched_ctx)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        # 7. Humanizar respuesta
        try:
            resp = self.humanizer.enhance(resp, role)
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        # 8. Sanitizar texto
        try:
            resp = self.humanizer.sanitize_text(resp)
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        # 9. Guardar en memoria avanzada
        if self.adv_memory_ok:
            try:
                extract_and_save(session_id, text or '', intent_str, resp[:200], role)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        # 10. Guardar en memoria basica (fallback)
        self.sessions[session_id] = {
            "text": text, "role": role,
            "time": datetime.now().isoformat(),
            "intent": intent_str
        }

        # 11. Registrar metricas de uso
        elapsed_ms = (time.time() - t_start) * 1000
        self._record_metrics(role, intent_str, elapsed_ms)

        return {
            'response': resp,
            'intent': str(intent),
            'confidence': conf,
            'role': role,
            'privilegios': poderes,
            'tools': tools,
            'session_id': session_id
        }

    # ----------------------------------------------------------------
    # Busqueda de productos con fuzzy match
    # ----------------------------------------------------------------
    def _search_products(self, text, role, icon):
        """Busca productos en BD, usando fuzzy match si no hay resultado exacto."""
        # Intento 1: busqueda SQL directa
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            c = conn.cursor()
            c.execute(
                "SELECT nombre, precio, unidad_medida, COALESCE("
                "(SELECT stock_actual FROM inventario_general "
                "WHERE producto_id=p.producto_id), 0) "
                "FROM productos p WHERE activo=1 AND nombre LIKE ?",
                (f"%{text}%",)
            )
            rows = c.fetchall()
            conn.close()
            if rows:
                items = [f"{r[0]}: ${r[1]:.2f} ({r[3]} {r[2]})" for r in rows[:5]]
                return {'response': f"{icon} Productos encontrados:\n" + "\n".join(f"  📦 {item}" for item in items), 'exact': True}
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        # Intento 2: fuzzy match si no hubo resultado exacto
        if _HAS_FUZZY:
            try:
                # Obtener nombres de productos de BD para fuzzy matching
                product_names = self._get_product_names()
                if product_names:
                    match, score = best_match(text, product_names, threshold=55)
                    if match:
                        # Buscar el producto coincidente en BD
                        try:
                            from db_connection import obtener_conexion
                            conn = obtener_conexion()
                            c = conn.cursor()
                            c.execute(
                                "SELECT nombre, precio, unidad_medida, COALESCE("
                                "(SELECT stock_actual FROM inventario_general "
                                "WHERE producto_id=p.producto_id), 0) "
                                "FROM productos p WHERE activo=1 AND nombre LIKE ?",
                                (f"%{match}%",)
                            )
                            rows = c.fetchall()
                            conn.close()
                            if rows:
                                items = [f"{r[0]}: ${r[1]:.2f} ({r[3]} {r[2]})" for r in rows[:5]]
                                return {
                                    'response': f"{icon} Quisiste decir:\n" + "\n".join(f"  📦 {item}" for item in items),
                                    'exact': False, 'fuzzy_score': score
                                }
                        except Exception:  # noqa: broad-except - graceful degradation
                            pass
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        return None

    def _get_product_names(self):
        """Obtiene lista de nombres de productos para fuzzy matching."""
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            c = conn.cursor()
            c.execute("SELECT nombre FROM productos WHERE activo=1")
            rows = c.fetchall()
            conn.close()
            return [r[0] for r in rows] if rows else []
        except Exception:
            return []

    # ----------------------------------------------------------------
    # Fallback de deteccion de intencion por keywords
    # ----------------------------------------------------------------
    def _keyword_fallback(self, text):
        """Fallback: detecta intención por keywords cuando NLP tiene baja confianza."""
        if not text:
            return None, 0
        tl = text.lower()
        # Orden: más específico primero
        _MAP = [
            ('STOCK_QUERY', ['cuanto hay de', 'stock de', 'quedan de', 'tengo de', 'existencia de']),
            ('TOP_PRODUCTS', ['top productos', 'mas vendidos', 'productos estrella']),
            ('ABC', ['analisis abc', 'pareto', 'clasificacion abc']),
            ('EOQ', ['eoq', 'lote optimo', 'pedido optimo']),
            ('PREDICTIONS', ['prediccion', 'pronostico', 'proyeccion', 'forecast']),
            ('ROTATION', ['rotacion', 'indice rotacion']),
            ('EXPENSES', ['gastos', 'egresos', 'costos fijos']),
            ('DASHBOARD', ['dashboard', 'resumen', 'estado general', 'kpi']),
            ('CATEGORIES', ['categorias', 'catalogo', 'secciones', 'que tienen']),
            ('LOYALTY', ['puntos', 'lealtad', 'fidelidad', 'recompensa']),
            ('HISTORY', ['historial', 'compras', 'recibo', 'factura']),
            ('LOGIN', ['login', 'iniciar sesion', 'entrar', 'contrasena']),
            ('PAYMENT', ['metodo pago', 'pagar', 'efectivo', 'tarjeta', 'cobrar']),
            ('SYSTEM', ['estado sistema', 'logs', 'debug', 'errores']),
            ('BACKUP', ['respaldo', 'backup', 'copia seguridad']),
            ('RECOMMEND', ['recomiendame', 'recomendar', 'sugerir', 'sugerencia']),
            ('STOCK', ['stock', 'inventario', 'critico', 'agotado', 'reabastecer']),
            ('FINANCE', ['finanza', 'balance', 'ganancia', 'margen', 'ingreso']),
            ('SALES', ['venta', 'cuanto vendi', 'caja', 'facturacion']),
            ('OFFERS', ['oferta', 'descuento', 'rebaja', 'promo']),
            ('TRENDS', ['top', 'mas vendido', 'ranking', 'popular', 'tendencia']),
            ('HELP', ['ayuda', 'que puedes', 'opciones', 'menu', 'como funciona']),
            ('GOODBYE', ['adios', 'hasta luego', 'chao', 'nos vemos', 'bye']),
            ('GREETING', ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos']),
        ]
        for intent, keywords in _MAP:
            if any(kw in tl for kw in keywords):
                return intent, 0.75
        return None, 0

    # ----------------------------------------------------------------
    # Busqueda de herramientas relevantes
    # ----------------------------------------------------------------
    def _find_relevant_tools(self, text, role):
        """Encuentra herramientas del tool_system relevantes al texto y rol."""
        tools = []
        if not text:
            return tools
        text_low = text.lower()
        for tname, tinfo in self.tools.items():
            if role in tinfo.get('roles', []):
                if any(kw in text_low for kw in tinfo.get('keywords', [])):
                    tools.append({
                        'name': tname,
                        'icon': tinfo.get('icon', '🔧'),
                        'desc': tinfo.get('desc', '')
                    })
        return tools

    # ----------------------------------------------------------------
    # Generar respuesta (usa handlers si disponibles, sino fallback)
    # ----------------------------------------------------------------
    def _generate_response(self, text, intent, role, name, icon, poderes, tools,
                           product_results, enriched_ctx, session_id):
        """Genera la respuesta usando handlers especializados o fallback."""

        # Si hay resultado de busqueda de productos directo, usarlo
        if product_results and product_results.get('exact'):
            return product_results['response']

        # Intentar usar handler especializado por rol
        if _HAS_HANDLERS and role in self._role_handlers:
            try:
                handler = self._role_handlers[role]
                # Firma de los handlers: (agent, text, name). handle_admin y
                # handle_dev usan el 3er arg como NOMBRE del usuario; vendedor y
                # supervisor lo ignoran. Antes se pasaba un dict y se imprimía crudo.
                result = handler(self, text or '', name or '')
                if result and len(result.strip()) > 5:
                    # Agregar contexto de memoria si hay datos del cliente
                    if enriched_ctx and enriched_ctx.get('client_data'):
                        client_name = enriched_ctx['client_data'].get('nombre')
                        if client_name and client_name not in result:
                            result = result.replace('Bienvenido', f'Bienvenido de vuelta, {client_name}', 1)
                    return result
            except Exception as e:
                logger.debug("[AgentMaster] Handler '%s' fallo: %s, usando fallback", role, e)

        # Fallback: generar respuesta con logica interna
        return self._respond_fallback(text, intent, role, name, icon, poderes, tools,
                                      product_results, enriched_ctx)

    def _respond_fallback(self, text, intent, role, name, icon, poderes, tools,
                          product_results, enriched_ctx):
        """Respuesta de fallback cuando no hay handlers disponibles."""
        nombre = name or role.capitalize()

        # Si fuzzy match encontro algo
        if product_results and not product_results.get('exact'):
            return product_results['response']

        # Usar role guidance para saludo contextual
        if 'GREETING' in intent or not text:
            priv = ', '.join(poderes[:6])
            greeting = f"{icon} ¡Hola {nombre}! Bienvenido al TPV.\n\nTu rol: {role}\nAcceso a: {priv}\n"
            # Agregar mision contextual del rol
            if _HAS_ROLE_GUIDANCE:
                try:
                    from datetime import datetime as _dt
                    h = _dt.now().hour
                    state = "inicio" if h < 9 else "operativo" if h < 18 else "cierre"
                    missions = ROLE_MISSIONS.get(role, ROLE_MISSIONS.get('cliente', {}))
                    mission = missions.get(state, missions.get('operativo', []))
                    if mission:
                        import random as _rnd
                        greeting += f"\n💡 {_rnd.choice(mission)}\n"
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
            return greeting + "\n¿En qué puedo ayudarte?"

        if 'FINANCE' in intent:
            if 'ventas' in poderes or 'reportes' in poderes:
                # Usar metricas reales si disponibles
                if _HAS_METRICS:
                    try:
                        d = F.diario()
                        prof = d['r'] - d['g']
                        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
                        return (f"{icon} Balance Financiero:\n"
                                f"💰 Ventas hoy: ${d['r']:,.2f} ({d['t']} transacciones)\n"
                                f"📊 Gastos: ${d['g']:,.2f}\n"
                                f"📈 Margen: {margen:.1f}%\n"
                                f"💵 Ganancia: ${prof:,.2f}")
                    except Exception:  # noqa: broad-except - graceful degradation
                        pass
                try:
                    d = F.diario()
                    return f"{icon} Balance Financiero:\n💰 Ventas hoy: ${d['r']:,.2f} ({d['t']} transacciones)\n📊 Ticket promedio: ${d['a']:,.2f}\n💵 Gastos: ${d['g']:,.2f}\n📈 Neto: ${d['r']-d['g']:,.2f}"
                except Exception:
                    return f"{icon} No hay datos financieros disponibles aún. Registre ventas para ver el balance."
            return f"{icon} No tienes acceso a finanzas con tu rol actual."

        if 'STOCK' in intent:
            if 'inventario' in poderes or 'catalogo' in poderes:
                if _HAS_METRICS:
                    try:
                        r = F.stock_resumen()
                        crit = F.stock_critico()
                        total = r['total'] if not hasattr(r, 'keys') else r['total']
                        agot = r['agotados']; criticos = r['criticos']; unid = r['unidades'] or 0
                        msg = (f"{icon} Inventario (datos reales):\n"
                               f"📦 {total} productos · {unid:.0f} unidades\n"
                               f"🔴 Agotados: {agot} · 🟡 Críticos: {criticos}\n")
                        if crit:
                            items = ', '.join(f"{c['nombre']} ({c['stock_actual']:.0f}u)" for c in crit[:5])
                            msg += f"\n⚠️ Atención: {items}"
                        else:
                            msg += "\n✅ Todo el stock está por encima del mínimo."
                        return msg
                    except Exception:  # noqa: broad-except - graceful degradation
                        pass
                return f"{icon} Inventario: usa la pestaña Inventario para ver el detalle."
            return f"{icon} No tienes acceso al inventario con tu rol actual."

        if 'SALES' in intent:
            if 'ventas' in poderes:
                if _HAS_METRICS:
                    try:
                        d = F.diario()
                        return (f"{icon} Ventas Hoy:\n🛒 {d['t']} transacciones | ${d['r']:,.2f}\n"
                                f"📊 Promedio: ${d['a']:,.2f}")
                    except Exception:  # noqa: broad-except - graceful degradation
                        pass
                try:
                    d = F.diario()
                    return f"{icon} Ventas Hoy:\n🛒 {d['t']} transacciones | ${d['r']:,.2f}\n📊 Promedio: ${d['a']:,.2f}"
                except Exception:
                    return f"{icon} Sin datos de ventas disponibles."
            try:
                d = F.diario()
                return f"{icon} Hoy: {d['t']} ventas por ${d['r']:,.2f}. ¿Registramos una nueva?"
            except Exception:
                return f"{icon} ¿Registramos una venta?"

        if 'TOP_PRODUCTS' in intent:
            if _HAS_METRICS:
                try:
                    top = F.top(dias=7, lim=5)
                    if top:
                        lst = '\n'.join(f"  {i+1}. {t['nombre']} — {t['q']:.0f} uds (${t['t']:,.2f})"
                                        for i, t in enumerate(top))
                        return f"{icon} Top productos (últimos 7 días):\n{lst}"
                    return f"{icon} Aún no hay ventas suficientes esta semana para un ranking."
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
        if 'CATEGORIES' in intent or 'categoria' in (text or '').lower():
            if _HAS_METRICS:
                try:
                    cats = F.categorias()
                    if cats:
                        lst = '\n'.join(f"  • {c['cat']}: {c['n']} productos (${(c['valor'] or 0):,.2f})"
                                        for c in cats[:8])
                        return f"{icon} Categorías del catálogo:\n{lst}"
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
        # Consulta de stock de un producto concreto ("cuanto hay de X")
        if 'STOCK_QUERY' in intent and _HAS_METRICS:
            try:
                import re as _re
                m = _re.search(r'(?:hay de|stock de|quedan de|cuanto hay de|tengo de)\s+(.+)', (text or '').lower())
                term = (m.group(1).strip() if m else '')
                if term:
                    res = F.buscar_stock(term)
                    if res:
                        lst = '\n'.join(f"  {r['nombre']}: {r['stock_actual']:.0f} uds (${r['precio_venta']:,.2f})"
                                        for r in res[:6])
                        return f"{icon} Stock de '{term}':\n{lst}"
                    return f"{icon} No encontré productos que coincidan con '{term}'."
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        if 'RECOMMEND' in intent or 'OFFERS' in intent:
            if _HAS_METRICS:
                try:
                    top = F.top(dias=7, lim=3)
                    if top:
                        estrella = top[0]['nombre']
                        return (f"{icon} Recomendaciones (según ventas reales):\n"
                                f"⭐ Más vendido: {estrella}\n"
                                f"📈 También destacan: " + ', '.join(t['nombre'] for t in top[1:3]) +
                                f"\n💡 Considera ofertas en productos de baja rotación.")
                except Exception:  # noqa: broad-except - graceful degradation
                    pass
            return f"{icon} Recomendaciones: revisa el Dashboard para ver tendencias de venta."

        if tools:
            tlist = '\n'.join([f"  {t['icon']} {t['name']}: {t['desc'][:80]}" for t in tools[:4]])
            return f"{icon} Herramientas disponibles:\n\n{tlist}"

        return f"{icon} Como {role}, puedes: {', '.join(poderes[:5])}.\n\n¿Qué necesitas?"

    # ----------------------------------------------------------------
    # Razonamiento ReAct para consultas complejas
    # ----------------------------------------------------------------
    def react_query(self, query, plan_name=None, role='vendedor'):
        """Usa el motor ReAct para consultas complejas multi-paso."""
        if not self.react_engine:
            return {'success': False, 'error': 'Motor ReAct no disponible'}
        try:
            if plan_name:
                result = self.react_engine.execute_plan(plan_name=plan_name, context={'role': role})
            else:
                # Buscar la herramienta mas relevante
                result = self.react_engine._call_by_search(query, params={'role': role})
            return result
        except Exception as e:
            logger.error("[AgentMaster] ReAct error: %s", e)
            return {'success': False, 'error': str(e)}

    # ----------------------------------------------------------------
    # Guia contextual (Guide Manager)
    # ----------------------------------------------------------------
    def get_guide(self, role='cliente', screen_id=None):
        """Obtiene guia contextual para el rol y pantalla actual."""
        if _HAS_GUIDE:
            try:
                if role not in self._guide_managers:
                    self._guide_managers[role] = GuideManager(user_role=role)
                return self._guide_managers[role].get_contextual_guide(screen_id)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        # Fallback basico
        if _HAS_ROLE_GUIDANCE:
            try:
                missions = ROLE_MISSIONS.get(role, ROLE_MISSIONS.get('cliente', {}))
                suggestions = missions.get('operativo', ['Estoy aqui para ayudarle.'])
                return f"🤖 {random.choice(suggestions)}"
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        return "🤖 ¿En qué puedo ayudarle?"

    # ----------------------------------------------------------------
    # Metricas de uso del IA
    # ----------------------------------------------------------------
    def _record_metrics(self, role, intent, elapsed_ms):
        """Registra metricas de uso de la IA."""
        m = self._usage_metrics
        m['total_queries'] += 1
        m['by_role'][role] = m['by_role'].get(role, 0) + 1
        if intent:
            m['by_intent'][intent] = m['by_intent'].get(intent, 0) + 1
        hour = datetime.now().strftime('%H')
        m['by_hour'][hour] = m['by_hour'].get(hour, 0) + 1
        m['_total_time_ms'] += elapsed_ms
        m['avg_response_time_ms'] = round(m['_total_time_ms'] / m['total_queries'], 1)

    def get_metrics(self):
        """Devuelve metricas de uso de la IA."""
        m = dict(self._usage_metrics)
        # Limpiar campo interno
        m.pop('_total_time_ms', None)
        m['uptime_seconds'] = (datetime.now() - datetime.fromisoformat(m['start_time'])).total_seconds()
        return m

    # ----------------------------------------------------------------
    # Estado de los modulos IA
    # ----------------------------------------------------------------
    def get_status(self):
        """Devuelve el estado de todos los modulos IA conectados."""
        status = {
            'version': '8.0.0',
            'modules': {
                'nlp_engine': True,
                'tool_system': bool(self.tools),
                'humanizer': True,
                'memory_advanced': self.adv_memory_ok,
                'memory_basic': bool(self.sessions),
                'react_core': self.react_engine is not None,
                'handlers': _HAS_HANDLERS,
                'fuzzy_match': _HAS_FUZZY,
                'skills': self.skill_registry is not None,
                'role_guidance': _HAS_ROLE_GUIDANCE,
                'guide_manager': _HAS_GUIDE,
                'metrics': _HAS_METRICS,
                'state': _HAS_STATE,
            },
            'tools_count': len(self.tools),
            'sessions_active': len(self.sessions),
            'handlers_roles': list(self._role_handlers.keys()) if _HAS_HANDLERS else [],
        }
        if self.react_engine:
            try:
                status['react_status'] = self.react_engine.get_status()
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        if self.skill_registry:
            try:
                status['skills_count'] = len(self.skill_registry.skills)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        return status

    # ----------------------------------------------------------------
    # Operaciones de memoria avanzada
    # ----------------------------------------------------------------
    def get_memory(self, session_id='default', category=None, limit=20):
        """Recupera recuerdos de la memoria avanzada."""
        if self.adv_memory_ok:
            try:
                return recall(session_id, category=category, limit=limit)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        # Fallback: memoria basica
        return self.sessions.get(session_id, {})

    def clear_memory(self, session_id='default', category=None):
        """Limpia la memoria de una sesion."""
        if self.adv_memory_ok:
            try:
                return mem_forget(session_id, category=category)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        # Fallback: memoria basica
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_memory_summary(self, session_id='default'):
        """Resumen de la memoria de una sesion."""
        if self.adv_memory_ok:
            try:
                return mem_summary(session_id)
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        return {'total': len(self.sessions), 'categories': {}}

    # ----------------------------------------------------------------
    # Busqueda difusa de productos (endpoint)
    # ----------------------------------------------------------------
    def fuzzy_search_products(self, query, threshold=55):
        """Busqueda difusa de productos por nombre."""
        if not _HAS_FUZZY:
            return {'results': [], 'error': 'Fuzzy match no disponible'}
        product_names = self._get_product_names()
        if not product_names:
            return {'results': [], 'query': query}
        try:
            # Busqueda rapida con indice invertido
            from ia.fuzzy_match import build_index
            build_index(product_names)
            match, score = quick_search(query, threshold=threshold)
            if match:
                return {'results': [{'name': match, 'score': round(score, 1)}], 'query': query}
            return {'results': [], 'query': query}
        except Exception as e:
            return {'results': [], 'query': query, 'error': str(e)}


# ══════════════════════════════════════════════════════════════
#  AGENTE FALLBACK (antes ia/agent_pro.py — unificado aquí, #6)
#  Se usa cuando AgentMaster no puede inicializarse.
# ══════════════════════════════════════════════════════════════
from ia.tool_system import suggest_tools  # noqa: E402

# Helpers para obtener datos reales
def _datos_reales():
    """Obtiene métricas reales de la BD."""
    try:
        from ia.db_utils import q
        d = q("SELECT COUNT(*) t, COALESCE(SUM(total),0) r, COALESCE(AVG(total),0) a "
              "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        p = q("SELECT COUNT(*) n FROM productos WHERE activo=1", one=True)
        sb = q("SELECT COUNT(*) n FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0", one=True)
        return {
            'ventas_hoy': d['t'] if d else 0,
            'ingresos_hoy': d['r'] if d else 0,
            'promedio': d['a'] if d else 0,
            'productos': p['n'] if p else 0,
            'stock_bajo': sb['n'] if sb else 0,
        }
    except Exception:
        return {'ventas_hoy': 0, 'ingresos_hoy': 0, 'promedio': 0,
                'productos': 0, 'stock_bajo': 0}

def _fmt(n):
    """Formatea número como moneda."""
    try:
        return f"${n:,.2f}"
    except Exception:
        return f"${n}"


class AgentPro:
    def __init__(self):
        self.nlp = NLPEngine()
        self.humanizer = Humanizer()
        self.tools = TOOLS

        self.personalities = {
            'desarrollador': {'name': 'Neo', 'emoji': '🧠'},
            'administrador': {'name': 'Athena', 'emoji': '🦉'},
            'supervisor': {'name': 'Ares', 'emoji': '⚔️'},
            'vendedor': {'name': 'Hermes', 'emoji': '💚'},
            'cajero': {'name': 'Iris', 'emoji': '💵'},
        }

    def process(self, text, role='cliente', user_name=''):
        session_id = f"sess_{random.randint(100000, 999999)}"
        p = self.personalities.get(role, {'name': 'Asistente', 'emoji': '🤖'})
        e = p['emoji']

        # Detectar intención
        intent, confidence = self.nlp.predict_intent(text) if text else (None, 0)
        intent_str = str(intent) if intent else ''

        # Buscar herramientas relevantes
        tools = suggest_tools(text, role) if text else []

        # Obtener datos reales
        datos = _datos_reales()

        # Generar respuesta con datos REALES
        if 'GREETING' in intent_str:
            saludo = self.humanizer.time_greeting()
            nombre = user_name or role
            resp = (f"{e} {saludo} {nombre}! Soy {p['name']}, tu asistente. "
                    f"Tienes {datos['productos']} productos activos"
                    f"{f' y {datos['stock_bajo']} con stock bajo' if datos['stock_bajo'] else ''}. "
                    f"¿En qué te ayudo?")

        elif 'FINANCE' in intent_str:
            resp = (f"{e} Balance del día:\n"
                    f"💰 Ingresos: {_fmt(datos['ingresos_hoy'])}\n"
                    f"🛒 Ventas: {datos['ventas_hoy']} transacciones\n"
                    f"📊 Ticket promedio: {_fmt(datos['promedio'])}\n"
                    f"📦 Productos activos: {datos['productos']}\n"
                    f"⚠️ Stock bajo: {datos['stock_bajo']}")

        elif 'STOCK' in intent_str:
            try:
                from ia.db_utils import q
                criticos = q("SELECT nombre, stock_actual FROM inventario_general "
                             "WHERE stock_actual<=5 ORDER BY stock_actual LIMIT 8")
                if criticos:
                    lst = '\n'.join(f"  {'🔴' if r['stock_actual']<=2 else '🟡'} "
                                    f"{r['nombre']}: {int(r['stock_actual'])} uds"
                                    for r in criticos)
                    resp = f"{e} Stock que necesita atención:\n{lst}"
                else:
                    resp = f"{e} ✅ Todo el inventario está en niveles saludables."
            except Exception:
                resp = f"{e} {datos['stock_bajo']} productos con stock bajo."

        elif 'SALES' in intent_str:
            resp = (f"{e} Ventas de hoy:\n"
                    f"🛒 {datos['ventas_hoy']} transacciones\n"
                    f"💰 Total: {_fmt(datos['ingresos_hoy'])}\n"
                    f"📊 Promedio: {_fmt(datos['promedio'])}")

        elif 'RECOMMEND' in intent_str or 'OFFERS' in intent_str:
            try:
                from ia.metrics import F
                top = F.top(dias=7, lim=3)
                if top:
                    lst = '\n'.join(f"  ⭐ {t['nombre']}: {int(t['q'])} uds ({_fmt(t['t'])})"
                                    for t in top)
                    resp = f"{e} Recomendaciones basadas en ventas reales:\n{lst}"
                else:
                    resp = f"{e} Aún no hay suficientes ventas para recomendaciones. ¡A vender!"
            except Exception:
                resp = f"{e} Consulta el Dashboard para ver tendencias."

        elif 'GOODBYE' in intent_str:
            resp = f"{e} ¡Hasta luego{', ' + user_name if user_name else ''}! 👋"

        elif 'HELP' in intent_str:
            resp = (f"{e} Soy {p['name']}. Puedo ayudarte con:\n"
                    f"💰 Finanzas y balances\n📦 Inventario y stock\n"
                    f"🛒 Ventas y reportes\n⭐ Recomendaciones\n"
                    f"📊 Métricas y KPIs\n\n¿Qué necesitas?")

        elif tools:
            tools_list = '\n'.join(f"  {t['icon']} {t['name']}: {t['desc'][:60]}" for t in tools[:4])
            resp = f"{e} Herramientas relevantes:\n\n{tools_list}\n\n¿Profundizamos en alguna?"

        else:
            resp = self.humanizer.human_help(role)
            resp = f"{e} {resp}"

        # Humanizar
        resp = self.humanizer.enhance(resp, role)

        return {
            'response': resp,
            'intent': intent_str,
            'confidence': confidence,
            'role': role,
            'tools': tools[:4],
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
        }


# Alias de compatibilidad: el fallback se expone con el mismo nombre
AgentFallback = AgentPro

def _crear_agente():
    """Instancia AgentMaster; si falla, usa el fallback AgentPro."""
    try:
        a = AgentMaster()
        logger.info("[ia] Agente principal: AgentMaster")
        return a
    except Exception as e:  # noqa: broad-except - fallback controlado
        logger.warning("[ia] AgentMaster fallo (%s); usando AgentPro fallback", e)
        return AgentPro()

agent = _crear_agente()
fallback_agent = agent if isinstance(agent, AgentPro) else None

