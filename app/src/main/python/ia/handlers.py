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
    from ia.intent_engine import get_suggestions as _get_suggestions
    _HAS_INTENT = True
except Exception:
    _HAS_INTENT = False


def _fm(agent, text, keywords, threshold=0.7):
    try:
        if _HAS_NORM:
            matched, kw, score = contains_any(text, keywords, threshold)
            return matched
    except Exception:
        pass
    return any(w in text for w in keywords)


def _follow(role):
    frases = [
        "Necesitas algo más?",
        "En qué más te puedo ayudar?",
        "Te gustaria ver las ofertas del dia?",
        "Puedo buscar otro producto si deseas.",
        "Tienes alguna otra consulta?",
    ]
    if role == "cliente":
        frases.extend([
            "Quieres que te muestre productos relacionados?",
            "Te puedo ayudar a encontrar algo específico.",
        ])
    return "\n\n" + frases[hash(str(frases)) % len(frases)]


def _get_sug(intent_name, role):
    try:
        if _HAS_INTENT:
            return _get_suggestions(intent_name, role)
    except Exception:
        pass
    return []


def greet(role, name):
    h = datetime.now().hour
    g = ("Buenas noches" if h < 6 else
         "Buenos días" if h < 12 else
         "Buen mediodia" if h < 14 else
         "Buenas tardes" if h < 20 else
         "Buenas noches")
    n = f", {name}" if name else ""
    P.refresh()

    if role == 'cliente':
        msg = (f"{g}{n}. Bienvenido a TPV Smart. Puede consultar productos, "
               f"precios y ofertas. Si desea registrarse, solicite al administrador "
               f"sus credencíales de acceso.")
        if P.cache:
            msg += f" Hoy tenemos {len(P.cache)} productos disponibles."
        msg += " Escriba el nombre del producto que busca o consulte categorías."
        return msg

    if role == 'vendedor':
        d = F.diario()
        if d['t'] > 0:
            h2 = datetime.now().hour
            proy = d['r'] / h2 * 24 if h2 > 0 else d['r']
            return (f"{g}{n}. Al momento lleva {d['t']} ventas por "
                    f"{fmt_money(d['r'])}. Proyectamos cerrar el dia en "
                    f"~{fmt_money(proy)}. En que le ayudo?")
        return (f"{g}{n}. Aún no hay ventas hoy. Revise el catálogo para "
                f"ofrecer a sus clientes. Necesita algo?")

    if role == 'supervisor':
        d = F.diario()
        low = sum(1 for p in P.cache if 0 < p['s'] <= 5)
        return (f"{g}{n}. Panel de supervisión activo. {len(P.cache)} productos, "
                f"{low} con stock bajo. Ventas hoy: {fmt_money(d['r'])}. "
                f"Que desea revisar?")

    d = F.diario()
    low = sum(1 for p in P.cache if 0 < p['s'] <= 5)
    out = sum(1 for p in P.cache if p['s'] <= 0)
    return (f"{g}{n}. Sistema completo bajo su control. {len(P.cache)} productos "
            f"activos, {low} requieren atención, {out} agotados. "
            f"Ventas: {fmt_money(d['r'])}. Estoy a sus órdenes.")


def help_text(role):
    if role == 'cliente':
        return ("Con gusto le ayudo. Puedo:\n"
                "- Buscar productos y precios\n"
                "- Mostrar las mejores ofertas\n"
                "- Recomendar productos complementarios\n"
                "- Ver todas las categorías\n\n"
                "Dígame: 'busco cafe' o 'mejores ofertas'")
    if role == 'vendedor':
        return ("Estoy para asistirle. Puedo:\n"
                "- Ver ventas del dia y proyección\n"
                "- Consultar stock bajo\n"
                "- Top productos más vendidos\n"
                "- Buscar precios y margenes\n\n"
                "Dígame: 'ventas' o 'stock bajo' o 'cafe'")
    if role == 'supervisor':
        return ("Panel de supervisión disponible:\n"
                "- Dashboard y KPIs\n"
                "- Tendencías de venta\n"
                "- Proyecciónes\n"
                "- Estado de inventario\n\n"
                "Dígame: 'dashboard' o 'tendencías'")
    return ("Gestor completo a su servicio:\n\n"
            "Finanzas: ingresos, gastos, ganancías, margenes\n"
            "Analisis: ABC, rotación, punto equilibrio\n"
            "Predicciones: regresion, proyecciónes\n"
            "Inventario: stock bajo, críticos\n"
            "Ofertas inteligentes\n\n"
            "Ejemplos: 'finanzas', 'ABC', 'predicciónes', 'ofertas'")


