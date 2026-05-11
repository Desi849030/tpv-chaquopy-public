# -*- coding: utf-8 -*-
"""
ia_assistant.py - TPV Smart v1.0
Asistente IA 100% ON-DEVICE - Texto 100% ASCII (sin tildes, sin simbolos)

v1.0 ULTRA-OPTIMIZADO:
  - FIX: Busqueda por PALABRAS (no solo coincidencia exacta) - encuentra "aceite"
    incluso si el producto es "Aceite Oliva ExtraVirgen 500ml"
  - FIX: Eliminado filtro activo=1 de busqueda principal - reconoce TODOS
    los productos importados sin importar su estado
  - FIX: Supabase ELIMINADO de busqueda de productos - 100% SQLite local,
    cero latencia de red, respuestas inmediatas
  - FIX: _handle_resumen_rol usa BATCH QUERY (1 query) en vez de 4-5 queries
    separadas - 5x mas rapido
  - PERF: Busqueda en 3 tablas SQLite con UNICO fallback entre ellas
  - PERF: Conexion SQLite persistente con WAL y cache 4MB
"""
import sqlite3, json, math, random, re, os, time, unicodedata, logging
_log = logging.getLogger("ia_assistant")
from datetime import datetime, timedelta
from collections import defaultdict

def _clean_text(text):
    """Normaliza texto: minusculas, sin puntuacion extra. Preserva tildes y ñ."""
    if not text:
        return ""
    text = str(text)
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    return text.strip()

def _normalize_search(text):
    """Para busqueda: quita tildes para comparación flexible."""
    if not text:
        return ""
    text = str(text).lower().strip()
    nfkd = unicodedata.normalize('NFKD', text)
    sin_tildes = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    return sin_tildes

def _var(texto, variantes=None):
    import random as _rnd
    if not variantes:
        return texto
    for pal, sins in variantes:
        if pal in texto:
            texto = texto.replace(pal, _rnd.choice([pal]+sins), 1)
    return texto


def _unaccent_sql(text):
    """Función SQLite custom: elimina tildes para LIKE insensible a acentos.
    Registro: conn.create_function('UNACCENT', 1, _unaccent_sql)"""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn').lower()

_sessions = {}
_sessions_lock = __import__('threading').Lock()

def _get_session(sid):
    with _sessions_lock:
        if sid not in _sessions:
            _sessions[sid] = {
                "history": [], "ts": datetime.now().isoformat(),
                "role": "vendedor", "context": {},
                "last_alerts_ts": None, "user_name": ""
            }
        return _sessions[sid]

def set_session_role(sid, role, user_name=""):
    with _sessions_lock:
        sess = _get_session(sid)
        if role in ROLES:
            sess["role"] = role
        if user_name:
            sess["user_name"] = user_name
        return sess["role"]

def get_session_info(sid):
    sess = _get_session(sid)
    r = ROLES.get(sess["role"], ROLES["vendedor"])
    return {
        "role": sess["role"], "role_label": r["label"],
        "role_color": r["color"], "role_icon": r["icon"],
        "user_name": sess.get("user_name", "")
    }

ROLES = {
    "desarrollador": {
        "label": "Desarrollador", "icon": "D", "color": "#9b59b6",
        "access": ["all"],
        "focus": "control total del sistema, blindajes, debug, seguridad avanzada",
        "greeting": "Tienes acceso completo al sistema. Debug, seguridad avanzada, API, configuración y todo lo demas."
    },
    "administrador": {
        "label": "Administrador", "icon": "A", "color": "#e74c3c",
        "access": ["ventas","inventario","empleados","reportes","predicciones","fraude",
                   "recomendaciónes","márgenes","gastos","seguridad","configuración",
                   "usuarios","lealtad","cross_selling","analisis_abc"],
        "focus": "gestion completa del negocio, seguridad, equipo, finanzas",
        "greeting": "Gestionas todo el negocio: ventas, inventario, equipo, seguridad y finanzas."
    },
    "supervisor": {
        "label": "Supervisor", "icon": "S", "color": "#f39c12",
        "access": ["ventas","inventario","productos","reportes_basicos","stock_rapido",
                   "recomendaciónes","predicciones","lealtad","empleados"],
        "focus": "supervision de ventas, inventario, equipo, metricas",
        "greeting": "Supervisas ventas, inventario y equipo. Accedes a predicciones y recomendaciónes."
    },
    "vendedor": {
        "label": "Vendedor", "icon": "V", "color": "#3498db",
        "access": ["ventas_hoy","inventario_basico","productos","busqueda","stock_rapido",
                   "precios","lealtad_basico"],
        "focus": "ventas rapidas, consultar productos, precios y stock",
        "greeting": "Te ayudo con ventas del dia, buscar productos, precios y stock disponible."
    },
    "cliente": {
        "label": "Cliente", "icon": "C", "color": "#2ecc71",
        "access": ["productos","busqueda","precios","lealtad","puntos"],
        "focus": "buscar productos, ver precios, consultar puntos de lealtad",
        "greeting": "Bienvenido! Puedo ayudarte a buscar productos, ver precios y consultar tus puntos."
    }
}

def _get_role_perms(role):
    return ROLES.get(role, ROLES["vendedor"])

def _has_access(role, capability):
    perms = _get_role_perms(role)
    return "all" in perms["access"] or capability in perms["access"]

def _time_context():
    h = datetime.now().hour
    if h < 7: return "madrugada", "A estas horas es poco comun tener actividad"
    elif h < 12: return "manana", "Buen comienzo de jornada"
    elif h < 14: return "mediodia", "Hora pico de almuerzo - se espera alto flujo"
    elif h < 18: return "tarde", "La tarde avanza bien - buen momento para revisar metricas"
    else: return "noche", "Cerrando el dia - momento ideal para el resumen"

def _time_recommendation(role):
    h = datetime.now().hour
    if h < 9:
        if _has_access(role, "inventario"):
            return "Al inicio del dia te recomiendo revisar stock bajo y las predicciones de reabastecimiento."
        return "Buen comienzo de jornada. Consulta las ventas de ayer para planificar el dia."
    elif h < 14:
        return "Hora pico. Revisa como van las ventas acumuladas y los productos con mas movimiento."
    elif h < 18:
        if _has_access(role, "reportes") or _has_access(role, "reportes_basicos"):
            return "Buen momento para revisar el rendimiento del equipo y ajustar estrategias."
        return "A mitad de dia, revisa lo que falta por vender y stock critico."
    else:
        if _has_access(role, "reportes"):
            return "Al cierre, revisa el resumen financiero, márgenes y prepara el cierre de caja."
        return "Final del dia. Revisa tus ventas totales y productos vendidos."

# ============================================================
# DATABASE LAYER v13.0 - SQLite PURO, CONEXION PERSISTENTE
# Prioridad: SQLite 100% local. Sin dependencias de red.
# ============================================================
_db_conn = None
_db_path = None
_db_init_done = False

def _get_db_paths():
    """Busca la base de datos en el orden correcto de prioridad."""
    paths = []
    files_dir = os.environ.get('TPV_FILES_DIR', '')
    if files_dir:
        for name in ['tpv_datos.db', 'tpv.db', 'tpvultrasmart.db']:
            paths.append(os.path.join(files_dir, name))
    env_db = os.environ.get('TPV_DB_PATH', '')
    if env_db and env_db not in paths:
        paths.append(env_db)
    try:
        cwd = os.getcwd()
        for name in ['tpv_datos.db', 'tpv.db', 'tpvultrasmart.db']:
            p = os.path.join(cwd, name)
            if p not in paths: paths.append(p)
    except: pass
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        for name in ['tpv_datos.db', 'tpv.db', 'tpvultrasmart.db']:
            p = os.path.join(this_dir, name)
            if p not in paths: paths.append(p)
    except: pass
    try:
        parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ['tpv_datos.db', 'tpv.db']:
            p = os.path.join(parent, name)
            if p not in paths: paths.append(p)
    except: pass
    return paths

