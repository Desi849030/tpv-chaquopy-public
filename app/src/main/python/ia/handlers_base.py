"""handlers_base.py - Extracted from handlers.py"""
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