# ================================================================
# CLIENTE
# ================================================================
def handle_cliente(agent, t, m):
    if _fm(agent, t, ["ayuda","qué puedes","qué haces","cómo funcióna","menu","opciones"]):
        return ("Puedo ayudarte con muchas cosas:\n\n"
                "- Buscar productos y precios\n"
                "- Ver ofertas y descuentos\n"
                "- Consultar stock disponible\n"
                "- Ver categorías del catálogo\n"
                "- Informacion de puntos y lealtad\n"
                "- Historial de compras\n\n"
                "Escribe lo que necesites.")

    if _fm(agent, t, ["login","inicíar sesion","acceder","entrar","contraseña","password","usuario","credencíales","cuenta"]):
        return ("Para acceder al sistema necesitas usuario y contraseña.\n"
                "Solicita tus credencíales al administrador del negocio.\n"
                "Mientras tanto, puedo ayudarte a buscar productos y precios.")

    if _fm(agent, t, ["registrarme","nueva cuenta","crear cuenta","soy nuevo"]):
        return ("Las cuentas se crean desde el panel de administración.\n"
                "Comunica al administrador qué necesitas acceso.")

    if _fm(agent, t, ["no funcióna","no puedo entrar","error","acceso denegado","bloqueado"]):
        return ("Si no puedes inicíar sesion:\n"
                "1. Verifica usuario y contraseña\n"
                "2. Espera 10 min si fallaste 5 veces\n"
                "3. Pide al admin que resetee tu contraseña")

    if _fm(agent, t, ["puntos","lealtad","fidelidad","recompensa","beneficio"]):
        return ("Sistema de puntos activo. Cada compra acumula puntos qué puedes "
                "canjear por descuentos y productos. Consulta tus puntos en la "
                "sección de Lealtad.")

    if _fm(agent, t, ["mis compras","historial","compre","recibo","factura"]):
        return ("Puedes ver tu historial de compras en la sección de Registros. "
                "Alli encontraras todos los recibos con fecha, productos, "
                "cantidades y totales.")

    if _fm(agent, t, ["pago","pagar","efectivo","tarjeta","transferencía","metodo"]):
        return ("Aceptamos múltiples métodos de pago: efectivo, tarjeta de "
                "crédito/débito, transferencía bancaria y código QR.")

    if _fm(agent, t, ["horario","abierto","cerrado","donde","ubicación","direccion"]):
        return "Consulte los detalles de horario y ubicación en la sección de Tienda."

    if _fm(agent, t, ["oferta","descuento","rebaja","mejor precio","barato","promo","promoción"]):
        of = O.mejores()
        if not of:
            return "Hoy todos nuestros precios son muy competitivos. Escribe el nombre de un producto."
        msg = "Ofertas disponibles:\n\n"
        for i, o in enumerate(of, 1):
            ahorro = o["p"] - o["d"]
            msg += (str(i) + ". " + o["n"] + ": " + fmt_money(o["d"]) +
                    " (Normal: " + fmt_money(o["p"]) +
                    " - Ahorras " + fmt_money(ahorro) + ")\n")
        return msg + "\nEscribe el nombre de cualquier producto para ver mas detalles."

    if _fm(agent, t, ["categorías","catálogo","qué tienen","secciónes","qué venden","departamento"]):
        cats = ", ".join(P.cats[:15]) if P.cats else "General"
        return ("Contamos con " + str(len(P.cats)) + " categorías: " + cats +
                ".\n\nEscribe el nombre de una categoria o producto.")

    if _fm(agent, t, ["stock","disponible","cuánto hay","hay de","quedan","existencía"]):
        prods = P.search(t, 8)
        if prods:
            msg = "Disponibilidad:\n\n"
            for p in prods[:10]:
                estado = str(p["s"]) + " " + p["u"] if p["s"] > 0 else "AGOTADO"
                msg += "- " + p["n"] + ": " + estado + " - " + fmt_money(p["p"]) + "\n"
            return msg + "\n\n" + _follow("cliente")

    prods = P.search(t, 8)
    if prods:
        m["p"] = prods[0]["n"]
        if len(prods) == 1:
            p = prods[0]
            msg = p["n"] + ": " + fmt_money(p["p"]) + " por " + p["u"] + ".\n"
            if p["s"] == 0:
                msg += "Momentáneamente agotado. "
                rel = O.relacionados(p["n"], 2)
                if rel:
                    msg += "Te sugiero: " + rel[0]["nombre"] + "."
            elif p["s"] <= 3:
                msg += "Últimas " + str(int(p["s"])) + " unidades disponibles."
            else:
                msg += "Stock: " + str(int(p["s"])) + " " + p["u"] + ".\n"
            rel = O.relacionados(p["n"], 2)
            if rel:
                msg += "Te puede interesar: " + rel[0]["nombre"] + "."
            return msg
        msg = "Encontré " + str(len(prods)) + " resultados:\n\n"
        for p in prods[:10]:
            si = " | " + str(int(p["s"])) + " " + p["u"] if p["s"] > 0 else " | AGOTADO"
            msg += "- " + p["n"] + ": " + fmt_money(p["p"]) + si + "\n"
        return msg + "\n\n" + _follow("cliente")

    if _fm(agent, t, ["hola","buenas","buenos días","buenas tardes","buenas noches","hey"]):
        return ("Hola! Soy tu asistente y estoy aquí para ayudarte. "
                "Puedes preguntarme sobre productos, precios, ofertas, "
                "stock o cualquier cosa que necesites.")

    return ("Con gusto te ayudo. Puedes preguntarme sobre productos, precios, "
            "ofertas, stock, categorías o escribir ayuda para ver todo lo que "
            "puedo hacer.")