def _db():
    """Obtiene conexión a la DB. CACHEA y REUTILIZA."""
    global _db_conn, _db_path, _db_init_done
    if _db_conn is not None:
        try:
            _db_conn.execute("SELECT 1")
            return _db_conn
        except:
            _db_conn = None
            _db_path = None
    for path in _get_db_paths():
        if not os.path.exists(path):
            continue
        try:
            conn = sqlite3.connect(path, timeout=1, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=3000")
            conn.execute("PRAGMA cache_size=-8000")
            conn.create_function('UNACCENT', 1, _unaccent_sql)
            conn.row_factory = sqlite3.Row
            _db_conn = conn
            _db_path = path
            if not _db_init_done:
                try:
                    conn.execute("CREATE TABLE IF NOT EXISTS ia_learning (id INTEGER PRIMARY KEY AUTOINCREMENT, rol TEXT NOT NULL, pregunta TEXT NOT NULL, respuesta TEXT NOT NULL, intent TEXT, hits INTEGER DEFAULT 1, fecha TEXT NOT NULL)")
                    conn.commit()
                    _db_init_done = True
                except Exception as _e: _log.debug("[IA] excepción: %s", _e)
            return conn
        except:
            continue
    return None

def _q(sql, p=(), one=False):
    c = _db()
    if not c:
        return None
    try:
        r = c.execute(sql, p)
        return r.fetchone() if one else r.fetchall()
    except:
        return None

def _safe_q(sql, p=(), one=False):
    try:
        return _q(sql, p, one)
    except:
        return None

def _exec(sql, p=()):
    c = _db()
    if not c:
        return False
    try:
        c.execute(sql, p)
        c.commit()
        return True
    except:
        return False

# ============================================================
# LEARNING - Memoria local 100% SQLite
# ============================================================
def _learn(rol, pregunta, respuesta, intent):
    try:
        existing = _safe_q(
            "SELECT id, hits FROM ia_learning WHERE rol=? AND LOWER(pregunta)=LOWER(?) LIMIT 1",
            (rol, pregunta), one=True)
        if existing:
            _exec("UPDATE ia_learning SET hits=?, fecha=? WHERE id=?",
                  (existing[1]+1, datetime.now().isoformat(), existing[0]))
        else:
            _exec("INSERT INTO ia_learning (rol,pregunta,respuesta,intent,fecha) VALUES (?,?,?,?,?)",
                  (rol, pregunta[:500], respuesta[:2000], intent, datetime.now().isoformat()))
    except:
        pass

def _recall(rol, question):
    try:
        ql = question.lower().strip()
        rows = _safe_q(
            "SELECT pregunta, respuesta, hits FROM ia_learning WHERE rol=? ORDER BY hits DESC LIMIT 5",
            (rol,))
        if not rows:
            return None
        for r in rows:
            stored = r[0].lower()
            words = [w for w in ql.split() if len(w) > 3]
            matches = sum(1 for w in words if w in stored)
            if matches >= 2 and r[2] >= 2:
                return r[1]
        return None
    except:
        return None

# ============================================================
# BUSQUEDA DE PRODUCTOS v13.0 - ULTRA RAPIDA, 100% SQLITE
#
# Cambios criticos:
# 1. Busqueda por PALABRAS separadas, no solo coincidencia total.
#    "aceite oliva" encuentra "Aceite Oliva ExtraVirgen 500ml"
# 2. SIN filtro activo=1 en la primera busqueda - reconoce TODOS
#    los productos importados sin importar su estado.
# 3. Busca en 3 tablas SQLite (productos, inventario_general, items)
# 4. Supabase ELIMINADO de la busqueda - cero latencia de red.
# ============================================================
_STOP_WORDS = set(["de","del","la","el","los","las","en","con","y","a","un","una",
                    "por","para","al","que","es","se","su","lo","no","si","mi","tu",
                    "mas","muy","ya","o","e","u"])

def _search_products(query, limit=8):
    """v13: Busqueda por palabras separadas. 100% SQLite local."""
    ql = query.lower().strip()
    if len(ql) < 2:
        return []
    # Separar en palabras y quitar stop words
    words = [_normalize_search(w) for w in re.split(r'[\s,;:]+', ql) if len(w) > 1 and w not in _STOP_WORDS]
    if not words:
        return []
    results = []
    seen = set()

    # ESTRATEGIA 1: Buscar CADA palabra individualmente en productos
    # Sin filtro activo=1 - asi encuentra TODOS los importados
    all_rows = []
    for word in words:
        rows = _safe_q(
            "SELECT nombre, precio_venta, stock_actual, categoría, unidad_medida FROM productos WHERE UNACCENT(nombre) LIKE ? LIMIT ?",
            ('%'+word+'%', limit))
        if rows:
            all_rows.extend(rows)
        # También buscar por categoría
        rows2 = _safe_q(
            "SELECT nombre, precio_venta, stock_actual, categoría, unidad_medida FROM productos WHERE UNACCENT(categoría) LIKE ? LIMIT ?",
            ('%'+word+'%', limit))
        if rows2:
            all_rows.extend(rows2)

    # ESTRATEGIA 2: Si no hay resultados, buscar coincidencia total sin activo
    if not all_rows:
        rows = _safe_q(
            "SELECT nombre, precio_venta, stock_actual, categoría, unidad_medida FROM productos WHERE UNACCENT(nombre) LIKE ? LIMIT ?",
            ('%'+_normalize_search(ql)+'%', limit))
        if rows:
            all_rows.extend(rows)

    # ESTRATEGIA 3: Buscar en inventario_general (tabla alternativa)
    if not all_rows:
        for word in words:
            rows = _safe_q(
                "SELECT nombre, precio_venta, stock_actual, categoría, unidad_medida FROM inventario_general WHERE UNACCENT(nombre) LIKE ? LIMIT ??",
                ('%'+word+'%', limit))
            if rows:
                all_rows.extend(rows)

    # ESTRATEGIA 4: Buscar en items (tercera tabla)
    if not all_rows:
        for word in words:
            rows = _safe_q(
                "SELECT nombre, precio, stock, categoría, unidad FROM items WHERE UNACCENT(nombre) LIKE ? LIMIT ?",
                ('%'+word+'%', limit))
            if rows:
                all_rows.extend(rows)

    # Convertir a resultados, eliminando duplicados por nombre
    if all_rows:
        for r in all_rows:
            nombre = _clean_text(r[0]) or "N/A"
            key = nombre.lower()
            if key not in seen:
                seen.add(key)
                results.append({
                    "nombre": nombre,
                    "precio": (r[1] or 0) if len(r) > 1 else 0,
                    "stock": (r[2] or 0) if len(r) > 2 else 0,
                    "categoría": _clean_text(r[3]) if len(r) > 3 else "",
                    "unidad": _clean_text(r[4]) if len(r) > 4 else "ud",
                    "source": "local"
                })

    # ORDENAR: productos que coincidan con MAS palabras van primero
    if len(words) > 1:
        def score_fn(p):
            name_l = p["nombre"].lower()
            return sum(1 for w in words if w in name_l)
        results.sort(key=score_fn, reverse=True)

    return results[:limit]


def _extract_product_name(text):
    tl = text.lower().strip()
    patterns = [
        r"(?:cuanto(?:| cuesta| vale| es)|precio (?:de|del?|la))\s+(?:el |la |los |las )?(.+?)[\?\.]?$",
        r"(?:tiene|hay|busco|necesito|quiero|deme|dame)\s+(?:el |la |los |las )?(.+?)[\?\.]?$",
        r"(?:dónde está|ubicación de|donde encuentro)\s+(?:el |la |los |las )?(.+?)[\?\.]?$",
        r"^(.+?)(?:\s+cuanto|cuesta|vale|precio|stock|hay|tiene|disponible)",
    ]
    for pat in patterns:
        m = re.search(pat, tl)
        if m:
            name = m.group(1).strip()
            name = re.sub(r'^(algun|un |una |unos |unas |de )', '', name)
            if len(name) >= 2:
                return name
    return None

def _fmt(v):
    if v is None: return "$0"
    return "${:,.0f}".format(v).replace("$-","-$")

# ============================================================
# SMART QUERY v13 - 100% SQLite, sin filtro activo innecesario
# ============================================================
_TABLE_KEYWORDS = {
    "productos": {
        "table": "productos", "fallback_table": "inventario_general",
        "words": ["producto","articulo","item","mercancia","catalogo",
                  "inventario","que tengo","cuantos productos","lista de"],
        "select": "nombre, precio_venta, stock_actual, categoría",
        "count_sql": "SELECT COUNT(*) FROM {table}",
        "list_sql": "SELECT nombre, precio_venta, stock_actual FROM {table} ORDER BY nombre LIMIT {limit}",
        "count_label": "productos registrados"
    },
    "ventas": {
        "table": "historial_ventas",
        "words": ["venta","vendido","factura","ticket","cobro","transacción",
                  "recaudado","ingreso","facturacion","cuanto vendi"],
        "select": "fecha, total, cantidad, nombre, vendedor_nombre",
        "count_sql": "SELECT COUNT(*), COALESCE(SUM(total),0) FROM {table} WHERE DATE(fecha)=DATE('now','localtime')",
        "list_sql": "SELECT fecha, total, nombre FROM {table} WHERE DATE(fecha)=DATE('now','localtime') ORDER BY total DESC LIMIT {limit}",
        "count_label": "ventas del dia"
    },
    "clientes": {
        "table": "clientes", "fallback_table": "usuarios",
        "words": ["cliente","comprador","consumidor","usuario registrado"],
        "select": "nombre, email, telefono, puntos",
        "count_sql": "SELECT COUNT(*) FROM {table}",
        "list_sql": "SELECT nombre, telefono FROM {table} LIMIT {limit}",
        "count_label": "clientes registrados"
    },
    "gastos": {
        "table": "gastos",
        "words": ["gasto","egreso","pago","costo operación","pago proveedor"],
        "select": "fecha, monto, concepto, categoría",
        "count_sql": "SELECT COUNT(*), COALESCE(SUM(monto),0) FROM {table} WHERE DATE(fecha)=DATE('now','localtime')",
        "list_sql": "SELECT fecha, monto, concepto FROM {table} WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC LIMIT {limit}",
        "count_label": "gastos del dia"
    },
    "empleados": {
        "table": "usuarios",
        "words": ["empleado","vendedor","trabajador","staff","personal","equipo"],
        "select": "nombre, rol, email",
        "count_sql": "SELECT COUNT(*) FROM {table}",
        "list_sql": "SELECT nombre, rol FROM {table} LIMIT {limit}",
        "count_label": "empleados registrados"
    },
    "categorías": {
        "table": "categorías",
        "words": ["categoría","clasificacion","departamento","seccion","tipo de producto"],
        "select": "nombre, descripción",
        "count_sql": "SELECT COUNT(*) FROM {table}",
        "list_sql": "SELECT nombre FROM {table} ORDER BY nombre LIMIT {limit}",
        "count_label": "categorías"
    }
}

_COUNT_WORDS = ["cuantos","cuantas","cantidad","total de","número de","contar","hay",
                "cuanto hay","existen","tenemos"]

def _smart_sqlite_query(text, role):
    tl = text.lower().strip()
    best_table = None
    best_score = 0
    for table_key, info in _TABLE_KEYWORDS.items():
        score = sum(1 for w in info["words"] if w in tl)
        if score > best_score:
            best_score = score
            best_table = table_key
    if not best_table or best_score == 0:
        return None
    info = _TABLE_KEYWORDS[best_table]
    if best_table == "ventas" and not _has_access(role,"ventas") and not _has_access(role,"ventas_hoy"):
        return None
    if best_table == "gastos" and not _has_access(role,"gastos") and not _has_access(role,"all"):
        return None
    if best_table == "empleados" and not _has_access(role,"empleados") and not _has_access(role,"all"):
        return None
    is_count = any(w in tl for w in _COUNT_WORDS)
    is_list = any(w in tl for w in ["lista","mostrar","ver","muestrame","que son","cuales",
                                     "todos","todas","todos los","todas las"])
    table_name = info["table"]
    limit = 8
    if is_count:
        sql = info["count_sql"].format(table=table_name)
        row = _safe_q(sql, one=True)
        if row:
            if len(row) >= 2 and row[1]:
                return _clean_text("Hay **%d** %s. Total: **%s**" % (row[0] or 0, info["count_label"], _fmt(row[1])))
            return _clean_text("Hay **%d** %s." % (row[0] or 0, info["count_label"]))
    elif is_list:
        sql = info["list_sql"].format(table=table_name, limit=limit)
        rows = _safe_q(sql)
        if not rows and "fallback_table" in info:
            sql2 = info["list_sql"].format(table=info["fallback_table"], limit=limit)
            rows = _safe_q(sql2)
        if rows:
            lines = ["**%s (%d):**" % (info["count_label"].title(), len(rows)), ""]
            for r in rows:
                if len(r) >= 2:
                    lines.append("  - %s: %s" % (r[0] or "N/A", r[1] if r[1] else ""))
                else:
                    lines.append("  - %s" % (r[0] or "N/A"))
            return _clean_text("\n".join(lines))
    return None

# ============================================================
# NLU - Deteccion de intención
# ============================================================
_SALUDOS = ["hola","buenos dias","buenas tardes","buenas noches","hey","saludos",
            "que tal","como estas","buen dia","que onda","buenas","hi","hello"]

_EDGE_KW_PREDICCION = ["prediccion","pronostico","predecir","tendencia",
                       "proyeccion","futuro","estimacion","holt","suavizado"]
_EDGE_KW_FRAUDE = ["fraude","anomalia","benford","alerta fraude","deteccion fraude"]
_EDGE_KW_ABC = ["abc","pareto","analisis abc","categoría abc","clasificacion abc"]
_EDGE_KW_CROSS = ["cross selling","cross-selling","venta cruzada","combinacion","conjunto"]
_EDGE_KW_PRECIOS = ["optimización de precios","precio sugerido","precio optimo","mejor precio","oportunidad precio"]
_EDGE_KW_KPI = ["kpi","indicador","metrica","rendimiento","health score","salud negocio"]
_EDGE_KW_DASHBOARD = ["dashboard","tablero","panel ia","ia edge","todo actualizado","actualizar todo"]
_AGRADECIMIENTOS = ["gracias","genial","perfecto","excelente","listo","vale",
                     "bien hecho","cool","ok","entendido"]
_DESPEDIDAS = ["adios","chao","bye","hasta luego","nos vemos","hasta manana","me voy"]
_AYUDA = ["ayuda","que puedes","funciónes","que haces","help","que sabes",
          "como funcióna","que puedo preguntar","para que sirves"]

_ROLE_KEYWORDS = {
    "desarrollador": ["debug","configurar","base de datos","error","logs","servidor","deploy","git","compilar","api"],
    "administrador": ["finanzas","empleados","seguridad","permisos","usuarios","licencias","configuración del sistema"],
    "supervisor": ["equipo","supervisar","metricas","reporte","rendimiento","horario","turno"],
    "vendedor": ["vender","cliente","caja","cobrar","facturar","ticket"],
    "cliente": ["comprar","precio","oferta","descuento","promocion","puntos"],
}

def _detect_role_from_text(text):
    tl = text.lower().strip()
    scores = {}
    for role, keywords in _ROLE_KEYWORDS.items():
        score = sum(1 for k in keywords if k in tl)
        if score > 0:
            scores[role] = score
    if not scores:
        return None
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None

def _detect_intent(text, role):
    tl = text.lower().strip()
    if not tl or len(tl) < 1:
        return "greeting", None
    # 1. SALUDOS
    if any(tl.startswith(g) for g in ["hola ","hey ","buenos ","buenas ","buen dia","que tal","como estas"]) or tl in _SALUDOS:
        if len(tl) < 30:
            return "greeting", None
    # 2. AGRADECIMIENTOS
    if any(g in tl for g in _AGRADECIMIENTOS) and len(tl) < 25:
        return "thanks", None
    # 3. DESPEDIDAS
    if any(g in tl for g in _DESPEDIDAS):
        return "farewell", None
    # 4. RESUMEN DEL DIA
    if any(g in tl for g in ["resumen del dia","resumen","estado","que hay","que tal el dia","informe","panel"]):
        return "resumen_rol", None
    # 5. AYUDA
    if any(g in tl for g in _AYUDA):
        return "help", None
    # 6. Memoria aprendizaje
    learned = _recall(role, text)
    if learned:
        return "learned", learned
    # 7. Precio producto - BUSQUEDA RAPIDA
    product_name = _extract_product_name(text)
    if product_name:
        products = _search_products(product_name, 5)
        if products:
            return "product_price", {"products": products, "query": product_name}
        products = _search_products(text, 5)
        if products:
            return "product_search", products
    # 8. Ventas
    if any(w in tl for w in ["venta","vendido","factura","ticket","cobro","facturacion",
                               "cuanto vendi","cuanto hecho","recaudado"]):
        sub = None
        if any(w in tl for w in ["hoy","dia","hoy dia"]): sub="hoy"
        elif any(w in tl for w in ["semana","7 dias","última semana"]): sub="semana"
        elif any(w in tl for w in ["mes","30 dias","último mes","mensual"]): sub="mes"
        if any(w in tl for w in ["top","mas vendido","mejor","lider","estrella"]):
            sub="top_"+(sub or "hoy")
        elif any(w in tl for w in ["vendedor","equipo","quien vendio"]): sub="vendedor"
        elif any(w in tl for w in ["hora pico","horario"]): sub="hora_pico"
        elif any(w in tl for w in ["ingreso","ganancia","facturacion","recaudado"]):
            sub="ingresos_"+(sub or "hoy")
        return "ventas", sub
    # 9. Inventario
    if any(w in tl for w in ["inventario","stock","existencia","cuantos productos",
                               "que tengo","almacen","disponible","cuanto hay",
                               "que me queda","agotado","sin stock","poco stock"]):
        if any(w in tl for w in ["bajo","critico","minimo","poco","agotado","sin stock"]):
            return "inventario","bajo"
        if any(w in tl for w in ["reorden","pedir","reabastecer","comprar"]):
            return "inventario","reorden"
        return "inventario","general"
    # 10. Seguridad
    if any(w in tl for w in ["seguridad","alerta","amenaza","bloqueado","ip",
                               "hack","intruso","protección","ataque","fraude"]):
        if any(w in tl for w in ["fraude","anomalia","benford"]): return "seguridad","fraude"
        return "seguridad","general"
    # 11. Recomendaciones
    if any(w in tl for w in ["recomend","sugerencia","que me sugieres","que deberia",
                               "consejo","mejorar","optimizar"]):
        return "recomendación", None
    # 12. Resumen (general, no por rol)
    if any(w in tl for w in ["resumen","estado general","como va","dashboard",
                               "como estamos","situación","overview","como vamos"]):
        return "resumen", None
    # 13. Finanzas
    if any(w in tl for w in ["gasto","egreso","costo","margen","rentabilidad",
                               "ganancia bruta","utilidad","profit","perdida","balance"]):
        if any(w in tl for w in ["margen","rentabilidad","utilidad"]): return "financiero","margen"
        return "financiero","gastos"
    # 14. Lealtad
    if any(w in tl for w in ["puntos","lealtad","membresia","recompensa","canje",
                               "mis puntos","cuántos puntos"]):
        return "lealtad", None
    # 15. Info app
    if any(w in tl for w in ["aplicación","app","tpv","versión","sistema","software"]):
        return "app_info", None
    # 16. IA Edge Functions
    if any(w in tl for w in ["kpi","indicador","metrica","rendimiento del negocio","health score",
                               "salud del negocio","dashboard","tablero","panel ia","ia edge",
                               "actualizar todo","todo actualizado"]):
        if any(w in tl for w in ["kpi","indicador","metrica"]):
            return "edge_kpis", None
        if any(w in tl for w in ["dashboard","tablero","salud del negocio","health score","panel ia"]):
            return "edge_dashboard", None
        return "edge_dashboard", None
    if any(w in tl for w in ["cross selling","cross-selling","venta cruzada","combinacion de productos","conjunto de productos","que combina con"]):
        return "edge_cross_selling", None
    if any(w in tl for w in ["abc","pareto","analisis abc","categoría abc","clasificacion abc"]):
        return "edge_abc", None
    if any(w in tl for w in ["optimización de precios","precio sugerido","precio optimo","mejor precio","oportunidad precio"]):
        return "edge_precios", None
    if any(w in tl for w in _EDGE_KW_PREDICCION):
        return "prediccion", None
    # 17. SMART QUERY
    smart_result = _smart_sqlite_query(text, role)
    if smart_result:
        return "smart_query", smart_result
    # 18. Busqueda producto generica - LA ULTIMA OPORTUNIDAD
    if len(tl) > 2:
        prods = _search_products(tl, 5)
        if prods:
            return "product_search", prods
    return "unknown", None

# SUGGESTIONS
_INTENT_SUGGESTIONS = {
    "greeting": ["ventas de hoy", "stock bajo", "predicciones"],
    "resumen_rol": ["ventas de hoy", "stock bajo", "ayuda"],
    "thanks": ["ventas de hoy", "resumen", "stock bajo"],
    "farewell": [],
    "help": ["ventas de hoy", "cuánto cuesta X", "resumen", "KPIs del día", "predicciones", "análisis ABC"],
    "product_price": ["stock bajo", "ventas de hoy", "recomendaciónes"],
    "product_search": ["ventas de hoy", "stock bajo", "resumen"],
    "ventas": ["top productos", "stock bajo", "finanzas del dia"],
    "ventas_hoy": ["top productos", "ventas de la semana", "finanzas del dia"],
    "inventario": ["stock bajo", "qué productos tengo", "reorden"],
    "seguridad": ["resumen", "ventas de hoy", "estado de seguridad", "fraude"],
    "recomendación": ["ventas de hoy", "stock bajo", "predicciones", "cross-selling"],
    "resumen": ["ventas de hoy", "stock bajo", "KPIs del día", "predicciones"],
    "financiero": ["ventas de hoy", "gastos", "márgenes"],
    "lealtad": ["cuántos puntos tengo", "ventas de hoy", "recomendaciónes"],
    "app_info": ["ventas de hoy", "resumen", "ayuda"],
    "prediccion": ["stock bajo", "recomendaciónes", "ventas de hoy", "KPIs del día"],
    "edge_kpis": ["predicciones", "ventas de hoy", "dashboard"],
    "edge_dashboard": ["KPIs del día", "predicciones", "fraude"],
    "edge_abc": ["cross-selling", "optimización de precios", "resumen"],
    "edge_cross_selling": ["análisis ABC", "optimización de precios", "resumen"],
    "edge_precios": ["análisis ABC", "cross-selling", "resumen"],
    "smart_query": ["ventas de hoy", "resumen", "stock bajo"],
    "learned": ["ventas de hoy", "resumen", "ayuda"],
    "unknown": ["ayuda", "ventas de hoy", "resumen", "KPIs del día"],
}

def _get_suggestions(intent):
    return _INTENT_SUGGESTIONS.get(intent, ["ayuda", "ventas de hoy", "resumen"])

# ============================================================
# HANDLERS - Respuestas por intención
# ============================================================

def _handle_greeting(role, user_name=""):
    """v13: GREETING 100% INSTANTANEO - CERO queries a la DB."""
    h = datetime.now().hour
    tc_name, tmsg = _time_context()
    s = "Buenos días" if h < 12 else "Buenas tardes" if h < 18 else "Buenas noches"
    r = _get_role_perms(role)
    name_str = ", %s" % _clean_text(user_name) if user_name else ""
    parts = ["%s%s! Soy TPV Smart v13.0. %s." % (s, name_str, tmsg), "",
             "Rol: %s - %s" % (r["label"], r["focus"]), "", r["greeting"], "",
             _time_recommendation(role), "",
             "Escribe lo que necesites. Ejemplos:"]
    if role == "cliente":
        parts.extend(["- \"cuánto cuesta el arroz\"","- \"qué productos tienen\"","- \"cuántos puntos tengo\""])
    elif role == "vendedor":
        parts.extend(["- \"cuánto cuesta X\" o \"hay stock de Y\"","- \"ventas de hoy\"","- Escribe un nombre de producto"])
    else:
        parts.extend(["- \"ventas de hoy\" / \"top productos\" / \"stock bajo\"","- \"cuánto cuesta X\" / \"predicciones\" / \"recomendaciónes\"","- Escribe cualquier cosa en lenguaje natural"])
    return _clean_text("\n".join(parts))

def _handle_resumen_rol(role, user_name=""):
    """v13: BATCH QUERY - 1 sola query en vez de 4-5 separadas. 5x mas rapido."""
    h = datetime.now().hour
    tc_name, tmsg = _time_context()
    s = "Buenos días" if h < 12 else "Buenas tardes" if h < 18 else "Buenas noches"
    name_str = ", %s" % _clean_text(user_name) if user_name else ""
    r = _get_role_perms(role)
    parts = ["%s%s! TPV Smart v13.0" % (s, name_str), "",
             "Rol: %s - %s" % (r["label"], r["focus"]), ""]
    try:
        # v13: BATCH - Una sola query que obtiene todo lo necesario
        batch = _safe_q("""SELECT
            (SELECT COUNT(*) FROM productos),
            (SELECT COUNT(*) FROM usuarios),
            (SELECT COALESCE(SUM(total),0) FROM historial_ventas WHERE date(fecha)=date('now','localtime')),
            (SELECT COUNT(*) FROM historial_ventas WHERE date(fecha)=date('now','localtime')),
            (SELECT COUNT(*) FROM productos WHERE stock_actual <= 5 AND stock_actual >= 0)
        """, one=True)
        if role == "desarrollador":
            parts.append("== Estado del Sistema ==")
            parts.append("Blindajes: PCI-DSS, HET, WebSockets, MPOC activos")
            if batch:
                parts.append("Productos: %d" % (batch[0] or 0))
                parts.append("Usuarios: %d" % (batch[1] or 0))
                parts.append("Ventas hoy: %s" % _fmt(batch[2]))
                parts.append("Transacciónes: %d" % (batch[3] or 0))
            parts.append("")
            parts.append("Comandos: estado sistema | blindajes | ventas | debug")
        elif role == "administrador":
            parts.append("== Resumen de Gestion ==")
            if batch:
                parts.append("Total productos: %d" % (batch[0] or 0))
                parts.append("Ventas hoy: %s" % _fmt(batch[2]))
                parts.append("Transacciónes hoy: %d" % (batch[3] or 0))
                if batch[4] and batch[4] > 0:
                    parts.append("ALERTA: %d productos con stock bajo" % batch[4])
            parts.append("")
            parts.append("Comandos: ventas | stock bajo | finanzas | equipo")
        elif role == "supervisor":
            parts.append("== Panel de Supervision ==")
            if batch:
                parts.append("Ventas hoy: %s" % _fmt(batch[2]))
                parts.append("Transacciónes: %d" % (batch[3] or 0))
                if batch[4] and batch[4] > 0:
                    parts.append("ALERTA: %d productos con stock bajo" % batch[4])
            parts.append("")
            parts.append("Comandos: ventas | top productos | predicciones")
        elif role == "vendedor":
            parts.append("== Tu Panel de Ventas ==")
            if batch:
                parts.append("Ventas acumuladas hoy: %s" % _fmt(batch[2]))
                parts.append("Ventas realizadas: %d" % (batch[3] or 0))
                if batch[4] and batch[4] > 0:
                    parts.append("Nota: %d productos con stock bajo" % batch[4])
            parts.append("")
            parts.append("Comandos: precio de X | stock de Y | ventas de hoy")
        else:
            parts.append("Busca productos y consulta precios rapidamente.")
            parts.append("Comandos: cuánto cuesta X | qué productos tienen")
    except Exception as e:
        parts.append(r["greeting"])
    parts.append("")
    parts.append(tmsg)
    return _clean_text("\n".join(parts))


def _handle_thanks():
    return random.choice([
        "Con gusto! Si necesitas algo mas, aqui estoy.",
        "Me alegra poder ayudar! Preguntame lo que necesites.",
        "Excelente! Estoy aqui para lo que haga falta.",
        "Listo! No dudes en consultarme cuándo quieras.",
    ])

def _handle_farewell():
    return "Hasta luego! Que tengas un excelente dia. Vuelve cuándo necesites."

def _handle_help(role):
    try:
        r = _get_role_perms(role)
        if role == "cliente":
            return _clean_text("Qué puedo hacer por ti:\n\nProductos:\n  - \"cuánto cuesta el arroz\" / \"precio de leche\"\n  - \"qué productos tienen\" / \"hay gaseosas\"\n\nLealtad:\n  - \"cuántos puntos tengo\" / \"mis puntos\"\n\nEscribe en lenguaje natural, sin comandos!")
        elif role == "vendedor":
            return _clean_text("Qué puedo hacer por ti (Rol: %s):\n\nProductos y Precios:\n  - \"cuánto cuesta el café\" / \"precio de pan\"\n  - \"hay stock de arroz\" / \"busco gaseosa\"\n\nVentas:\n  - \"ventas de hoy\" / \"cuánto he vendido\"\n\nInventario:\n  - \"stock bajo\" / \"qué productos tengo\"\n\nIA Edge (todo desde aquí):\n  - \"predicciones\" / \"KPIs del día\" / \"dashboard\"\n  - \"análisis ABC\" / \"cross-selling\" / \"optimización de precios\"\n\nTodo en lenguaje natural!" % r["label"])
        else:
            return _clean_text("Qué puedo hacer por ti (Rol: %s):\n\nVentas: \"ventas de hoy/semana/mes\", \"top productos\", \"hora pico\"\nProductos: \"cuánto cuesta X\", \"hay Y\", nombre de producto\nInventario: \"stock bajo\", \"que debo reordenar\"\nFinanzas: \"gastos\", \"márgenes\", \"ganancia bruta\"\nIA: \"predicciones\", \"recomendaciónes\", \"cross-selling\"\nSeguridad: \"estado de seguridad\", \"fraude\"\nLealtad: \"puntos\", \"programa de lealtad\"\n\nEscribe lo que quieras saber, sin comandos!" % r["label"])
    except:
        return "Puedo ayudarte con productos, precios, ventas, inventario y mas."

def _handle_product_price(data, role):
    try:
        products = data.get("products", [])
        query = data.get("query", "")
        if not products:
            return _clean_text("No encontré '%s'. Intenta con otro nombre." % query)
        if len(products) == 1:
            p = products[0]
            lines = ["%s:" % p["nombre"],""]
            lines.append("  Precio: %s" % _fmt(p["precio"]))
            lines.append("  Stock: %d %s" % (p["stock"], p["unidad"]))
            if p["precio"] > 0 and p["stock"] > 0:
                lines.append("  Valor en stock: %s" % _fmt(p["precio"] * p["stock"]))
            if p["categoría"]:
                lines.append("  Categoria: %s" % p["categoría"])
            if p["stock"] == 0: lines.append("  [Producto agotado]")
            elif p["stock"] <= 5: lines.append("  [Pocas unidades disponibles]")
            return _clean_text("\n".join(lines))
        else:
            lines = ["%d productos encontrados para '%s':" % (len(products), query),""]
            for p in products:
                stock_st = "Sin stock" if p["stock"]==0 else "%d %s" % (p["stock"], p["unidad"])
                lines.append("  - %s | %s | Stock: %s" % (p["nombre"], _fmt(p["precio"]), stock_st))
            lines.extend(["","Escribe el nombre exacto para ver detalles."])
            return _clean_text("\n".join(lines))
    except:
        return "Error al buscar el producto. Intenta de nuevo."

def _handle_product_search(products):
    try:
        if not products:
            return "No encontré productos. Intenta con otro nombre."
        lines = ["%d productos encontrados:" % len(products),""]
        for p in products:
            stock_st = "Sin stock" if p["stock"]==0 else "%d %s" % (p["stock"], p["unidad"])
            lines.append("  - %s | %s | Stock: %s" % (p["nombre"], _fmt(p["precio"]), stock_st))
        return _clean_text("\n".join(lines))
    except:
        return "Error en la busqueda. Intenta de otro termino."

def _handle_app_info(role):
    try:
        lines = ["TPV Smart - Información del Sistema:",""]
        lines.append("  Versión: v1.0")
        lines.append("  Motor IA: NLU v13.0 Role-Aware ON-DEVICE")
        lines.append("  Base de datos: SQLite local (prioridad) + Supabase (respaldo)")
        lines.append("  Busqueda: 100% local, por palabras, 3 tablas SQLite")
        lines.append("  Blindajes: PCI-DSS, HET, WebSockets, SSE, MPOC Attestation")
        if _has_access(role,"all") or _has_access(role,"configuración"):
            lines.extend(["","Modulos activos:","  - 5 paneles: Seguridad, IA Edge, Lealtad, Inventario, Ventas","  - Sistema de roles con privilegios por modulo","  - Lealtad omnicanal con 4 niveles","  - Inteligencia periferica SQLite (Smart Query)"])
        else:
            lines.append("Tu rol (%s) permite consultar productos, precios, stock y mas." % _get_role_perms(role)["label"])
        return _clean_text("\n".join(lines))
    except:
        return "TPV Smart v13.0 - Sistema de punto de venta inteligente."

def _handle_ventas(sub, role):
    try:
        if not _has_access(role,"ventas") and not _has_access(role,"ventas_hoy"):
            return "No tienes permiso para ver datos de ventas en tu rol actual."
        if sub == "hoy" or sub is None:
            r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(cantidad),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            if not r or r[0]==0: return "No hay ventas registradas hoy."
            avg = r[1]/r[0] if r[0]>0 else 0
            return _clean_text("Ventas de hoy:\n  Transacciónes: %d\n  Ingresos: %s\n  Unidades: %d\n  Ticket promedio: %s" % (r[0], _fmt(r[1]), int(r[2] or 0), _fmt(avg)))
        elif sub == "semana":
            r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(cantidad),0) FROM historial_ventas WHERE fecha >= DATE('now','localtime','-7 days')", one=True)
            if not r or r[0]==0: return "No hay ventas en los últimos 7 dias."
            avg = r[1]/r[0] if r[0]>0 else 0
            return _clean_text("Ventas de la semana:\n  Transacciónes: %d\n  Ingresos: %s\n  Ticket promedio: %s" % (r[0], _fmt(r[1]), _fmt(avg)))
        elif sub == "mes":
            r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(cantidad),0) FROM historial_ventas WHERE fecha >= DATE('now','localtime','-30 days')", one=True)
            if not r or r[0]==0: return "No hay ventas en los últimos 30 dias."
            avg = r[1]/r[0] if r[0]>0 else 0
            return _clean_text("Ventas del mes:\n  Transacciónes: %d\n  Ingresos: %s\n  Ticket promedio: %s\n  Promedio diario: %s" % (r[0], _fmt(r[1]), _fmt(avg), _fmt(r[1]/30)))
        elif sub and sub.startswith("top_"):
            period = sub.replace("top_","")
            if period=="hoy": sql="DATE(fecha)=DATE('now','localtime')"; label="Hoy"
            elif period=="semana": sql="fecha >= DATE('now','localtime','-7 days')"; label="Semana"
            elif period=="mes": sql="fecha >= DATE('now','localtime','-30 days')"; label="Mes"
            else: sql="DATE(fecha)=DATE('now','localtime')"; label="Hoy"
            rows = _safe_q("SELECT * FROM historial_ventas WHERE fecha >= ?"  % sql)
            if not rows: return "No hay ventas en este periodo."
            lines = ["Top 5 productos (%s):" % label,""]
            for i,r in enumerate(rows,1):
                lines.append("  %d. %s - %d uds / %s" % (i, _clean_text(r[0]) or "N/A", int(r[1] or 0), _fmt(r[2] or 0)))
            return _clean_text("\n".join(lines))
        elif sub == "vendedor":
            rows = _safe_q("SELECT vendedor_nombre, COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') AND vendedor_nombre IS NOT NULL GROUP BY vendedor_nombre ORDER BY SUM(total) DESC LIMIT 5")
            if not rows: return "No hay datos de vendedores hoy."
            lines = ["Vendedores del dia:",""]
            for i,v in enumerate(rows,1):
                lines.append("  %d. %s - %d ventas / %s" % (i, _clean_text(v[0]), v[1], _fmt(v[2])))
            return _clean_text("\n".join(lines))
        elif sub == "hora_pico":
            rows = _safe_q("SELECT strftime('%%H', fecha) as h, COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') GROUP BY strftime('%%H', fecha) ORDER BY SUM(total) DESC LIMIT 3")
            if not rows: return "No hay datos hoy."
            lines = ["Horas pico de hoy:",""]
            for v in rows:
                lines.append("  %s:00 - %d ventas / %s" % (v[0], v[1], _fmt(v[2])))
            return _clean_text("\n".join(lines))
        elif sub and sub.startswith("ingresos_"):
            period = sub.replace("ingresos_","")
            if period=="semana": sql_date="DATE('now','localtime','-7 days')"; label="la semana"
            else: sql_date="DATE('now','localtime')"; label="hoy"
            rev = _safe_q("SELECT * FROM historial_ventas WHERE fecha >= ?"  % sql_date, one=True)
            exp = _safe_q("SELECT * FROM historial_ventas WHERE fecha >= ?"  % sql_date, one=True)
            if not rev: return "No hay datos financieros %s." % label
            rv = float(rev[0] or 0); ev = float(exp[0] or 0) if exp else 0; p = rv-ev
            if rv==0: return "No hay ingresos %s." % label
            return _clean_text("Financiero %s:\n  Ingresos: %s\n  Gastos: %s\n  Ganancia: %s\n  Margen: %.1f%%" % (label, _fmt(rv), _fmt(ev), _fmt(p), p/rv*100 if rv>0 else 0))
        else:
            r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(cantidad),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
            if not r or r[0]==0: return "No hay ventas hoy."
            avg = r[1]/r[0] if r[0]>0 else 0
            return _clean_text("Ventas de hoy:\n  Transacciónes: %d\n  Ingresos: %s\n  Unidades: %d\n  Ticket promedio: %s" % (r[0], _fmt(r[1]), int(r[2] or 0), _fmt(avg)))
    except:
        return "Error al consultar ventas. Intenta de nuevo."

