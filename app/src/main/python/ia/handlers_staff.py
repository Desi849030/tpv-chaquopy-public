"""handlers_staff.py - Extracted from handlers.py"""
"Role-specific IA handlers for TPV Smart."""
from datetime import datetime
from ia.db_utils import q, fmt_money, pct
from ia.catalog import P, O
from ia.metrics import F, M

try:
    from ia.normalizer import contains_any
    _HAS_NORM = True
except Exception:
    _HAS_NORM = False

try:
    from ia.intent_engine import get_suggestións as _get_suggestións
    _HAS_INTENT = True
except Exception:
    _HAS_INTENT = False


from ia.handlers_base import _fm, _follow, _get_sug

# ================================================================
def handle_vendedor(agent, t, m=None):
    name = m if isinstance(m, str) else ''

    # Saludo personalizado
    if _fm(agent, t, ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'buenas', 'que tal', 'saludos', 'hey']):
        from datetime import datetime as _dt
        h = _dt.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        nm = f", {name}" if name else ""
        return (f"{s}{nm} 🛒. Soy tu asistente de ventas. "
                f"Puedo ayudarte con: tus ventas de hoy, stock bajo, productos "
                f"más vendidos o el precio de cualquier producto. ¿Qué necesitas?")

    # Agradecimiento
    if _fm(agent, t, ['gracias', 'genial', 'perfecto', 'adios', 'hasta luego', 'chao']):
        return "¡Con gusto! Aquí estoy para lo que necesites. 👍"

    if _fm(agent, t, ["ventas","caja","recaudó","cuánto vendí","cuanto vendi","cómo voy","como voy"]):
        d = F.diario()
        if d['t'] == 0:
            return "Todavía no hay ventas hoy. ¡A vender! 💪"
        h = datetime.now().hour
        proy = d['r'] / h * 24 if h > 0 else d['r']
        return (f"Al momento: {d['t']} ventas, {fmt_money(d['r'])} facturados. "
                f"Ticket promedio: {fmt_money(d['a'])}. "
                f"Proyección cierre: {fmt_money(proy)}.")

    if _fm(agent, t, ["stock bajo","agotado","crítico","reabastecer"]):
        rows = q("SELECT nombre,stock_actual FROM inventario_general "
                 "WHERE stock_actual<=5 AND stock_actual>=0 "
                 "ORDER BY stock_actual LIMIT 500")
        if rows:
            msg = "Atencion: " + str(len(rows)) + " productos necesitan reabastecimiento:\n"
            for r in rows[:20]:
                msg += "- " + r["nombre"] + ": " + str(int(r["stock_actual"])) + " uds\n"
            return msg + "\nDesea generar orden de pedido?"
        return "Todo en orden. No hay stock bajo."

    if _fm(agent, t, ["top","más vendido","popular","ranking"]):
        top = F.top(7, 5)
        if not top:
            return "Aún no hay historial suficiente esta semana."
        msg = "Más vendidos (7 días):\n"
        for i, r in enumerate(top, 1):
            msg += (str(i) + ". " + r["nombre"] + ": " +
                    str(int(r["q"])) + " uds (" + fmt_money(r["t"]) + ")\n")
        return msg

    # Búsqueda de producto (limpia palabras de relleno: 'precio del cafe' -> 'cafe')
    import re as _re
    _term = _re.sub(r'\b(precio|costo|valor|cuanto|cuánto|cuesta|vale|de|del|la|el|los|las|hay|tienes|tiene|stock)\b',
                    ' ', t.lower()).strip()
    prods = P.search(_term or t, 10)
    if prods:
        msg = "Productos:\n"
        for p in prods[:10]:
            mrg = ((p['p'] - p['c']) / p['p'] * 100) if p['p'] > 0 and p['c'] > 0 else 0
            msg += ("- " + p["n"] + ": " + fmt_money(p["p"]) +
                    " | Stock: " + str(int(p["s"]))
                    + (" | Margen: " + pct(mrg) if mrg > 0 else "") + "\n")
        return msg

    return ("Dime qué necesitas: tus ventas, stock bajo, productos más vendidos, "
            "o el nombre de un producto.\n\n" + _follow("vendedor"))


