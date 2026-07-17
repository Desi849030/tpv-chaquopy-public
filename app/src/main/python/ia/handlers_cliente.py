# -*- coding: utf-8 -*-
"""handlers_cliente.py v8.8 - Gestor universal adaptado al esquema real.

Esquema real:
- productos: producto_id (TEXT), nombre, precio, categoria, unidad_medida,
             en_oferta, imagen, activo
- inventario_general: producto_id, stock_actual, stock_minimo
- (no hay tabla tiendas)
"""

from datetime import datetime
import re
import unicodedata

from ia.handlers_base import _fm, _follow, _get_sug


def _normalizar(texto):
    """Quita tildes y convierte a minusculas para busqueda flexible."""
    if not texto:
        return ''
    t = unicodedata.normalize('NFD', str(texto))
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return t.lower().strip()


# ═══════════════════════════════════════════════════════════════
#  HELPERS — BD real
# ═══════════════════════════════════════════════════════════════

def _buscar_productos(consulta):
    """Busca productos (sin tilde, case-insensitive)."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        q_norm = _normalizar(consulta)
        # Buscar en tabla completa y filtrar en Python para ignorar tildes
        rows = conn.execute("""
            SELECT p.producto_id, p.nombre, p.precio, p.categoria,
                   p.unidad_medida,
                   COALESCE(p.en_oferta, 0) as en_oferta,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
            ORDER BY p.nombre
        """).fetchall()
        conn.close()
        # Filtrar por nombre o categoria normalizados
        resultados = []
        for r in rows:
            d = dict(r)
            nom = _normalizar(d.get('nombre', ''))
            cat = _normalizar(d.get('categoria', ''))
            if q_norm in nom or q_norm in cat:
                resultados.append(d)
        return resultados[:10]
    except Exception:
        return []


def _todas_ofertas():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        rows = conn.execute("""
            SELECT producto_id, nombre, precio, categoria, unidad_medida
            FROM productos
            WHERE COALESCE(activo, 1) = 1 AND COALESCE(en_oferta, 0) = 1
            ORDER BY precio LIMIT 15
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _stock_de(producto_nombre):
    """Devuelve [(nombre, stock), ...] para productos con stock."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        q_norm = _normalizar(producto_nombre)
        rows = conn.execute("""
            SELECT p.nombre, COALESCE(i.stock_actual, 0) as stock,
                   p.unidad_medida
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
        """).fetchall()
        conn.close()
        resultados = []
        for r in rows:
            d = dict(r)
            if q_norm in _normalizar(d.get('nombre', '')):
                if int(d.get('stock') or 0) > 0:
                    resultados.append(d)
        return resultados[:10]
    except Exception:
        return []


def _todas_categorias():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        rows = conn.execute("""
            SELECT categoria, COUNT(*) as total
            FROM productos
            WHERE COALESCE(activo, 1) = 1 AND categoria IS NOT NULL
              AND categoria != ''
            GROUP BY categoria ORDER BY total DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _contar_productos():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        n = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE COALESCE(activo,1)=1"
        ).fetchone()[0]
        conn.close()
        return int(n)
    except Exception:
        return 0


def _extraer_producto(texto):
    """Extrae el nombre del producto de la frase del usuario."""
    t = _normalizar(texto)
    stopwords = {
        'cuanto', 'cuesta', 'precio', 'vale', 'tienen', 'tienes',
        'hay', 'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del',
        'que', 'donde', 'tienda', 'producto', 'productos',
        'me', 'puedes', 'decir', 'mostrar', 'buscar', 'busca', 'muestra',
        'en', 'con', 'por', 'para', 'sobre', 'cual', 'algun',
        'algo', 'tiene', 'esta', 'estan', 'disponible', 'disponibles',
        'algunos', 'algunas', 'cualquier', 'cualquiera', 'esto', 'eso',
        'esa', 'ese', 'sus', 'mis', 'tus', 'nos'
    }
    palabras = re.findall(r'[a-z]+', t)
    relevantes = [p for p in palabras if p not in stopwords and len(p) > 2]
    return ' '.join(relevantes).strip()