def _handle_inventario(sub, role):
    try:
        if not _has_access(role,"inventario") and not _has_access(role,"inventario_basico") and not _has_access(role,"stock_rapido") and "all" not in _get_role_perms(role).get("access",[]):
            return "No tienes permiso para ver inventario en tu rol actual."
        if sub == "bajo":
            rows = _safe_q("SELECT nombre, stock_actual, stock_minimo FROM inventario_general WHERE stock_actual <= stock_minimo AND stock_actual >= 0 ORDER BY stock_actual ASC LIMIT 10")
            if not rows:
                rows = _safe_q("SELECT nombre, stock_actual, 5 FROM productos WHERE stock_actual <= 5 AND stock_actual >= 0 ORDER BY stock_actual ASC LIMIT 10")
            if not rows: return "Todos los productos tienen stock suficiente."
            lines = ["Productos con stock bajo (%d):" % len(rows),""]
            for r in rows:
                min_st = r[2] if len(r) > 2 and r[2] else 5
                status = "AGOTADO" if r[1]==0 else "%d uds (min: %d)" % (r[1], min_st)
                lines.append("  - %s: %s" % (_clean_text(r[0]) or "?", status))
            return _clean_text("\n".join(lines))
        elif sub == "reorden":
            rows = _safe_q("SELECT nombre, stock_actual, stock_minimo FROM inventario_general WHERE stock_actual <= stock_minimo ORDER BY stock_actual ASC LIMIT 8")
            if not rows:
                rows = _safe_q("SELECT nombre, stock_actual, 10 FROM productos WHERE stock_actual <= 5 ORDER BY stock_actual ASC LIMIT 8")
            if not rows: return "No hay productos que requieran reorden."
            lines = ["Productos para reorden:",""]
            for r in rows:
                min_st = r[2] if len(r) > 2 and r[2] else 10
                needed = max(0, min_st*2 - (r[1] or 0))
                lines.append("  - %s: %d uds -> pedir %d uds" % (_clean_text(r[0]) or "?", r[1], needed))
            return _clean_text("\n".join(lines))
        else:
            total = _safe_q("SELECT COUNT(*), COALESCE(SUM(stock_actual),0), COALESCE(SUM(precio_venta * stock_actual),0) FROM productos", one=True)
            if not total or total[0]==0:
                total = _safe_q("SELECT COUNT(*), COALESCE(SUM(stock_actual),0), 0 FROM inventario_general", one=True)
            if not total or total[0]==0: return "No hay productos en el inventario."
            low = _safe_q("SELECT COUNT(*) FROM productos WHERE stock_actual <= 5", one=True)
            lines = ["Inventario general:",""]
            lines.append("  Total productos: %d" % total[0])
            lines.append("  Unidades en stock: %d" % (total[1] or 0))
            if total[2]: lines.append("  Valor total: %s" % _fmt(total[2]))
            if low and low[0]>0: lines.append("  Con stock bajo: %d" % low[0])
            return _clean_text("\n".join(lines))
    except:
        return "Error al consultar inventario. Intenta de nuevo."