# ================================================================
# SUPERVISOR
# ================================================================
def handle_supervisor(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    d = F.diario()
    w = F.semanal()
    low = sum(1 for p in P.cache if 0 < p['s'] <= 5)

    # Saludo personalizado
    if _fm(agent, t, ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'buenas', 'que tal', 'saludos', 'hey']):
        from datetime import datetime as _dt
        h = _dt.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        nm = f", {name}" if name else ""
        return (f"{s}{nm} 👁️. Soy tu asistente de supervisión. Puedo darte el "
                f"dashboard, ventas del día, stock bajo y tendencias. ¿Qué reviso?")
    if _fm(agent, t, ['gracias', 'genial', 'perfecto', 'adios', 'hasta luego', 'chao']):
        return "¡Con gusto! Aquí estoy para lo que necesites. 👍"

    if _fm(agent, t, ["ayuda","qué puedes","menu","opciones"]):
        return ("Como supervisor tienes acceso completo:\n\n"
                "- dashboard: KPIs\n"
                "- ventas: Resumen del dia\n"
                "- stock bajo: Alertas\n"
                "- top: Más vendidos\n"
                "- finanzas: Balance y margen\n"
                "- gastos: Egresos\n"
                "- predicciones: Tendencías\n"
                "- rotación: Indice\n"
                "- ABC: Clasificación\n"
                "- ofertas: Promociones\n"
                "- Nombre de producto para info detallada")

    if _fm(agent, t, ["dashboard","resumen","estado","kpi"]):
        msg = ("Dashboard:\n"
               "- Ventas hoy: " + fmt_money(d["r"]) + " (" + str(d["t"]) + " ops)\n"
               "- Ventas semana: " + fmt_money(w["r"]) + "\n"
               "- Ticket promedio: " + fmt_money(d["a"]) + "\n"
               "- Productos: " + str(len(P.cache)) + "\n"
               "- Stock bajo: " + str(low) + "\n"
               "- Categorias: " + str(len(P.cats)))
        if d["t"] > 0:
            h = datetime.now().hour
            proy = d['r'] / h * 24 if h > 0 else d['r']
            msg += "\n- Proyección cierre: " + fmt_money(proy)
        return msg

    if _fm(agent, t, ["ventas","caja","recaudó","cuánto vendí","cómo voy"]):
        if d['t'] == 0:
            return "Aún no hay ventas hoy."
        h = datetime.now().hour
        proy = d['r'] / h * 24 if h > 0 else d['r']
        return ("Ventas del dia:\n"
                "- Ops: " + str(d['t']) + "\n"
                "- Facturado: " + fmt_money(d['r']) + "\n"
                "- Ticket: " + fmt_money(d['a']) + "\n"
                "- Proyección: " + fmt_money(proy) + "\n"
                "- Gastos: " + fmt_money(d['g']) + "\n"
                "- Ganancía: " + fmt_money(d['r'] - d['g']))

    if _fm(agent, t, ["stock bajo","agotado","crítico","reabastecer","faltante"]):
        rows = q("SELECT nombre,stock_actual FROM inventario_general "
                 "WHERE stock_actual<=5 AND stock_actual>=0 "
                 "ORDER BY stock_actual LIMIT 500")
        if not rows:
            return "Todo en orden. No hay productos con stock bajo."
        msg = "Alerta: " + str(len(rows)) + " productos necesitan reabastecimiento:\n\n"
        for r in rows[:20]:
            icon = "X" if r["stock_actual"] == 0 else "!"
            msg += " [" + icon + "] " + r["nombre"] + ": " + str(int(r["stock_actual"])) + " uds\n"
        return msg + "\nDesea generar orden de pedido?"

    if _fm(agent, t, ["top","más vendido","popular","ranking","mejor","vendidos"]):
        top = F.top(7, 5)
        if not top:
            return "Aún no hay suficiente historial."
        msg = "Más vendidos (7 días):\n\n"
        for i, r in enumerate(top, 1):
            msg += (str(i) + ". " + r["nombre"] + ": " +
                    str(int(r["q"])) + " uds (" + fmt_money(r["t"]) + ")\n")
        return msg

    if _fm(agent, t, ["finanza","margen","gasto","ingreso","balance","ganancía","rentabilidad"]):
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        return ("Finanzas:\n\n"
                "- Ingresos: " + fmt_money(d['r']) + "\n"
                "- Gastos: " + fmt_money(d['g']) + "\n"
                "- Ganancía: " + fmt_money(prof) + "\n"
                "- Margen: " + pct(margen) + "\n"
                "- Ticket: " + fmt_money(d['a']))

    if _fm(agent, t, ["gasto","egreso","gastos","costo"]):
        rows = q("SELECT descripcion,monto,categoría FROM gastos "
                 "WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
        if not rows:
            return "No hay gastos hoy."
        msg = "Gastos del dia (" + str(len(rows)) + "):\n\n"
        total = 0
        for r in rows[:20]:
            msg += ("- " + str(r["descripcion"]) + ": " + fmt_money(r["monto"]) +
                    " (" + str(r["categoría"]) + ")\n")
            total += r["monto"]
        return msg + "\nTotal: " + fmt_money(total)

    if _fm(agent, t, ["tendencia","predicción","proyección","forecast","pronóstico"]):
        proy = d['r'] * 7 if d['r'] > 0 else w['r']
        return ("Proyección semanal: " + fmt_money(proy) + "\n"
                "- Ritmo diario: " + fmt_money(d['r']) + "\n"
                "- Semana: " + fmt_money(w['r']))

    if _fm(agent, t, ["rotación","índice"]):
        cv = q("SELECT COALESCE(SUM(cantidad*costo),0) cv "
               "FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
        ip = sum(p['c'] * p['s'] for p in P.cache) / len(P.cache) if P.cache else 1
        rot = (cv['cv'] / ip) if ip > 0 else 0
        msg = "Rotación (30 días): " + str(round(rot, 2)) + " veces"
        if rot > 4:
            msg += "\nExcelente: inventario se renueva rápido."
        elif rot > 1:
            msg += "\nNormal: buen ritmo."
        else:
            msg += "\nBaja: considere promociónes."
        return msg

    if _fm(agent, t, ["abc","pareto","clasificación"]):
        abc = F.abc()
        if not abc["A"]:
            return "Necesito al menos 30 días para análisis ABC."
        msg = "Analisis ABC:\n\n"
        msg += "- A (80%): " + str(len(abc["A"])) + " productos"
        if abc["A"]:
            msg += "\n  Top: " + abc["A"][0]
        msg += "\n- B (15%): " + str(len(abc["B"])) + " productos"
        msg += "\n- C (5%): " + str(len(abc["C"])) + " productos"
        return msg

    if _fm(agent, t, ["eoq","lote optimo","pedido óptimo"]):
        top = F.top(30, 1)
        if top:
            demanda = top[0]["q"] * 12
            eoq = M.eoq(demanda, 50, 10)
            return ("Lote óptimo " + top[0]["nombre"] + ":\n"
                    "- EOQ: " + str(int(eoq)) + " uds/pedido\n"
                    "- Demanda anual: " + str(int(demanda)) + " uds")
        return "Necesito más datos de ventas para EOQ."

    if _fm(agent, t, ["oferta","descuento","rebaja","promo"]):
        of = O.mejores()
        if not of:
            return "No hay productos con margen para ofertas."
        msg = "Productos para oferta:\n\n"
        for i, o in enumerate(of, 1):
            msg += (str(i) + ". " + o["n"] + ": " + fmt_money(o["p"]) +
                    " -> " + fmt_money(o["d"]) + " (" + pct(o["m"]) + ")\n")
        return msg

    import re as _re
    _term = _re.sub(r'\b(precio|costo|valor|cuanto|cuánto|cuesta|vale|de|del|la|el|los|las|hay|tienes|tiene|stock)\b',
                    ' ', t.lower()).strip()
    prods = P.search(_term or t, 10)
    if prods:
        msg = "Productos:\n\n"
        for p in prods[:10]:
            mrg = ((p['p'] - p['c']) / p['p'] * 100) if p['p'] > 0 and p['c'] > 0 else 0
            msg += ("- " + p["n"] + ": " + fmt_money(p["p"]) +
                    " | Stock: " + str(int(p["s"]))
                    + (" | Margen: " + pct(mrg) if mrg > 0 else "") + "\n")
        return msg

    return ("Escriba: ventas, stock bajo, top, finanzas, gastos, predicciones, "
            "ABC, rotación, ofertas, EOQ, o nombre de producto.\n\n" +
            _follow("supervisor"))


# ================================================================
# ADMINISTRADOR
# ================================================================
def handle_admin(agent, t, name):
    d = F.diario()
    low = sum(1 for p in P.cache if 0 < p['s'] <= 5)
    n = f", {name}" if name else ""

    if _fm(agent, t, ['finanza','margen','gasto','ingreso','balance','ganancía','comisión','rentabilidad']):
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        comisión = d['r'] * 0.05 if d['r'] > 0 else 0
        msg = (f"Estimado administrador{n}, aquí tiene el balance del día:\n\n"
               f"Ingresos por ventas: {fmt_money(d['r'])}\n"
               f"Gastos registrados: {fmt_money(d['g'])}\n"
               f"Ganancía bruta: {fmt_money(prof)}\n"
               f"Margen neto: {pct(margen)}\n"
               f"Comisión estimada (5%): {fmt_money(comisión)}\n\n")
        if prof > d['g'] * 2:
            msg += "Excelente rentabilidad hoy! El negocio esta generando buenas ganancías."
        elif prof > 0:
            msg += "Buen desempeño. Las ganancías cubren los gastos del día."
        else:
            msg += "Atención: los gastos superan los ingresos. Revise las finanzas."
        return msg

    if _fm(agent, t, ['abc','pareto','clasificación']):
        abc = F.abc()
        if not abc['A']:
            return "Necesito al menos 30 días de ventas para el análisis ABC."
        msg = "Analisis ABC de productos (últimos 30 días):\n\n"
        msg += "- A (80% ingresos): " + str(len(abc['A'])) + " productos"
        if abc['A']:
            msg += "\n   Top: " + abc['A'][0]
        msg += "\n- B (siguiente 15%): " + str(len(abc['B'])) + " productos"
        msg += "\n- C (ultimo 5%): " + str(len(abc['C'])) + " productos\n\n"
        msg += "Concéntrese en los productos A para maximizar ganancías."
        return msg

    if _fm(agent, t, ['punto equilibrio','break even','umbral']):
        gf = d['g'] if d['g'] > 0 else 100
        pp = sum(p['p'] for p in P.cache) / len(P.cache) if P.cache else 10
        pc = sum(p['c'] for p in P.cache) / len(P.cache) if P.cache else 5
        pe = M.punto_eq(gf, pp, pc)
        msg = "Punto de equilibrio diario:\n\n"
        msg += f"Necesita vender: {pe} unidades\n"
        msg += f"Para cubrir: {fmt_money(gf)} de gastos fijos\n"
        msg += f"Precio promedio: {fmt_money(pp)}\n"
        msg += f"Costo promedio: {fmt_money(pc)}\n"
        return msg

    if _fm(agent, t, ['eoq','lote optimo','pedido óptimo']):
        top = F.top(30, 1)
        if top:
            demanda = top[0]['q'] * 12
            eoq = M.eoq(demanda, 50, 10)
            return (f"Lote óptimo para {top[0]['nombre']}:\n"
                    f"EOQ: {eoq:.0f} unidades/pedido\n"
                    f"Demanda anual estimada: {demanda:.0f} unidades\n")
        return "Necesito más datos. Mientras mas ventas se registren, mas preciso será el calculculo."

    if _fm(agent, t, ['predicción','pronóstico','proyección','forecast','tendencia']):
        rows = q("SELECT DATE(fecha) d,SUM(total) r FROM historial_ventas "
                 "WHERE fecha>=DATE('now','-7 days') GROUP BY DATE(fecha) ORDER BY d")
        if rows and len(rows) >= 3:
            x = list(range(len(rows)))
            y = [r['r'] for r in rows]
            mg, b = M.regresion(x, y)
            prox = max(0, mg * len(rows) + b)
            tend = "creciente" if mg > 0 else "decreciente"
            msg = "Analisis de tendencia:\n\n"
            msg += f"Tendencía: {tend}\n"
            msg += f"Cambio diario: {fmt_money(mg)}\n"
            msg += f"Próximo día estimado: {fmt_money(prox)}\n"
            msg += f"Proyección semanal: {fmt_money(prox * 7)}\n"
            return msg
        return "Necesito al menos 3 días de ventas para proyectar. Siga vendiendo y pronto tendremos datos."

    if _fm(agent, t, ['oferta','descuento','rebaja']):
        of = O.mejores()
        if not of:
            return "No hay productos con margen suficiente para ofertas. Revise los precios de compra."
        msg = "Productos ideales para poner en oferta:\n\n"
        for i, o in enumerate(of, 1):
            msg += (f"{i}. {o['n']}: Precio normal {fmt_money(o['p'])} -> "
                    f"Oferta {fmt_money(o['d'])} ({pct(o['m'])} margen)\n")
        return msg

    if _fm(agent, t, ['stock','inventario','crítico']):
        rows = q("SELECT nombre,stock_actual,precio_venta FROM inventario_general "
                 "WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 500")
        out = sum(1 for p in P.cache if p['s'] <= 0)
        msg = (f"Estado del inventario:\n\n"
               f"Total productos: {len(P.cache)}\n"
               f"Stock bajo: {low}\n"
               f"Agotados: {out}\n")
        if rows:
            msg += "\nProductos críticos:\n"
            for r in rows:
                msg += f"- {r['nombre']}: {r['stock_actual']:.0f} unidades\n"
            msg += "\nDesea generar órdenes de compra?"
        return msg

    if _fm(agent, t, ['rotación','índice rotación']):
        cv = q("SELECT COALESCE(SUM(cantidad*costo),0) cv "
               "FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
        ip = sum(p['c'] * p['s'] for p in P.cache) / len(P.cache) if P.cache else 1
        rot = (cv['cv'] / ip) if ip > 0 else 0
        msg = f"Indice de rotación (30 días): {rot:.2f} veces\n\n"
        if rot > 4:
            msg += "Excelente. El inventario se renueva rápidamente."
        elif rot > 1:
            msg += "Rotación normal. El inventario se mueve a buen ritmo."
        else:
            msg += "Rotación baja. Considere promociónes para mover el stock."
        return msg

    if _fm(agent, t, ['gasto','egreso','costo fijo']):
        rows = q("SELECT descripcion,monto,categoría FROM gastos "
                 "WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
        if not rows:
            return "No hay gastos registrados hoy."
        msg = f"Gastos del dia ({len(rows)}):\n\n"
        total = 0
        for r in rows:
            msg += f"- {r['descripcion']}: {fmt_money(r['monto'])} ({r['categoría']})\n"
            total += r['monto']
        msg += f"\nTotal gastos: {fmt_money(total)}"
        return msg

    # Saludo
    if _fm(agent, t, ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'buenas', 'que tal', 'saludos', 'hey']):
        from datetime import datetime as _dt
        h = _dt.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        nm = f", {name}" if name else ""
        return (f"{s}{nm}. Soy tu asistente del TPV. Puedo ayudarte con: "
                f"finanzas, ventas, stock, productos, ofertas y reportes. "
                f"¿Qué necesitas consultar?")

    # Agradecimiento / despedida
    if _fm(agent, t, ['gracias', 'genial', 'perfecto', 'adios', 'hasta luego', 'chao']):
        return "¡Con gusto! Estoy aquí para lo que necesites. 👍"

    # Productos más vendidos (antes que "ventas" para que 'vendidos' no caiga ahí)
    if _fm(agent, t, ['mas vendido', 'más vendido', 'top productos', 'mejores productos', 'ranking', 'mas vendidos', 'top vendidos', 'productos mas']):
        top = F.top(7, 5)
        if not top:
            return "Aún no hay ventas suficientes esta semana para un ranking."
        msg = "Top productos (últimos 7 días):\n"
        for i, x in enumerate(top):
            msg += f"{i+1}. {x['nombre']} — {x['q']:.0f} uds ({fmt_money(x['t'])})\n"
        return msg

    # Listado de catálogo / categorías
    if _fm(agent, t, ['que productos', 'qué productos', 'catalogo', 'catálogo', 'lista de productos', 'que tienes', 'categoria', 'categoría', 'categorias', 'categorías', 'productos tienes']):
        cats = F.categorias()
        total = sum(c['n'] for c in cats) if cats else 0
        if not cats:
            return "Aún no hay productos en el catálogo. Importa un Excel para empezar."
        msg = f"Catálogo: {total} productos en {len(cats)} categorías:\n"
        for c in cats[:8]:
            msg += f"• {c['cat']}: {c['n']} productos\n"
        msg += "\nPregúntame por un producto concreto (ej: 'precio del café')."
        return msg

    # Ventas del día
    if _fm(agent, t, ['cuanto vendi', 'cuánto vendí', 'ventas de hoy', 'ventas hoy', 'caja', 'recaude', 'facturacion', 'cobrado', 'ingreso del dia', 'como voy', 'cuanto llevo']):
        d = F.diario()
        if d['t'] == 0:
            return "Aún no hay ventas registradas hoy. ¡A vender! 💪"
        return (f"Ventas de hoy:\n"
                f"🛒 {d['t']} transacciones\n"
                f"💰 Total: {fmt_money(d['r'])}\n"
                f"📊 Ticket promedio: {fmt_money(d['a'])}")

    # Búsqueda de productos (limpia palabras de relleno como 'precio de', 'cuanto')
    import re as _re
    _term = _re.sub(r'\b(precio|costo|valor|cuanto|cuánto|cuesta|vale|de|del|la|el|los|las|hay|tienes|tiene|stock)\b',
                    ' ', t.lower()).strip()
    prods = P.search(_term or t, 10)
    if prods:
        if len(prods) == 1:
            p = prods[0]
            mg = ((p['p'] - p['c']) / p['p'] * 100) if p['p'] > 0 else 0
            rot = F.top(30, 20)
            vendido = 0
            if rot:
                for r in rot:
                    if r['nombre'].lower() == p['n'].lower():
                        vendido = r['q']
                        break
            msg = f"Análisis completo de {p['n']}:\n\n"
            msg += f"Precio venta: {fmt_money(p['p'])}\n"
            msg += f"Costo: {fmt_money(p['c'])}\n"
            msg += f"Margen: {pct(mg)}\n"
            msg += f"Ganancía/unidad: {fmt_money(p['p'] - p['c'])}\n"
            msg += f"Stock: {p['s']:.0f} {p['u']}\n"
            msg += f"Valor inventario: {fmt_money(p['p'] * p['s'])}\n"
            if vendido > 0:
                msg += f"Vendidos (30d): {vendido:.0f} unidades\n"
            return msg
        msg = "Resultados para su búsqueda:\n"
        for p in prods[:10]:
            msg += f"- {p['n']}: {fmt_money(p['p'])} | Stock: {p['s']:.0f}\n"
        return msg

    return ("Gestor completo a su disposición. Puede consultar:\n"
            "Finanzas | ABC | Punto equilibrio\n"
            "Stock | Predicciones | Ofertas\n"
            "Rotación | Gastos | EOQ")


# ================================================================
# DESARROLLADOR
# ================================================================
def handle_dev(agent, t, name):
    base = handle_admin(agent, t, name)
    tl = t.lower()
    if any(w in tl for w in ["metrica","rendimiento","servidor","cpu","ram","disco","memoria"]):
        try:
            import dev_metrics
            base += "\n\nMétricas del sistema (solo desarrollador):\n"
            base += "Usa el panel de métricas en /dev/metrics para detalles en tiempo real."
        except Exception:
            pass
    if any(w in tl for w in ["licencía","license","activacion"]):
        base += "\n\nLicencias: Usa /admin/licencías para gestiónar."
    if any(w in tl for w in ["usuario","users","cuentas"]):
        base += "\n\nUsuarios: Usa /admin/usuarios para gestiónar cuentas del sistema."
    return base