# ═══════════════════════════════════════════════════════════════
#  HANDLER PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def handle_cliente(agent, t, ctx=None):
    """Handler universal — datos REALES de la BD."""
    NL = "\n"
    tl = _normalizar(t)

    name = ''
    if isinstance(ctx, dict):
        name = ctx.get('name', '') or ctx.get('nombre', '')
    elif isinstance(ctx, str):
        name = ctx

    # ─── SALUDO ─────────────────────────────────────────────────
    if any(k in tl for k in ['hola', 'buenas', 'hey', 'buenos dias',
                              'buenas tardes', 'buenas noches']):
        h = datetime.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        n = name or ''
        return (s + " " + n + " 🛍️. Soy tu asistente. Puedo ayudarte a buscar "
                "productos, ver precios, ofertas, categorías o consultar "
                "stock. ¿Qué necesitas?")

    # ─── OFERTAS ────────────────────────────────────────────────
    if any(k in tl for k in ['oferta', 'descuento', 'rebaja', 'promocion']):
        ofertas = _todas_ofertas()
        if not ofertas:
            return "🏷️ No hay ofertas activas en este momento. ¡Vuelve pronto!"
        msg = "🏷️ Tenemos " + str(len(ofertas)) + " ofertas activas:" + NL + NL
        for o in ofertas[:8]:
            msg += "• " + str(o.get('nombre', '?'))
            msg += " — $" + str(o.get('precio', 0))
            if o.get('unidad_medida'):
                msg += " / " + str(o['unidad_medida'])
            msg += NL
        return msg

    # ─── TIENDAS / HORARIOS ────────────────────────────────────
    if any(k in tl for k in ['tienda', 'tiendas', 'sucursal', 'donde estan',
                              'ubicacion', 'direccion', 'horario', 'horarios']):
        return ("🏪 **Tienda Principal**" + NL +
                "🕐 Horario: 08:00 - 20:00" + NL +
                "📍 Para dirección exacta consulta con el personal." + NL +
                NL + "¿Quieres saber si tenemos algún producto en particular?")

    # ─── CATEGORÍAS ────────────────────────────────────────────
    if any(k in tl for k in ['categoria', 'categorias', 'tipos de producto',
                              'que vendes', 'que venden']):
        cats = _todas_categorias()
        if not cats:
            return "📂 No hay categorías disponibles."
        msg = "📂 " + str(len(cats)) + " categorías disponibles:" + NL + NL
        for c in cats[:15]:
            msg += "• " + str(c.get('categoria', '?'))
            msg += " (" + str(c.get('total', 0)) + " productos)" + NL
        msg += NL + "Pregúntame por una en particular, ej. 'productos de Bebidas'"
        return msg

    # ─── PRODUCTOS DE UNA CATEGORÍA ─────────────────────────────
    cats_disponibles = [_normalizar(c['categoria']) for c in _todas_categorias()]
    for cat in cats_disponibles:
        if cat and cat in tl and len(cat) > 3:
            try:
                from db_connection import obtener_conexion
                conn = obtener_conexion()
                rows = conn.execute("""
                    SELECT nombre, precio, unidad_medida
                    FROM productos
                    WHERE COALESCE(activo,1)=1 AND LOWER(categoria) LIKE ?
                    ORDER BY nombre LIMIT 15
                """, ('%' + cat + '%',)).fetchall()
                conn.close()
                if rows:
                    msg = "📂 Productos en categoría '" + cat.title() + "':" + NL + NL
                    for r in rows:
                        msg += "• " + str(r['nombre'])
                        msg += " — $" + str(r['precio'])
                        if r['unidad_medida']:
                            msg += " / " + str(r['unidad_medida'])
                        msg += NL
                    return msg
            except Exception:
                pass

    # ─── EN QUÉ TIENDA / DÓNDE HAY X ────────────────────────────
    if any(k in tl for k in ['en que tienda', 'donde hay', 'que tienda tiene',
                              'donde puedo encontrar', 'donde lo consigo',
                              'donde esta', 'donde se vende']):
        producto = _extraer_producto(tl)
        if not producto:
            return "🔍 Dime qué producto buscas y te digo si tenemos stock."
        items = _stock_de(producto)
        if not items:
            return ("😕 No encontré '" + producto + "' con stock disponible. "
                    "¿Probamos otro nombre?")
        msg = "📍 '" + str(items[0].get('nombre', producto)) + "' disponible en:" + NL + NL
        for it in items[:5]:
            stock = int(it.get('stock') or 0)
            msg += "• Tienda Principal — " + str(stock) + " "
            msg += str(it.get('unidad_medida') or 'unidades') + NL
        return msg

    # ─── PRECIO / CUÁNTO CUESTA ────────────────────────────────
    if any(k in tl for k in ['cuanto cuesta', 'precio', 'vale', 'cuanto vale',
                              'cuesta']):
        producto = _extraer_producto(tl)
        if not producto:
            return "💰 Dime de qué producto quieres saber el precio."
        items = _buscar_productos(producto)
        if not items:
            return "😕 No encontré '" + producto + "' en el catálogo. ¿Otro nombre?"
        if len(items) == 1:
            p = items[0]
            msg = "💰 **" + str(p.get('nombre', '?')) + "**: $" + str(p.get('precio', 0))
            if p.get('unidad_medida'):
                msg += " / " + str(p['unidad_medida'])
            stock = int(p.get('stock_total') or 0)
            if stock > 0:
                msg += NL + "📦 Stock: " + str(stock) + " disponibles"
            else:
                msg += NL + "⚠️ Sin stock actualmente"
            if p.get('en_oferta'):
                msg += NL + "🏷️ ¡En oferta!"
            return msg
        msg = "🔍 Encontré " + str(len(items)) + " productos con '" + producto + "':" + NL + NL
        for p in items[:8]:
            msg += "• **" + str(p.get('nombre', '?')) + "**"
            msg += " — $" + str(p.get('precio', 0))
            if p.get('en_oferta'):
                msg += " 🏷️"
            msg += NL
        return msg

    # ─── BUSCAR / TIENEN X ─────────────────────────────────────
    if any(k in tl for k in ['tienen', 'tienes', 'hay', 'busca', 'buscar',
                              'mostrar', 'muestrame', 'muestra']):
        producto = _extraer_producto(tl)
        if not producto:
            return "🔍 Dime qué producto buscas."
        items = _buscar_productos(producto)
        if not items:
            return ("😕 No tenemos '" + producto + "' en este momento. "
                    "¿Buscas algo parecido?")
        msg = "✅ Encontré " + str(len(items)) + " producto(s) con '"
        msg += producto + "':" + NL + NL
        for p in items[:8]:
            stock = int(p.get('stock_total') or 0)
            disp = "✓ disponible" if stock > 0 else "✗ agotado"
            msg += "• **" + str(p.get('nombre', '?')) + "**"
            msg += " — $" + str(p.get('precio', 0)) + " (" + disp + ")" + NL
        return msg

    # ─── CATÁLOGO COMPLETO ─────────────────────────────────────
    if any(k in tl for k in ['catalogo', 'que productos tienen',
                              'todos los productos', 'lista de productos',
                              'que vendes', 'que venden']):
        n = _contar_productos()
        cats = _todas_categorias()
        msg = ("📦 Tenemos **" + str(n) + " productos** organizados en "
               + str(len(cats)) + " categorías." + NL + NL)
        if cats:
            msg += "Categorías principales:" + NL
            for c in cats[:6]:
                msg += "• " + str(c['categoria']) + " (" + str(c['total']) + ")" + NL
        msg += NL + "Dime qué buscas, ej. 'café', 'aceite', 'leche'..."
        return msg

    # ─── AYUDA ─────────────────────────────────────────────────
    if any(k in tl for k in ['ayuda', 'help', 'que puedes hacer',
                              'opciones', 'menu']):
        return ("🤝 Puedo ayudarte con:" + NL +
                "• 🔍 Buscar productos (ej. 'tienen café')" + NL +
                "• 💰 Precios (ej. 'cuánto cuesta el aceite')" + NL +
                "• 🏷️ Ofertas activas" + NL +
                "• 📦 Stock disponible" + NL +
                "• 📂 Categorías y sus productos" + NL +
                "• 🏪 Horarios de tienda")

    # ─── DEFAULT: buscar lo que escribió ───────────────────────
    if len(tl) > 2:
        items = _buscar_productos(tl)
        if items:
            msg = "🔍 Encontré esto con tu búsqueda:" + NL + NL
            for p in items[:5]:
                msg += "• **" + str(p.get('nombre', '?')) + "**"
                msg += " — $" + str(p.get('precio', 0))
                if p.get('en_oferta'):
                    msg += " 🏷️"
                stock = int(p.get('stock_total') or 0)
                if stock > 0:
                    msg += f" ({stock} uds)"
                msg += NL
            # v12_mejora: sugerir productos relacionados
            if items and len(items) >= 1:
                try:
                    cat_primera = items[0].get('categoria', '')
                    if cat_primera:
                        msg += NL + f"📂 Más en *{cat_primera}*: pregúntame 'productos de {cat_primera}'"
                except Exception:
                    pass
            return msg

    # ─── MENSAJE POR DEFECTO CON CATEGORÍAS (v12_mejora) ───────
    n = _contar_productos()
    cats = _todas_categorias()
    if cats:
        msg = (f"🛍️ Tenemos **{n} productos** en {len(cats)} categorías:" + NL + NL)
        for c in cats[:5]:
            msg += f"• {c['categoria']} ({c['total']} productos)" + NL
        msg += NL + "Pregúntame por cualquier producto o categoría."
        return msg

    return ("🛍️ ¿En qué te ayudo? Puedes preguntarme por productos, precios, "
            "ofertas, categorías o stock. Escribe 'ayuda' para opciones.")