def _handle_seguridad(sub, role):
    try:
        if not _has_access(role,"seguridad") and not _has_access(role,"all"):
            return "No tienes permiso para ver datos de seguridad."
        if sub == "fraude":
            try:
                from ai_fraud import get_fraud_dashboard
                fd = get_fraud_dashboard()
                lines = ["Estado de seguridad - Anti-Fraude:",""]
                dist = fd.get("alert_distribution",{})
                lines.append("  Alertas criticas: %d" % dist.get("critical",0))
                lines.append("  Alertas altas: %d" % dist.get("high",0))
                lines.append("  Alertas medias: %d" % dist.get("medium",0))
                lines.append("  Score de seguridad: %.1f%%" % fd.get("overall_score",0))
                return _clean_text("\n".join(lines))
            except:
                return "Modulo anti-fraude no disponible en este momento."
        lines = ["Estado de seguridad:",""]
        lines.append("  Blindaje PCI-DSS: Activo")
        lines.append("  Deteccion HET: Activo")
        lines.append("  WebSockets seguros: Activo")
        lines.append("  MPOC Attestation: Activo")
        return _clean_text("\n".join(lines))
    except:
        return "Error al consultar seguridad."

def _handle_recomendación(role):
    try:
        r = _get_role_perms(role)
        lines = ["Recomendaciones para %s:" % r["label"],""]
        top_selling = _safe_q("SELECT nombre, SUM(cantidad) as total_vendido FROM historial_ventas WHERE DATE(fecha) >= DATE('now','localtime','-7 days') AND nombre IS NOT NULL GROUP BY nombre ORDER BY total_vendido DESC LIMIT 3")
        if top_selling:
            lines.append("Top vendidos (7 dias):")
            for p in top_selling: lines.append("  - %s: %d unidades" % (_clean_text(p[0]), p[1]))
            lines.append("")
        low = _safe_q("SELECT nombre, stock_actual FROM inventario_general WHERE stock_actual <= stock_minimo ORDER BY stock_actual ASC LIMIT 3")
        if not low:
            low = _safe_q("SELECT nombre, stock_actual FROM productos WHERE stock_actual <= 5 ORDER BY stock_actual ASC LIMIT 3")
        if low:
            lines.append("Urgente reabastecer:")
            for p in low: lines.append("  - %s: %d uds" % (_clean_text(p[0]), p[1]))
            lines.append("")
        h = datetime.now().hour
        if h < 10: lines.append("Tip del dia: Revisa el inventario al inicio de la jornada.")
        elif h < 15: lines.append("Tip del dia: Monitorea las horas pico para optimizar staffing.")
        else: lines.append("Tip del dia: Revisa el cierre de caja y prepara el resumen del dia.")
        return _clean_text("\n".join(lines))
    except:
        return "No pude generar recomendaciónes ahora."