# ================================================================
# VENDEDOR
# ================================================================
def handle_vendedor(agent, t, m):
    if _fm(agent, t, ["ventas","caja","recaudó","cuánto vendí","cómo voy"]):
        d = F.diario()
        if d['t'] == 0:
            return "Todavía no hay ventas hoy."
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

    prods = P.search(t, 10)
    if prods:
        m["p"] = prods[0]["n"]
        msg = "Productos:\n"
        for p in prods[:10]:
            mrg = ((p['p'] - p['c']) / p['p'] * 100) if p['p'] > 0 and p['c'] > 0 else 0
            msg += ("- " + p["n"] + ": " + fmt_money(p["p"]) +
                    " | Stock: " + str(int(p["s"]))
                    + (" | Margen: " + pct(mrg) if mrg > 0 else "") + "\n")
        return msg

    return ("Dime qué necesitas: ventas, stock bajo, top, o nombre de un "
            "producto.\n\n" + _follow("vendedor"))


# ================================================================
# SUPERVISOR
# ================================================================
def handle_supervisor(agent, t, m=None):
    d = F.diario()
    w = F.semanal()
    low = sum(1 for p in P.cache if 0 < p['s'] <= 5)

    if _fm(agent, t, ["ayuda","qué puedes","menu","opciones"]):
        return ("Como supervisor tienes acceso completo:\n\n"
                "- dashboard: KPIs\n"
                "- ventas: Resumen del dia\n"
                "- stock bajo: Alertas\n"
                "- top: Más vendidos\n"
                "- finanzas: Balance y margen\n"
                "- gastos: Egresos\n"
                "- predicciónes: Tendencías\n"
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
        rows = q("SELECT descripcion,monto,categoria FROM gastos "
                 "WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
        if not rows:
            return "No hay gastos hoy."
        msg = "Gastos del dia (" + str(len(rows)) + "):\n\n"
        total = 0
        for r in rows[:20]:
            msg += ("- " + str(r["descripcion"]) + ": " + fmt_money(r["monto"]) +
                    " (" + str(r["categoria"]) + ")\n")
            total += r["monto"]
        return msg + "\nTotal: " + fmt_money(total)

    if _fm(agent, t, ["tendencía","predicción","proyección","forecast","pronóstico"]):
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

    prods = P.search(t, 10)
    if prods:
        m["p"] = prods[0]["n"]
        msg = "Productos:\n\n"
        for p in prods[:10]:
            mrg = ((p['p'] - p['c']) / p['p'] * 100) if p['p'] > 0 and p['c'] > 0 else 0
            msg += ("- " + p["n"] + ": " + fmt_money(p["p"]) +
                    " | Stock: " + str(int(p["s"]))
                    + (" | Margen: " + pct(mrg) if mrg > 0 else "") + "\n")
        return msg

    return ("Escriba: ventas, stock bajo, top, finanzas, gastos, predicciónes, "
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
            msg += "Atencion: los gastos superan los ingresos. Revise las finanzas."
        return msg

    if _fm(agent, t, ['abc','pareto','clasificación']):
        abc = F.abc()
        if not abc['A']:
            return "Necesito al menos 30 días de ventas para el análisis ABC."
        msg = "Analisis ABC de productos (ultimos 30 días):\n\n"
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

    if _fm(agent, t, ['predicción','pronóstico','proyección','forecast','tendencía']):
        rows = q("SELECT DATE(fecha) d,SUM(total) r FROM historial_ventas "
                 "WHERE fecha>=DATE('now','-7 days') GROUP BY DATE(fecha) ORDER BY d")
        if rows and len(rows) >= 3:
            x = list(range(len(rows)))
            y = [r['r'] for r in rows]
            mg, b = M.regresion(x, y)
            prox = max(0, mg * len(rows) + b)
            tend = "creciente" if mg > 0 else "decreciente"
            msg = "Analisis de tendencía:\n\n"
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
        rows = q("SELECT descripcion,monto,categoria FROM gastos "
                 "WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
        if not rows:
            return "No hay gastos registrados hoy."
        msg = f"Gastos del dia ({len(rows)}):\n\n"
        total = 0
        for r in rows:
            msg += f"- {r['descripcion']}: {fmt_money(r['monto'])} ({r['categoria']})\n"
            total += r['monto']
        msg += f"\nTotal gastos: {fmt_money(total)}"
        return msg

    prods = P.search(t, 10)
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
        base += "\n\nLicencías: Usa /admin/licencías para gestionar."
    if any(w in tl for w in ["usuario","users","cuentas"]):
        base += "\n\nUsuarios: Usa /admin/usuarios para gestionar cuentas del sistema."
    return base
