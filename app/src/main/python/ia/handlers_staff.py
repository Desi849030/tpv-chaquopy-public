# -*- coding: utf-8 -*-
"""handlers_staff.py v11 — Role-specific IA handlers 100% OFFLINE
Todas las consultas usan ia.db_utils.q() — sin depender de db_connection.
"""
import re
from datetime import datetime, date, timedelta
from ia.db_utils import q, fmt_money, pct
from ia.catalog import P, O
from ia.metrics import F, M
from ia.handlers_base import _fm, _follow, _get_sug
from version import __version__

def _q(sql, params=()):
    """Wrapper seguro: retorna lista de dicts o [].
    Usa ia.db_utils.q() que ya maneja errores."""
    rows = q(sql, params)
    if rows is None:
        return []
    return [dict(r) for r in rows] if rows else []

def _q1(sql, params=()):
    """Wrapper para una sola fila: retorna dict o {}."""
    r = q(sql, params, one=True)
    return dict(r) if r else {}


# ================================================================
# VENDEDOR
# ================================================================
def handle_vendedor(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    tl = (t or '').lower().strip()

    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        h = datetime.now().hour
        s = 'Buenos dias' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        return f"{s} {name}. Soy tu asistente de caja. Puedo ayudarte con:\n- Ventas de hoy\n- Buscar precios rapidos\n- Stock critico\n- Metas diarias\n- Historial de ventas"

    # --- Ventas del dia ---
    if _fm(agent, t, ["ventas", "caja", "cuanto vendi", "recaudo", "como voy", "cuanto he vendido"]):
        d = F.diario()
        if d['t'] == 0:
            return "Todavia no has registrado ventas hoy. Vamos por la primera!"
        sem = F.semanal()
        return (f"Ventas de HOY:\n"
                f"  Transacciones: {d['t']}\n"
                f"  Total: {fmt_money(d['r'])}\n"
                f"  Ticket Promedio: {fmt_money(d['a'])}\n\n"
                f"Esta SEMANA:\n"
                f"  Transacciones: {sem['t']}\n"
                f"  Total: {fmt_money(sem['r'])}")

    # --- Stock critico ---
    if _fm(agent, t, ["stock", "agotado", "bajo", "sin stock", "se acaba"]):
        rows = _q("SELECT nombre, stock_actual, stock_minimo FROM inventario_general "
                  "WHERE stock_actual <= COALESCE(NULLIF(stock_minimo,0),5) "
                  "ORDER BY stock_actual ASC LIMIT 10")
        if not rows:
            return "Excelente, ningun producto tiene stock critico."
        msg = "Atencion, productos con stock bajo:\n"
        for r in rows:
            icon = "X" if r['stock_actual'] <= 0 else "!"
            msg += f"  [{icon}] {r['nombre']}: {int(r['stock_actual'])} uds\n"
        msg += "\nUsa 'productos' para ver el inventario completo."
        return msg

    # --- Busqueda rapida de productos ---
    _term = re.sub(r'\b(precio|cuesta|vale|de|del|hay|tienes|stock|cuanto|es|el|la|un|una)\b', ' ', tl).strip()
    prods = P.search(_term or t, 5)
    if prods and len(_term) > 2:
        msg = "Resultados de busqueda:\n"
        for p in prods:
            stock_icon = "OK" if p.get('s', 0) > 0 else "AGOTADO"
            msg += f"  - {p['n']}: {fmt_money(p['p'])} [{stock_icon}]\n"
        return msg

    # --- Precio rapido (NLP) ---
    if _fm(agent, t, ["cuanto cuesta", "precio de", "cuanto vale", "que precio",
                      "costa el", "cuanto es", "valor del", "dame el precio"]):
        rows = _q("SELECT nombre, precio, stock_actual FROM productos p "
                  "LEFT JOIN inventario_general i ON i.producto_id=p.producto_id "
                  "WHERE p.activo=1")
        _clean = re.sub(r'\b(cuanto|cuesta|vale|costa|precio|de|del|el|la|es|un|una|que|dame)\b', ' ', tl).strip()
        for p in rows:
            if p['nombre'].lower() in _clean or _clean in p['nombre'].lower():
                st = "Disponible" if (p.get('stock_actual') or 0) > 0 else "Agotado"
                return f"{p['nombre']}: {fmt_money(p['precio'])} [{st}]"
        words = [w for w in _clean.split() if len(w) > 2]
        for w in words:
            for p in rows:
                if w in p['nombre'].lower():
                    return f"{p['nombre']}: {fmt_money(p['precio'])}"
        return "No encontre ese producto. Prueba con: 'precio de cafe latte'"

    # --- Metas diarias ---
    if _fm(agent, t, ["meta", "objetivo", "cuanto falta", "progreso", "faltan para", "cuanto para"]):
        d = F.diario()
        meta = 500.0
        actual = float(d['r'])
        p = min(actual / meta * 100, 100) if meta > 0 else 0
        bar_len = 15
        filled = int(bar_len * p / 100)
        bar = "#" * filled + "." * (bar_len - filled)
        status = "META CUMPLIDA!" if p >= 100 else f"Te faltan {fmt_money(meta - actual)}"
        return (f"Meta Diaria:\n"
                f"  Objetivo: {fmt_money(meta)}\n"
                f"  Actual:   {fmt_money(actual)} ({d['t']} ventas)\n"
                f"  [{bar}] {p:.0f}%\n"
                f"  {status}")

    # --- Historial reciente ---
    if _fm(agent, t, ["ultimas ventas", "historial", "ventas recientes", "que vendi", "recientes"]):
        rows = _q("SELECT producto_nombre as nombre, cantidad, total, fecha "
                  "FROM historial_ventas ORDER BY fecha DESC LIMIT 10")
        if not rows:
            return "No hay ventas registradas aun."
        msg = "Ultimas 10 ventas:\n"
        for i, r in enumerate(rows, 1):
            msg += f"  {i}. {r['nombre']} x{int(r['cantidad'])} = {fmt_money(r['total'])}\n"
        return msg

    # --- Top productos vendidos ---
    if _fm(agent, t, ["top", "mas vendido", "mejor vendido", "ranking", "popular"]):
        rows = _q("SELECT nombre, SUM(cantidad) as q, SUM(total) as t "
                  "FROM historial_ventas WHERE fecha>=DATE('now','-7 days') "
                  "GROUP BY nombre ORDER BY q DESC LIMIT 5")
        if not rows:
            return "Sin datos de ventas esta semana."
        msg = "Top 5 productos (7 dias):\n"
        for i, r in enumerate(rows, 1):
            msg += f"  {i}. {r['nombre']}: {int(r['q'])} uds / {fmt_money(r['t'])}\n"
        return msg

    # --- Registrar venta por chat ---
    if _fm(agent, t, ["registrar venta", "nueva venta", "vendi", "hice una venta"]):
        rows = _q("SELECT producto_id, nombre, precio FROM productos WHERE activo=1")
        encontrados = []
        for prod in rows:
            if prod['nombre'].lower() in tl:
                encontrados.append(prod)
        if not encontrados:
            return "No encontre productos en tu mensaje. Ej: 'vendi 3 cafe americano'."
        msg = "Venta registrada (simulada):\n\n"
        total = 0
        for p in encontrados[:5]:
            qty_match = re.search(r'(\d+)\s*' + re.escape(p['nombre'].lower().split()[0]), tl)
            qty = int(qty_match.group(1)) if qty_match else 1
            subtotal = p['precio'] * qty
            total += subtotal
            msg += f"  {p['nombre']} x{qty} = {fmt_money(subtotal)}\n"
        msg += f"\n  TOTAL: {fmt_money(total)}"
        return msg

    # --- Productos por categoria ---
    if _fm(agent, t, ["categorias", "categoria", "que productos hay", "que tienen"]):
        rows = _q("SELECT categoria, COUNT(*) as n FROM productos WHERE activo=1 GROUP BY categoria ORDER BY n DESC")
        if not rows:
            return "No hay categorias registradas."
        msg = "Productos por categoria:\n"
        for r in rows:
            cat = r['categoria'] or '(sin categoria)'
            msg += f"  {cat}: {r['n']} productos\n"
        msg += "\nPreguntame por una categoria especifica para ver los productos."
        return msg

    # --- Ofertas / recomendaciones ---
    if _fm(agent, t, ["ofertas", "descuentos", "promocion", "recomienda", "sugerencia"]):
        ofertas = O.mejores()
        if not ofertas:
            return "No hay productos con margen suficiente para ofertas activas."
        msg = "Productos con mejor margen (posibles ofertas 15% off):\n"
        for o in ofertas[:5]:
            msg += f"  - {o['n']}: {fmt_money(o['p'])} -> {fmt_money(o['d'])} (margen {o['m']*100:.0f}%)\n"
        return msg

    return _follow('vendedor')


# ================================================================
# CAJERO (NUEVO — no existia en la version anterior)
# ================================================================
def handle_cajero(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    tl = (t or '').lower().strip()

    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        h = datetime.now().hour
        s = 'Buenos dias' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        return f"{s} {name}. Lista la caja. Puedo ayudarte con:\n- Registrar ventas rapidas\n- Consultar precios\n- Ver historial del dia\n- Arqueo de caja"

    # --- Resumen de caja del dia ---
    if _fm(agent, t, ["arqueo", "cierre", "cuanto hay en caja", "resumen de caja", "cerrar caja"]):
        d = F.diario()
        gastos = _q("SELECT COALESCE(SUM(monto),0) as total FROM gastos "
                    "WHERE DATE(fecha)=DATE('now','localtime')")
        g = gastos[0]['total'] if gastos else 0
        neto = d['r'] - g
        metodos = _q("SELECT metodo_pago, COUNT(*) as ops, SUM(total) as total "
                     "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') "
                     "GROUP BY metodo_pago")
        msg = (f"ARQUEO DE CAJA — {date.today().isoformat()}\n"
               f"================================\n"
               f"  Ventas:          {d['t']} transacciones\n"
               f"  Ingreso bruto:   {fmt_money(d['r'])}\n"
               f"  Gastos:          {fmt_money(g)}\n"
               f"  Ingreso neto:    {fmt_money(neto)}\n"
               f"  Ticket promedio: {fmt_money(d['a'])}\n")
        if metodos:
            msg += "\n  Por metodo de pago:\n"
            for m in metodos:
                msg += f"    {m['metodo_pago'] or 'Efectivo'}: {m['ops']} ops / {fmt_money(m['total'])}\n"
        return msg

    # --- Ventas del dia ---
    if _fm(agent, t, ["ventas", "cuanto vendi", "como va el dia", "cuanto he cobrado"]):
        d = F.diario()
        if d['t'] == 0:
            return "No se han registrado ventas hoy."
        return (f"Resumen de hoy:\n"
                f"  {d['t']} ventas / {fmt_money(d['r'])}")

    # --- Precio rapido ---
    if _fm(agent, t, ["precio", "cuesta", "vale", "cuanto es"]):
        prods = P.search(t, 3)
        if prods:
            msg = ""
            for p in prods:
                msg += f"  {p['n']}: {fmt_money(p['p'])}\n"
            return msg
        return "No encontre ese producto."

    # --- Buscar producto ---
    prods = P.search(t, 5)
    if prods and len(t.split()) > 1:
        msg = "Productos encontrados:\n"
        for p in prods:
            msg += f"  {p['n']}: {fmt_money(p['p'])} (stock: {int(p.get('s', 0))})\n"
        return msg

    return "En que puedo ayudarte? Puedo: arqueo de caja, buscar precios, ver ventas del dia."


# ================================================================
# ADMINISTRADOR
# ================================================================
def handle_admin(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    tl = (t or '').lower()
    d = F.diario()

    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        return f"Hola Admin {name}. Panel de administracion activo.\n\nPuedo generar:\n- Balance y ganancias\n- Rendimiento de vendedores\n- Gastos del dia\n- Punto de equilibrio\n- EOQ (lote optimo)\n- Diagnostico completo del negocio"

    # --- Balance / ganancias ---
    if _fm(agent, t, ["ganancias", "balance", "rentabilidad", "finanzas", "como va el negocio"]):
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        sem = F.semanal()
        return (f"Balance de HOY:\n"
                f"  Ingresos:       {fmt_money(d['r'])}\n"
                f"  Gastos:         {fmt_money(d['g'])}\n"
                f"  Ganancia neta:  {fmt_money(prof)} ({pct(margen)})\n\n"
                f"Esta SEMANA:\n"
                f"  Ingresos:  {fmt_money(sem['r'])} ({sem['t']} ops)")

    # --- Rendimiento de vendedores ---
    if _fm(agent, t, ["vendedores", "personal", "rendimiento", "quien vendio", "equipo"]):
        rows = _q("SELECT vendedor_nombre, COUNT(*) as ops, SUM(total) as total "
                  "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') "
                  "GROUP BY vendedor_nombre ORDER BY total DESC")
        if not rows:
            return "No hay ventas registradas por el personal hoy."
        msg = "Rendimiento de Vendedores (Hoy):\n"
        for i, r in enumerate(rows, 1):
            msg += f"  {i}. {r['vendedor_nombre']}: {fmt_money(r['total'])} ({r['ops']} ventas)\n"
        return msg

    # --- Gastos ---
    if _fm(agent, t, ["gastos", "egresos", "salidas", "desembolsos"]):
        rows = _q("SELECT descripcion, monto, categoria FROM gastos "
                  "WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
        if not rows:
            return "Cero gastos registrados hoy. Excelente control."
        total_g = sum(r['monto'] for r in rows)
        msg = f"Gastos de hoy (Total: {fmt_money(total_g)}):\n"
        for r in rows:
            cat = r.get('categoria', '') or ''
            msg += f"  - {r['descripcion']}: {fmt_money(r['monto'])} {cat}\n"
        return msg

    # --- Punto de equilibrio ---
    if _fm(agent, t, ["punto equilibrio", "break even", "umbral", "equilibrio"]):
        gastos_fijos = d['g']
        ticket = d['a'] if d['a'] > 0 else 50
        cv = ticket * 0.6
        pe = M.punto_eq(gastos_fijos, ticket, cv)
        return (f"Punto de Equilibrio:\n"
                f"  Gastos fijos diarios: {fmt_money(gastos_fijos)}\n"
                f"  Ticket promedio: {fmt_money(ticket)}\n"
                f"  Costo variable est: {fmt_money(cv)}\n"
                f"  Ventas necesarias: {pe} transacciones\n"
                f"  Ingreso minimo: {fmt_money(pe * ticket)}")

    # --- EOQ (Lote optimo) ---
    if _fm(agent, t, ["eoq", "lote optimo", "pedido optimo"]):
        rows = _q("SELECT nombre, stock_actual, precio_venta "
                  "FROM inventario_general WHERE stock_actual > 0 "
                  "ORDER BY stock_actual ASC LIMIT 5")
        if not rows:
            return "Sin productos en inventario para calcular EOQ."
        msg = "Lote Optimo de Pedido (EOQ):\n"
        msg += "  (D=300 uds/mes, Costo pedido=$50, Almacen=20% precio)\n\n"
        for r in rows:
            dem = 300; costo_p = 50; h = r['precio_venta'] * 0.2
            if h > 0:
                eoq = M.eoq(dem, costo_p, h)
                msg += f"  {r['nombre']}: EOQ = {eoq:.0f} uds (stock: {int(r['stock_actual'])})\n"
        return msg

    # --- Diagnostico completo ---
    if any(k in tl for k in ['diagnostico', 'resumen ejecutivo', 'como va',
                              'estado del negocio', 'reporte general', 'dashboard']):
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        stock = dict(F.stock_resumen())
        conteos = F.conteos()
        return (f"REPORTE EJECUTIVO\n"
                f"==================\n"
                f"Balance Hoy:\n"
                f"  Ingresos:  {fmt_money(d['r'])}\n"
                f"  Gastos:    {fmt_money(d['g'])}\n"
                f"  Ganancia:  {fmt_money(prof)} (margen {pct(margen)})\n\n"
                f"Inventario:\n"
                f"  Total: {stock.get('total', 0)} | Agotados: {stock.get('agotados', 0)} | Criticos: {stock.get('criticos', 0)}\n\n"
                f"Negocio:\n"
                f"  Productos: {conteos['productos']} | Ventas hoy: {conteos['ventas_hoy']} | Clientes: {conteos['clientes']}\n\n"
                f"Puedo mostrar: punto de equilibrio, EOQ, top vendedores, ABC.")

    # --- Hora pico ---
    if any(k in tl for k in ["hora pico", "mejor hora", "cuando venden mas", "horario"]):
        rows = _q("SELECT strftime('%H', fecha) as hora, COUNT(*) as ops, SUM(total) as total "
                  "FROM historial_ventas WHERE fecha >= DATE('now','-7 days') "
                  "GROUP BY hora ORDER BY total DESC LIMIT 5")
        if not rows:
            return "Sin datos de ventas esta semana."
        msg = "Horas Pico (ultimos 7 dias):\n"
        for r in rows:
            h = int(r['hora'])
            p = "manana" if h < 12 else ("tarde" if h < 19 else "noche")
            msg += f"  {r['hora']}:00 ({p}) — {r['ops']} ventas / {fmt_money(r['total'])}\n"
        return msg

    # --- Ticket promedio ---
    if any(k in tl for k in ["ticket promedio", "ticket medio", "promedio por venta"]):
        r = _q1("SELECT COUNT(*) as c, COALESCE(SUM(total),0) as s, "
                "COALESCE(AVG(total),0) as a FROM historial_ventas "
                "WHERE fecha >= DATE('now','-7 days')")
        if not r or r.get('c', 0) == 0:
            return "Sin ventas esta semana para calcular ticket promedio."
        return (f"Ticket Promedio (7 dias):\n"
                f"  Ventas: {r['c']}\n"
                f"  Ingreso total: {fmt_money(r['s'])}\n"
                f"  Ticket promedio: {fmt_money(r['a'])}")

    # --- Categorias ---
    if any(k in tl for k in ["categorias", "por categoria", "clasificacion"]):
        rows = _q("SELECT p.categoria, COUNT(*) as prods, AVG(p.precio) as precio_medio, "
                  "SUM(i.stock_actual) as stock_total "
                  "FROM productos p LEFT JOIN inventario_general i ON i.producto_id=p.producto_id "
                  "WHERE p.activo=1 GROUP BY p.categoria ORDER BY prods DESC")
        if not rows:
            return "No hay categorias registradas."
        msg = "Categorias:\n"
        for r in rows:
            cat = r['categoria'] or '(sin categoria)'
            msg += f"  {cat}: {r['prods']} productos, precio medio {fmt_money(r['precio_medio'])}\n"
        return msg

    # --- Clientes ---
    if any(k in tl for k in ["clientes", "cuantos clientes", "lista clientes"]):
        total = 0
        r = _q1("SELECT COUNT(*) as n FROM clientes_tienda")
        if r:
            total = r.get('n', 0)
        if total == 0:
            r2 = _q1("SELECT COUNT(*) as n FROM clientes")
            if r2:
                total = r2.get('n', 0)
        if total == 0:
            return "No hay clientes registrados en la base local."
        return f"Total clientes registrados: {total}"

    # --- ABC Pareto ---
    if _fm(agent, t, ["abc", "pareto", "80/20"]):
        abc = F.abc()
        if not abc.get("A"):
            return "Faltan datos historicos para analisis ABC."
        return (f"Analisis ABC (Regla 80/20):\n"
                f"  Clase A (Top ventas): {len(abc['A'])} productos\n"
                f"  Clase B (Rotacion media): {len(abc['B'])} productos\n"
                f"  Clase C (Poca salida): {len(abc['C'])} productos\n"
                + (f"\n  Top A: {abc['A'][0]}" if abc['A'] else ""))

    return _follow('administrador')


# ================================================================
# SUPERVISOR
# ================================================================
def handle_supervisor(agent, t, m=None):
    tl = (t or '').lower().strip()

    # --- Dashboard ---
    if any(k in tl for k in ['diagnostico', 'resumen', 'estado negocio',
                              'como va', 'reporte ejecutivo', 'dashboard']):
        vh = _q1("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r "
                 "FROM historial_ventas WHERE fecha LIKE DATE('now')||'%'")
        semana = (date.today() - timedelta(days=7)).isoformat()
        vs = _q1("SELECT COUNT(*) as t, COALESCE(SUM(total),0) as r "
                 "FROM historial_ventas WHERE fecha >= ?", (semana,))
        gh = _q1("SELECT COALESCE(SUM(monto),0) as g FROM gastos "
                 "WHERE DATE(fecha)=DATE('now','localtime')")
        sb = _q1("SELECT COUNT(*) as c FROM inventario_general "
                 "WHERE stock_actual <= COALESCE(NULLIF(stock_minimo,0),5)")
        v_t = vh.get('t', 0); v_r = vh.get('r', 0)
        s_t = vs.get('t', 0); s_r = vs.get('r', 0)
        g_h = gh.get('g', 0)
        stock_bajo = sb.get('c', 0) if sb else 0
        return (f"Dashboard Supervisor:\n\n"
                f"  Ventas Hoy:   {v_t} ops / {fmt_money(v_r)}\n"
                f"  Ventas Semana: {s_t} ops / {fmt_money(s_r)}\n"
                f"  Gastos Hoy:   {fmt_money(g_h)}\n"
                f"  Ganancia Hoy: {fmt_money(v_r - g_h)}\n"
                f"  Stock bajo:   {stock_bajo} productos\n\n"
                f"Pregunta por: 'analisis ABC', 'prediccion', 'rotacion', 'dias de stock'.")

    # --- Prediccion de ventas ---
    if any(k in tl for k in ['prediccion', 'pronostico', 'proyeccion', 'forecast', 'tendencia']):
        rows = _q("SELECT DATE(fecha) as dia, SUM(total) as total "
                  "FROM historial_ventas WHERE fecha >= DATE('now','-7 days') "
                  "GROUP BY dia ORDER BY dia")
        if not rows or len(rows) < 2:
            return "Necesito al menos 2 dias de datos para predecir."
        totales = [r['total'] for r in rows]
        n = len(totales)
        x = list(range(n))
        sx, sy = sum(x), sum(totales)
        sxy = sum(x[i] * totales[i] for i in range(n))
        sx2 = sum(v * v for v in x)
        denom = n * sx2 - sx * sx
        pend = (n * sxy - sx * sy) / denom if denom != 0 else 0
        inter = (sy - pend * sx) / n
        pred = inter + pend * n
        tendencia = "creciente" if pend > 0 else "decreciente" if pend < 0 else "estable"
        return (f"Prediccion de Ventas:\n"
                f"  Tendencia: {tendencia} ({pend:+.2f}/dia)\n"
                f"  Prediccion manana: {fmt_money(pred)}\n"
                f"  Promedio 7 dias: {fmt_money(sum(totales)/n)}\n"
                f"  Min/Max: {fmt_money(min(totales))} / {fmt_money(max(totales))}")

    # --- Rotacion ---
    if _fm(agent, t, ["rotacion", "indice de rotacion"]):
        rows = _q("SELECT nombre, stock_actual, precio_venta, "
                  "(SELECT COALESCE(SUM(cantidad),0) FROM historial_ventas hv "
                  "WHERE hv.nombre=ig.nombre AND hv.fecha>=DATE('now','-30 days')) as vendidos "
                  "FROM inventario_general ig WHERE stock_actual > 0 ORDER BY vendidos DESC LIMIT 5")
        if not rows:
            return "Sin datos suficientes para calcular rotacion."
        msg = "Indice de Rotacion (30 dias, Top 5):\n"
        for r in rows:
            v = r['vendidos']; s = r['stock_actual']
            rot = (v / s) if s > 0 else 0
            msg += f"  {r['nombre']}: rot={rot:.2f}x (vendidos {v}, stock {s})\n"
        return msg

    # --- ABC Pareto ---
    if _fm(agent, t, ["abc", "pareto"]):
        abc = F.abc()
        if not abc.get("A"):
            return "Faltan datos historicos para analisis ABC."
        return (f"Analisis ABC (Regla 80/20):\n"
                f"  Clase A (Top ventas): {len(abc['A'])} productos\n"
                f"  Clase B (Rotacion media): {len(abc['B'])} productos\n"
                f"  Clase C (Poca salida): {len(abc['C'])} productos\n"
                + (f"\n  Tip: Asegura que {abc['A'][0]} nunca se quede sin stock." if abc['A'] else ""))

    # --- Dias de stock ---
    if any(k in tl for k in ["dias de stock", "dias stock", "cuantos dias quedan",
                              "abastecimiento", "cuanto dura"]):
        rows = _q("SELECT ig.nombre, ig.stock_actual, "
                  "(SELECT COALESCE(SUM(cantidad),0) FROM historial_ventas hv "
                  "WHERE hv.producto_id=ig.producto_id AND hv.fecha>=DATE('now','-30 days')) as vendidos "
                  "FROM inventario_general ig WHERE ig.stock_actual > 0 "
                  "ORDER BY vendidos DESC LIMIT 10")
        if not rows:
            return "Sin datos de ventas recientes para calcular."
        msg = "Dias de Stock Restante (Top vendidos):\n"
        criticos = 0
        for r in rows:
            v = r['vendidos']; s = r['stock_actual']
            diario = v / 30 if v > 0 else 0
            dias = int(s / diario) if diario > 0 else 999
            icon = "[!]" if dias <= 3 else ("[~]" if dias <= 7 else "[OK]")
            if dias <= 7: criticos += 1
            ds = f"{dias} dias" if dias < 999 else "sin rotacion"
            msg += f"  {icon} {r['nombre']}: {ds} ({int(s)} uds, {diario:.1f}/dia)\n"
        if criticos > 0:
            msg += f"\n{criticos} productos con menos de 7 dias de stock."
        return msg

    # --- Ventas por categoria ---
    if any(k in tl for k in ["ventas por categoria", "que categoria vende mas", "ranking categorias"]):
        rows = _q("SELECT p.categoria, COUNT(*) as ops, SUM(hv.cantidad) as uds, SUM(hv.total) as total "
                  "FROM historial_ventas hv "
                  "JOIN productos p ON p.producto_id=hv.producto_id "
                  "WHERE hv.fecha >= DATE('now','-7 days') "
                  "GROUP BY p.categoria ORDER BY total DESC")
        if not rows:
            return "Sin ventas por categoria esta semana."
        total_s = sum(r['total'] for r in rows)
        msg = "Ventas por Categoria (7 dias):\n"
        for r in rows:
            pc = (r['total'] / total_s * 100) if total_s > 0 else 0
            msg += f"  {r['categoria'] or '(otro)'}: {fmt_money(r['total'])} ({r['ops']} ops, {int(r['uds'] or 0)} uds) {pc:.0f}%\n"
        return msg

    return _follow('supervisor')


# ================================================================
# DESARROLLADOR (100% offline, sin depender de telecom_diag)
# ================================================================
def handle_dev(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    tl = (t or '').lower().strip()

    # --- SQL Executor (primero, antes de todo) ---
    if any(k in tl for k in ['ejecutar', 'select ', 'query ', 'sql',
                              'consulta sql', 'run sql', 'ejecuta']):
        sql_query = tl
        for prefix in ['ejecutar ', 'ejecuta ', 'query ', 'run ', 'consulta sql ', 'sql:']:
            if prefix in tl:
                sql_query = tl.split(prefix, 1)[1].strip()
                break
        for kw in ['select ', 'insert ', 'update ', 'delete ', 'create ', 'alter ',
                    'drop ', 'pragma ', 'explain ']:
            idx = tl.find(kw)
            if idx >= 0:
                sql_query = tl[idx:]
                break
        if not sql_query or len(sql_query) < 6:
            return "Escribe el SQL completo, ej: 'ejecutar SELECT * FROM productos LIMIT 5'"
        sql_upper = sql_query.strip().upper()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('PRAGMA')
                or sql_upper.startswith('EXPLAIN') or sql_upper.startswith('WITH')):
            return "Por seguridad solo se permiten consultas SELECT, PRAGMA y EXPLAIN."
        try:
            rows = _q(sql_query)
            if not rows:
                return "Consulta ejecutada. Sin resultados."
            if len(rows) == 1 and len(rows[0]) == 1:
                v = list(rows[0].values())[0]
                return f"Resultado: {v}"
            cols = list(rows[0].keys())
            lines = [" | ".join(str(c) for c in cols)]
            lines.append("-" * len(lines[0]))
            for r in rows[:15]:
                lines.append(" | ".join(str(r[c]) for c in cols))
            msg = "\n".join(lines)
            if len(rows) > 15:
                msg += f"\n... ({len(rows)} filas totales, mostrando 15)"
            return f"SQL Result ({len(rows)} filas):\n\n{msg}"
        except Exception as e:
            return f"Error SQL: {e}"

    # --- Inteligencia del proyecto para discusión de tesis ---
    if any(k in tl for k in ['inventario proyecto sin omitir', 'json proyecto completo', 'codigo sin omitir']):
        from project_intelligence import json_inventory
        return json_inventory()

    if any(k in tl for k in ['defensa completa', 'discusion tesis', 'discusión tesis',
                              'explica proyecto completo', 'informe tesis']):
        import json
        from project_intelligence import thesis_defense_summary
        return json.dumps(thesis_defense_summary(), ensure_ascii=False, indent=2)

    if any(k in tl for k in ['estructura de carpetas', 'estructura carpetas',
                              'organizacion repositorio', 'organización repositorio']):
        import json
        from project_intelligence import folder_structure
        return json.dumps(folder_structure(), ensure_ascii=False, indent=2)

    if any(k in tl for k in ['modulos y funciones', 'módulos y funciones',
                              'funciones del modulo', 'funciones del módulo',
                              'explica modulo', 'explica módulo']):
        from project_intelligence import find_modules, format_module_report
        modules = find_modules(tl, limit=5)
        return format_module_report(modules) if modules else "No encontré un módulo coincidente. Indica el nombre del archivo o función."

    # --- Estado del sistema / telemetria (OFFLINE PURO) ---
    if any(k in tl for k in ['estado', 'sistema', 'db', 'tablas', 'base de datos',
                              'telemetria', 'info sistema', 'version', 'version apk']):
        import sys
        prods = 0; ventas = 0
        r1 = _q1("SELECT COUNT(*) as n FROM productos WHERE activo=1")
        if r1: prods = r1.get('n', 0)
        r2 = _q1("SELECT COUNT(*) as n FROM historial_ventas")
        if r2: ventas = r2.get('n', 0)
        
        # Listar tablas
        tables = _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        table_list = ", ".join(t['name'] for t in tables[:15]) if tables else "N/A"
        
        msg = (f"Sistema TPV Ultra Smart v{__version__}\n"
               f"===========================\n"
               f"Python: {sys.version.split()[0]}\n"
               f"Productos: {prods}\n"
               f"Ventas: {ventas}\n"
               f"Arquitectura: Flask + Chaquopy + SQLite\n"
               f"IA: Handlers simbolicos offline\n"
               f"Modo: OFFLINE-FIRST (no necesita internet)\n\n"
               f"Tablas BD ({len(tables) if tables else 0}):\n  {table_list}")
        return msg

    # --- Integridad de BD ---
    if any(k in tl for k in ['integridad', 'check', 'verificar bd', 'salud',
                              'prueba base', 'quick check']):
        r = _q1("PRAGMA quick_check")
        status = r.get('quick_check', 'unknown') if r else 'error'
        size = 0
        try:
            import os as _os
            db = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'tpv_datos.db')
            size = os.path.getsize(db) if os.path.exists(db) else 0
        except: pass
        
        tables = _q("SELECT name FROM sqlite_master WHERE type='table'")
        msg = f"Integridad BD: {status.upper()}\nTamaño: {size / 1024:.1f} KB\n\nTablas:\n"
        for t_row in (tables or []):
            try:
                cnt = _q1(f"SELECT COUNT(*) as n FROM {t_row['name']}")
                n = cnt.get('n', 0) if cnt else 0
                if n > 0:
                    msg += f"  {t_row['name']}: {n} rows\n"
            except:
                msg += f"  {t_row['name']}: (error leyendo)\n"
        return msg

    # --- Logs / auditoria ---
    if any(k in tl for k in ['logs', 'errores', 'auditoria', 'eventos']):
        rows = _q("SELECT fecha, tipo, mensaje FROM logs_sistema ORDER BY fecha DESC LIMIT 10")
        if not rows:
            return "Logs limpios. No hay eventos recientes."
        msg = "Ultimos 10 eventos:\n"
        for r in rows:
            icon = "[ERROR]" if r['tipo'] == 'error' else "[INFO]"
            msg += f"  {icon} [{str(r['fecha'])[-8:]}] {r['mensaje'][:50]}\n"
        return msg

    # --- Usuarios ---
    if any(k in tl for k in ['usuarios', 'roles', 'activos', 'quien esta', 'staff']):
        rows = _q("SELECT rol, COUNT(*) as c FROM usuarios WHERE activo=1 GROUP BY rol")
        if not rows:
            return "No hay usuarios registrados."
        msg = "Usuarios activos por rol:\n"
        for r in rows:
            msg += f"  {r['rol'].capitalize()}: {r['c']}\n"
        total = sum(r['c'] for r in rows)
        msg += f"\nTotal: {total} usuarios"
        return msg

    # --- Seguridad ---
    if any(k in tl for k in ['seguridad', 'security', 'audit']):
        users = _q1("SELECT COUNT(*) as n FROM usuarios WHERE activo=1")
        audit = 0
        try:
            a = _q1("SELECT COUNT(*) as n FROM audit_logs")
            if a: audit = a.get('n', 0)
        except: pass
        return (f"Estado de Seguridad:\n"
                f"  Usuarios activos: {users.get('n', 0) if users else 0}\n"
                f"  Registros auditoria: {audit}\n"
                f"  Hashing: SHA-256\n"
                f"  Rate limiting: activo\n"
                f"  Guardrails: SQLi, XSS, PII\n"
                f"  BD: SQLite WAL")

    # --- Documentacion (lee de tabla local, 100% offline) ---
    if any(k in tl for k in ['documentacion', 'docs', 'estructura', 'endpoints',
                              'arquitectura', 'rutas', 'api docs', 'manual',
                              'readme', 'changelog', 'schema', 'licencia']):
        docs = _q("SELECT nombre FROM documentacion ORDER BY nombre")
        if not docs:
            return "No hay documentos en la base local. Usa 'ejecutar SELECT * FROM documentacion' para verificar."
        msg = "Documentos disponibles (lectura offline):\n\n"
        for d in docs:
            msg += f"  - {d['nombre']}\n"
        msg += "\nPara leer un documento: 'lee el documento README.md'\n"
        msg += "O usa SQL: 'ejecutar SELECT contenido FROM documentacion WHERE nombre=\"README.md\"'"
        return msg

    # --- Leer documento especifico ---
    if any(k in tl for k in ['lee el', 'leer el', 'abrir el', 'mostrar el',
                              'ver el', 'documento', 'lee la', 'leer la',
                              'dame el', 'quiero ver', 'quiero leer']):
        try:
            from db_connection import obtener_conexion
            from documentation_loader import find_document

            conn = obtener_conexion()
            try:
                matched = find_document(conn, tl)
            finally:
                conn.close()
            if matched:
                name, content, total = matched
                preview = '\n'.join(content.splitlines()[:25])
                suffix = f"\n\n... ({total - 25} lineas mas.)" if total > 25 else ""
                return f"--- {name} ({total} lineas) ---\n\n{preview}{suffix}"
        except Exception:
            pass

        doc_map = {
            'readme': 'README.md', 'licencia': 'LICENSE', 'license': 'LICENSE',
            'api': 'API_REFERENCE.md', 'endpoints': 'API_REFERENCE.md',
            'arquitectura': 'ARCHITECTURE.md', 'architecture': 'ARCHITECTURE.md',
            'schema': 'DATABASE_SCHEMA.md', 'database': 'DATABASE_SCHEMA.md',
            'base de datos': 'DATABASE_SCHEMA.md', 'changelog': 'CHANGELOG.md',
            'cambios': 'CHANGELOG.md',
            'desarrollador': 'DEVELOPER_GUIDE.md', 'developer': 'DEVELOPER_GUIDE.md',
            'acceso total': 'DEVELOPER_GUIDE.md', 'sin limites': 'DEVELOPER_GUIDE.md',
            'roadmap': 'ROADMAP_10_10.md', '10/10': 'ROADMAP_10_10.md',
        }
        for kw, fname in doc_map.items():
            if kw in tl:
                doc = _q1("SELECT contenido FROM documentacion WHERE nombre=?", (fname,))
                if doc and doc.get('contenido'):
                    lines = doc['contenido'].split('\n')
                    preview = '\n'.join(lines[:25])
                    total = len(lines)
                    if total > 25:
                        preview += f"\n\n... ({total - 25} lineas mas. Usa SQL para ver todo.)"
                    return f"--- {fname} ({total} lineas) ---\n\n{preview}"
                else:
                    return f"Documento '{fname}' no encontrado en la base local."
        # Si menciona "documento" pero no coincide con ningun nombre
        if 'documento' in tl:
            return "Especifica que documento: 'lee el documento README.md', 'lee el documento API_REFERENCE.md'"

    # --- Telecomunicaciones: mediciones reales y metodología explícita ---
    if any(k in tl for k in ['json telecom completo', 'datos telecom crudos', 'telecom sin omitir']):
        import json
        from modules.telecom_diag import diagnostico_completo
        return json.dumps(diagnostico_completo(), ensure_ascii=False, indent=2)
    if any(k in tl for k in ['diagnostico completo', 'diagnóstico completo', 'telecom completo']):
        from modules.telecom_diag import formato_humano_diagnostico
        return formato_humano_diagnostico()
    if any(k in tl for k in ['throughput', 'goodput', 'ancho de banda', 'velocidad red']):
        from modules.telecom_diag import medir_throughput_supabase
        result = medir_throughput_supabase()
        if not result.get('ok'):
            return f"Goodput HTTP no disponible: {result.get('error', 'error')}"
        return (f"Goodput HTTP: {result['throughput_mbps']} Mbps "
                f"({result['throughput_kib_s']} KiB/s)\n"
                f"Muestra: {result['bytes_recibidos']} bytes en {result['tiempo_s']} s.\n"
                f"Limitacion: {result['limitacion']}")
    if any(k in tl for k in ['dns', 'resolucion', 'resolución']):
        from modules.telecom_diag import medir_dns
        result = medir_dns()
        return (f"DNS: {result.get('host', '?')} -> {result.get('ip_principal', result.get('error', '?'))}\n"
                f"Tiempo getaddrinfo: {result.get('tiempo_ms', 'N/D')} ms")
    if any(k in tl for k in ['tls', 'certificado', 'cipher', 'handshake']):
        from modules.telecom_diag import medir_tls_handshake
        result = medir_tls_handshake()
        if not result.get('ok'):
            return f"TLS no disponible: {result.get('error', 'error')}"
        return (f"TLS: {result['tls_version']} / {result['cipher']} ({result['cipher_bits']} bits)\n"
                f"TCP: {result['tiempo_tcp_ms']} ms | handshake TLS: {result['tiempo_tls_ms']} ms")
    if any(k in tl for k in ['latencia', 'jitter', 'perdida', 'pérdida', 'rtt', 'ping']):
        from modules.telecom_diag import medir_latencia_supabase
        result = medir_latencia_supabase()
        if not result.get('ok'):
            return f"RTT HTTP no disponible: {result.get('error', 'error')}"
        return (f"RTT HTTP (no ICMP): media {result['latencia_media_ms']} ms, "
                f"P95 {result['latencia_p95_ms']} ms\n"
                f"Jitter {result['jitter_ms']} ms | solicitudes fallidas {result['perdida_pct']}%\n"
                f"Calidad: {result['calidad']['nivel']} ({result['calidad']['score']}/100)")
    if any(k in tl for k in ['red', 'conexion', 'conexión', 'enlace', 'telecom', 'mi ip']):
        from modules.telecom_diag import info_red_local, velocidad_sqlite
        local = info_red_local()
        sqlite = velocidad_sqlite()
        return (f"Endpoint local: {local.get('hostname', '?')} / {local.get('ip_local', '?')}\n"
                f"Plataforma: {local.get('plataforma', '?')}\n"
                f"Plano local SQLite: {sqlite.get('ops_por_segundo', 0)} ops/s; "
                f"integridad {str(sqlite.get('quick_check', '?')).upper()}\n"
                "Use 'diagnostico completo' para medir DNS, HTTP RTT, goodput y TLS.")

    # --- Productos / inventario ---
    if any(k in tl for k in ['productos', 'inventario', 'stock']):
        total = 0; agotados = 0
        r1 = _q1("SELECT COUNT(*) as n FROM productos WHERE activo=1")
        if r1: total = r1.get('n', 0)
        r2 = _q1("SELECT COUNT(*) as n FROM inventario_general WHERE stock_actual <= 0")
        if r2: agotados = r2.get('n', 0)
        return f"Productos activos: {total}\nAgotados: {agotados}\n\nUsa 'ejecutar SELECT nombre, precio FROM productos LIMIT 10' para ver detalles."

    # --- Ventas generales ---
    if any(k in tl for k in ['ventas', 'balance', 'ganancias', 'ingresos']):
        d = F.diario()
        sem = F.semanal()
        return (f"Ventas:\n"
                f"  Hoy: {d['t']} ops / {fmt_money(d['r'])}\n"
                f"  Semana: {sem['t']} ops / {fmt_money(sem['r'])}\n"
                f"  Gastos hoy: {fmt_money(d['g'])}")

    # --- Ayuda ---
    if any(k in tl for k in ['como usar', 'ayuda', 'help', 'manual', 'guia', 'que puedes']):
        return ("GUIA EXHAUSTIVA DEL DESARROLLADOR\n"
                "=================================\n"
                "Identidad: usuario y rol desarrollador únicos.\n"
                "Capacidad: all; sin límites funcionales de negocio.\n"
                "Controles activos: autenticación, sesión, auditoría, validación y secretos.\n\n"
                "SISTEMA Y DATOS\n"
                "  - 'estado' / 'sistema': versión, Python, tablas, productos y ventas.\n"
                "  - 'integridad': PRAGMA quick_check, tamaño y conteos de tablas.\n"
                "  - 'ejecutar SELECT ...': SQL de solo lectura (SELECT/PRAGMA/EXPLAIN/WITH).\n"
                "  - 'logs': eventos recientes y auditoría.\n"
                "  - 'usuarios': cuentas activas por rol.\n"
                "  - 'seguridad': hashing, rate limit, SQLi, XSS y auditoría.\n\n"
                "TELECOMUNICACIONES\n"
                "  - 'diagnóstico completo': endpoint, DNS, TCP, TLS, RTT HTTP, P95, jitter, fallos, goodput y SQLite.\n"
                "  - 'telecom sin omitir': JSON completo con todos los campos medidos.\n"
                "  - 'latencia' / 'jitter' / 'rtt': medición HTTP (no ICMP).\n"
                "  - 'throughput' / 'goodput': muestra útil Mbps y KiB/s.\n"
                "  - 'dns': resolución y tiempo getaddrinfo.\n"
                "  - 'tls': versión, cipher, certificado y tiempos TCP/TLS.\n"
                "  - 'mi ip' / 'red': endpoint local y plano SQLite.\n\n"
                "NEGOCIO\n"
                "  - 'productos' / 'inventario' / 'stock': activos y agotados.\n"
                "  - 'ventas' / 'balance' / 'ganancias': día y semana.\n"
                "  - Puede acceder además a caja, cierres, gastos, reportes, licencias, configuración y Supabase.\n\n"
                "TESIS Y CÓDIGO\n"
                "  - 'defensa completa': problema, hipótesis, arquitectura, IA, Telecom, seguridad, calidad y limitaciones.\n"
                "  - 'estructura de carpetas': organización real del repositorio.\n"
                "  - 'módulos y funciones <nombre>': clases, métodos, firmas, líneas, docstrings y rutas.\n"
                "  - 'inventario proyecto sin omitir': JSON AST; descarga íntegra en /api/dev/project/inventory.\n\n"
                "DOCUMENTACIÓN\n"
                "  - 'documentación': índice completo offline.\n"
                "  - 'lee el documento X': lectura paginada sin omitir contenido.\n"
                "  - 'siguiente': continúa hasta la última línea.\n"
                "  - Documentos clave: DEVELOPER_GUIDE, TELECOM_ENGINEERING, ARCHITECTURE, API_REFERENCE y DATABASE_SCHEMA.\n\n"
                "Use 'ayuda' para este índice, un comando específico para datos actuales y 'siguiente' para documentos largos.")

    # --- Hola ---
    if _fm(agent, t, ['hola', 'hey', 'buenas']):
        return f"Panel de desarrollador activo, {name}. Consola IA lista. Puedes pedirme: estado del sistema, integridad db, logs, SQL o documentacion."

    # --- Fallback inteligente para dev ---
    # Si el usuario escribio algo que parece una consulta, intentar SQL
    if len(tl) > 10 and ('select' in tl or 'count' in tl or 'from' in tl or 'where' in tl):
        return "Parece que quieres ejecutar SQL. Usa: 'ejecutar SELECT ...'"

    return "Dev tools: estado, integridad, ejecutar SQL, documentacion, logs, usuarios, seguridad, red. Escribe 'ayuda' para ver todo."