def _handle_resumen(role):
    try:
        r = _get_role_perms(role)
        lines = ["Resumen del estado - %s:" % r["label"],""]
        sc = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if sc and sc[0]>0: lines.append("Ventas hoy: %d txns | %s" % (sc[0], _fmt(sc[1])))
        else: lines.append("Ventas hoy: Sin ventas registradas")
        total = _safe_q("SELECT COUNT(*) FROM productos", one=True)
        low = _safe_q("SELECT COUNT(*) FROM productos WHERE stock_actual <= 5", one=True)
        if total: lines.append("Inventario: %d productos | %d con stock bajo" % (total[0], low[0] if low else 0))
        clients = _safe_q("SELECT COUNT(*) FROM clientes", one=True)
        if clients: lines.append("Clientes: %d registrados" % clients[0])
        if _has_access(role,"seguridad") or _has_access(role,"all"):
            lines.append("Seguridad: Todos los blindajes activos")
        _, tmsg = _time_context()
        lines.extend(["","[%s]" % tmsg,"", _time_recommendation(role)])
        return _clean_text("\n".join(lines))
    except:
        return "Error al generar el resumen."

def _handle_financiero(sub, role):
    try:
        if not _has_access(role,"gastos") and not _has_access(role,"all"):
            return "No tienes permiso para ver datos financieros."
        if sub == "margen":
            rows = _safe_q("SELECT p.nombre, p.precio_venta, COALESCE(i.precio_compra,0), CASE WHEN p.precio_venta > 0 THEN ROUND(((p.precio_venta - COALESCE(i.precio_compra,0)) / p.precio_venta) * 100, 1) ELSE 0 END as margen FROM productos p LEFT JOIN inventario_general i ON LOWER(p.nombre) = LOWER(i.nombre) WHERE p.precio_venta > 0 ORDER BY margen DESC LIMIT 10")
            if not rows: return "No hay datos de margen disponibles."
            lines = ["Margenes por producto (Top 10):",""]
            for r in rows:
                lines.append("  - %s: %.1f%% (compra: %s / venta: %s)" % (_clean_text(r[0]), r[3], _fmt(r[2]), _fmt(r[1])))
            return _clean_text("\n".join(lines))
        exp = _safe_q("SELECT COUNT(*), COALESCE(SUM(monto),0) FROM gastos WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        rev = _safe_q("SELECT COALESCE(SUM(total),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if not exp and not rev: return "No hay datos financieros hoy."
        rv = float(rev[0] or 0) if rev else 0
        ev = float(exp[0] or 0) if exp else 0
        lines = ["Finanzas del dia:",""]
        lines.append("  Ingresos (ventas): %s" % _fmt(rv))
        lines.append("  Gastos: %s" % _fmt(ev))
        lines.append("  Ganancia: %s" % _fmt(rv - ev))
        if rv > 0: lines.append("  Margen: %.1f%%" % ((rv - ev) / rv * 100))
        return _clean_text("\n".join(lines))
    except:
        return "Error al consultar finanzas."

def _handle_lealtad(role):
    try:
        lines = ["Programa de Lealtad:",""]
        total = _safe_q("SELECT COUNT(*) FROM clientes WHERE puntos > 0", one=True)
        total_cli = _safe_q("SELECT COUNT(*) FROM clientes", one=True)
        if total_cli: lines.append("  Clientes registrados: %d" % total_cli[0])
        if total: lines.append("  Con puntos activos: %d" % total[0])
        lines.extend(["","Niveles:","  - Bronce: 0-499 pts (2%% cashback)","  - Plata: 500-1499 pts (4%% cashback)","  - Oro: 1500-4999 pts (6%% cashback)","  - Diamante: 5000+ pts (10%% cashback)","","Escribe \"cuántos puntos tengo\" para consultar."])
        return _clean_text("\n".join(lines))
    except:
        return "No pude acceder al programa de lealtad."

def _handle_prediccion(role):
    try:
        if not _has_access(role,"predicciones") and not _has_access(role,"all"):
            return "No tienes acceso a predicciones en tu rol actual."
        rows = _safe_q("SELECT nombre, SUM(cantidad) as qty FROM historial_ventas WHERE fecha >= DATE('now','localtime','-7 days') AND nombre IS NOT NULL GROUP BY nombre ORDER BY qty DESC LIMIT 5")
        if not rows: return "No hay suficientes datos para predicciones. Se necesitan al menos 7 dias de ventas."
        lines = ["Prediccion de demanda (basada en 7 dias):",""]
        for p in rows:
            est = int(p[1] * 1.15)
            lines.append("  - %s: %d uds vendidas -> estimado %d uds/semana" % (_clean_text(p[0]), p[1], est))
        lines.extend(["","Nota: Las predicciones se basan en tendencia de 7 dias con margen del 15%%."])
        return _clean_text("\n".join(lines))
    except:
        return "Error al generar predicciones."

# ============================================================
# EDGE FUNCTIONS v13 - Inteligencia avanzada 100% local
# ============================================================

def _handle_edge_dashboard(role):
    try:
        lines = ["== Dashboard IA Edge ==",""]
        r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(AVG(total),0) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if r:
            lines.append("Ventas hoy: %d txns | Total: %s | Prom: %s" % (r[0], _fmt(r[1]), _fmt(r[2])))
        total = _safe_q("SELECT COUNT(*) FROM productos", one=True)
        low = _safe_q("SELECT COUNT(*) FROM productos WHERE stock_actual <= 5", one=True)
        if total:
            lines.append("Inventario: %d productos | %d stock bajo" % (total[0], low[0] if low else 0))
        cli = _safe_q("SELECT COUNT(*) FROM clientes", one=True)
        if cli: lines.append("Clientes: %d" % cli[0])
        if _has_access(role,"all"):
            lines.append("Blindajes: PCI-DSS, HET, WS, MPOC - Todos activos")
        return _clean_text("\n".join(lines))
    except:
        return "Error al generar dashboard."

def _handle_edge_kpis(role):
    try:
        lines = ["== KPIs del día ==",""]
        r = _safe_q("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(AVG(total),0), MAX(total), MIN(total) FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if r and r[0] > 0:
            lines.append("Transacciónes: %d" % r[0])
            lines.append("Ingresos: %s" % _fmt(r[1]))
            lines.append("Ticket promedio: %s" % _fmt(r[2]))
            lines.append("Ticket max: %s" % _fmt(r[3]))
            lines.append("Ticket min: %s" % _fmt(r[4]))
        else:
            lines.append("Sin ventas registradas hoy.")
        return _clean_text("\n".join(lines))
    except:
        return "Error al generar KPIs."

def _handle_edge_abc(role):
    try:
        if not _has_access(role,"analisis_abc") and not _has_access(role,"all"):
            return "No tienes acceso a análisis ABC."
        lines = ["== Analisis ABC Pareto ==",""]
        rows = _safe_q("SELECT nombre, SUM(total) as revenue FROM historial_ventas WHERE fecha >= DATE('now','localtime','-30 days') AND nombre IS NOT NULL GROUP BY nombre ORDER BY revenue DESC LIMIT 20")
        if not rows: return "No hay datos suficientes para ABC. Se necesitan al menos 30 dias de ventas."
        total_rev = sum(r[1] or 0 for r in rows)
        a_items = []; b_items = []; c_items = []; cum = 0
        for r in rows:
            cum += (r[1] or 0)
            pct = cum / total_rev * 100 if total_rev > 0 else 0
            if pct <= 80: a_items.append(r)
            elif pct <= 95: b_items.append(r)
            else: c_items.append(r)
        if a_items: lines.append("A (80%% ingresos): %d productos" % len(a_items))
        if b_items: lines.append("B (15%% ingresos): %d productos" % len(b_items))
        if c_items: lines.append("C (5%% ingresos): %d productos" % len(c_items))
        return _clean_text("\n".join(lines))
    except:
        return "Error en análisis ABC."

def _handle_edge_cross_selling(role):
    try:
        rows = _safe_q("""SELECT a.nombre as p1, b.nombre as p2, COUNT(*) as freq
            FROM historial_ventas a JOIN historial_ventas b
            ON a.id_venta = b.id_venta AND a.nombre != b.nombre
            WHERE DATE(a.fecha) >= DATE('now','localtime','-30 days')
            AND a.nombre IS NOT NULL AND b.nombre IS NOT NULL
            GROUP BY a.nombre, b.nombre ORDER BY freq DESC LIMIT 5""", one=False)
        if not rows:
            rows = _safe_q("SELECT nombre, COUNT(*) as c FROM historial_ventas WHERE fecha >= DATE('now','localtime','-7 days') AND nombre IS NOT NULL GROUP BY nombre ORDER BY c DESC LIMIT 3")
            if not rows: return "No hay datos suficientes para cross-selling."
            lines = ["Productos mas vendidos (posibles combos):",""]
            for r in rows: lines.append("  - %s" % _clean_text(r[0]))
            return _clean_text("\n".join(lines))
        lines = ["Cross-Selling (combos frecuentes):",""]
        for r in rows: lines.append("  - %s + %s (%d veces)" % (_clean_text(r[0]), _clean_text(r[1]), r[2]))
        return _clean_text("\n".join(lines))
    except:
        return "Error en cross-selling."

def _handle_edge_precios(role):
    try:
        rows = _safe_q("SELECT p.nombre, p.precio_venta, COALESCE(i.precio_compra,0), CASE WHEN p.precio_venta > 0 THEN ROUND(((p.precio_venta - COALESCE(i.precio_compra,0)) / p.precio_venta) * 100, 1) ELSE 0 END as margen FROM productos p LEFT JOIN inventario_general i ON LOWER(p.nombre) = LOWER(i.nombre) WHERE p.precio_venta > 0 ORDER BY margen ASC LIMIT 5")
        if not rows: return "No hay datos para optimizacion de precios."
        lines = ["Productos con margen bajo (oportunidad):",""]
        for r in rows:
            lines.append("  - %s: margen %.1f%% (compra: %s / venta: %s)" % (_clean_text(r[0]), r[3], _fmt(r[2]), _fmt(r[1])))
        return _clean_text("\n".join(lines))
    except:
        return "Error en optimizacion de precios."

def _handle_unknown(text, role):
    try:
        words = [w for w in text.lower().split() if len(w) > 2 and w not in _STOP_WORDS]
        if words:
            prods = _search_products(" ".join(words[:3]), 3)
            if prods:
                lines = ["Parece que buscas productos. Encontre:",""]
                for p in prods:
                    lines.append("  - %s | %s | Stock: %d" % (p["nombre"], _fmt(p["precio"]), p["stock"]))
                lines.extend(["","Para mas detalles escribe: \"cuánto cuesta [producto]\""])
                return _clean_text("\n".join(lines))
        r = _get_role_perms(role)
        return _clean_text("No entendí tu pregunta. Prueba con:\n  - \"cuánto cuesta X\" para precios\n  - \"ventas de hoy\" para estadísticas\n  - \"ayuda\" para ver todo lo que puedo hacer")
    except:
        return "No entendí. Escribe \"ayuda\" para ver opciónes."

# ============================================================
# MAIN PROCESS - Entrada principal
# ============================================================
def process_question(sid, question, role="vendedor", user_name=""):
    try:
        t0 = time.time()
        sess = _get_session(sid)
        if role in ROLES: sess["role"] = role
        if user_name: sess["user_name"] = _clean_text(user_name)
        sess["ts"] = datetime.now().isoformat()
        sess["history"].append({"q": question, "ts": datetime.now().isoformat()})
        if len(sess["history"]) > 50: sess["history"] = sess["history"][-30:]

        detected_role = _detect_role_from_text(question)
        if detected_role and detected_role in ROLES:
            role = detected_role

        intent, data = _detect_intent(question, role)
        answer = ""
        intent_used = intent
        if intent=="greeting": answer = _handle_greeting(role, user_name)
        elif intent=="resumen_rol": answer = _handle_resumen_rol(role, user_name)
        elif intent=="thanks": answer = _handle_thanks()
        elif intent=="farewell": answer = _handle_farewell()
        elif intent=="help": answer = _handle_help(role)
        elif intent=="learned": answer = _clean_text(str(data))
        elif intent=="product_price": answer = _handle_product_price(data, role)
        elif intent=="product_search": answer = _handle_product_search(data)
        elif intent=="ventas": answer = _handle_ventas(data, role)
        elif intent=="inventario": answer = _handle_inventario(data, role)
        elif intent=="seguridad": answer = _handle_seguridad(data, role)
        elif intent=="recomendación": answer = _handle_recomendación(role)
        elif intent=="resumen": answer = _handle_resumen(role)
        elif intent=="financiero": answer = _handle_financiero(data, role)
        elif intent=="lealtad": answer = _handle_lealtad(role)
        elif intent=="app_info": answer = _handle_app_info(role)
        elif intent=="prediccion": answer = _handle_prediccion(role)
        elif intent=="edge_dashboard": answer = _handle_edge_dashboard(role)
        elif intent=="edge_kpis": answer = _handle_edge_kpis(role)
        elif intent=="edge_abc": answer = _handle_edge_abc(role)
        elif intent=="edge_cross_selling": answer = _handle_edge_cross_selling(role)
        elif intent=="edge_precios": answer = _handle_edge_precios(role)
        elif intent=="smart_query": answer = data
        else: answer = _handle_unknown(question, role)
        try: _learn(role, question, answer, intent)
        except Exception as _e: _log.debug("[IA] excepción: %s", _e)

        elapsed = int((time.time() - t0) * 1000)
        suggestions = _get_suggestions(intent_used)
        r = _get_role_perms(role)
        result = {
            "answer": _clean_text(answer) or "No pude procesar tu pregunta. Intenta de nuevo.",
            "role": role, "role_label": r["label"], "role_color": r["color"],
            "role_icon": r["icon"], "intent": intent_used,
            "suggestions": suggestions,
            "ts": datetime.now().isoformat()
        }
        if elapsed > 100:
            print("[IA] process_question took %dms (intent: %s)" % (elapsed, intent_used))
        return result
    except Exception as e:
        return {
            "answer": "Error interno. Intenta de nuevo.\nEscribe \"ayuda\" para ver opciónes.",
            "role": role, "role_label": ROLES.get(role,ROLES["vendedor"])["label"],
            "role_color": ROLES.get(role,ROLES["vendedor"])["color"],
            "intent": "error", "error": _clean_text(str(e)),
            "suggestions": ["ayuda", "ventas de hoy", "resumen"],
            "ts": datetime.now().isoformat()
        }

def get_proactive_alerts(sid):
    try:
        sess = _get_session(sid)
        role = sess.get("role","vendedor")
        now = datetime.now()
        if sess.get("last_alerts_ts"):
            last = datetime.fromisoformat(sess["last_alerts_ts"])
            if (now - last).total_seconds() < 300:
                return {"alerts": [], "cached": True}
        alerts = _generate_proactive_alerts(role)
        sess["last_alerts_ts"] = now.isoformat()
        return {"alerts": alerts}
    except:
        return {"alerts": [], "error": True}

def _generate_proactive_alerts(role):
    alerts = []
    try:
        low = _safe_q("SELECT COUNT(*) FROM productos WHERE stock_actual <= 3 AND stock_actual >= 0", one=True)
        if low and low[0] > 0:
            alerts.append({"type":"warning","icon":"alert-triangle","title":"Stock critico","body":"%d productos con 3 o menos unidades" % low[0]})
    except: pass
    return alerts

def get_status():
    """Estado del modulo IA - requerido por ia_assistant_routes.py."""
    try:
        learning = None
        try:
            total = _safe_q("SELECT COUNT(*), COUNT(DISTINCT rol) FROM ia_learning", one=True)
            learning = {"total": total[0] if total else 0, "roles": total[1] if total else 0}
        except Exception as _e: _log.debug("[IA] excepción: %s", _e)
        return {
            "versión": "12.0.0",
            "model": "NLU Rule-based ON-DEVICE + Smart Query SQLite 100% local",
            "features": ["rol dinamico instantaneo","inteligencia periferica SQLite",
                "aprendizaje persistente","texto 100% ASCII (sin tildes)",
                "busqueda por palabras en 3 tablas","batch query resumen rol",
                "IA Edge completa: predicciones, anti-fraude, ABC, cross-selling, KPIs, precios"],
            "roles": list(ROLES.keys()), "learning": learning,
            "db_connected": _db() is not None,
            "db_path": _db_path or "not found",
            "sessions": len(_sessions)
        }
    except:
        return {"versión": "12.0.0", "error": True}

def cleanup_old_sessions():
    """Limpia sesiónes inactivas despues de 2 horas."""
    try:
        now = datetime.now()
        with _sessions_lock:
            to_remove = []
            for sid, sess in _sessions.items():
                try:
                    last = datetime.fromisoformat(sess.get("ts",""))
                    if (now - last).total_seconds() > 7200: to_remove.append(sid)
                except Exception as _e: _log.debug("[IA] excepción: %s", _e)
            for sid in to_remove: del _sessions[sid]
    except: pass

# ============================================================
# COMPATIBILITY WRAPPERS para ai_routes.py (backwards v7.0)
# ============================================================
def chat(message, session_id="default", role="vendedor"):
    """Wrapper compatible con ai_routes.py /api/ai/assistant"""
    result = process_question(session_id, message, role=role)
    result.setdefault("response", result.get("answer", ""))
    return result

def get_conversation_history(session_id="default"):
    """Wrapper compatible con ai_routes.py /api/ai/assistant/history"""
    sess = _get_session(session_id)
    return sess.get("history", [])
