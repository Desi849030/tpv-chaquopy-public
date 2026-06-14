# -*- coding: utf-8 -*-
"""handlers_cliente.py - Role-specific IA handlers para Cliente (Nivel 10/10)"""
from datetime import datetime
from ia.db_utils import q, fmt_money, pct
from ia.catalog import P, O
from ia.metrics import F, M
from ia.handlers_base import _fm, _follow, _get_sug

def handle_cliente(agent, t, m=None):
    if m is None:
        m = {}

    if _fm(agent, t, ["ayuda", "qué puedes", "qué haces", "cómo funciona", "menu", "opciones"]):
        return ("Puedo ayudarte con muchas cosas:\n\n"
                "- Buscar productos y precios\n"
                "- Ver ofertas y descuentos\n"
                "- Consultar stock disponible\n"
                "- Ver categorías del catálogo\n\n"
                "Escribe lo que necesites.")
                
    if _fm(agent, t, ["login", "iniciar sesion", "acceder", "entrar", "contraseña", "password"]):
        return ("Para acceder al sistema necesitas usuario y contraseña.\n"
                "Solicita tus credenciales al administrador del negocio.\n"
                "Mientras tanto, puedo ayudarte a buscar productos y precios.")

    if _fm(agent, t, ["horario", "abierto", "cerrado", "donde", "ubicación", "direccion"]):
        return "Consulte los detalles de horario y ubicación en la sección de Tienda."

    if _fm(agent, t, ["oferta", "descuento", "rebaja", "mejor precio", "barato", "promo"]):
        of = O.mejores()
        if not of:
            return "Hoy todos nuestros precios son muy competitivos. Escribe el nombre de un producto para buscarlo."
        msg = "🔥 Ofertas disponibles:\n\n"
        for i, o in enumerate(of, 1):
            ahorro = o["p"] - o["d"]
            msg += f"{i}. {o['n']}: {fmt_money(o['d'])} (Ahorras {fmt_money(ahorro)})\n"
        return msg

    if _fm(agent, t, ["categorías", "catálogo", "secciones", "departamento"]):
        cats = ", ".join(P.cats[:15]) if P.cats else "General"
        return f"Contamos con {len(P.cats)} categorías: {cats}.\n\nEscribe el nombre de una para ver más."

    if _fm(agent, t, ["hola", "buenas", "buenos", "buenas tardes", "buenas noches", "hey"]):
        return ("¡Hola! Soy tu asistente y estoy aquí para ayudarte. "
                "Puedes preguntarme sobre productos, precios, ofertas o stock disponible.")

    # BÚSQUEDA ROBUSTA DE PRODUCTOS (Fuzzy Match / Búsqueda en caché)
    import re
    _term = re.sub(r'\b(precio|cuesta|vale|de|del|hay|tienes|stock|busco)\b', ' ', t.lower()).strip()
    prods = P.search(_term or t, 8)
    
    if prods:
        m["p"] = prods[0]["n"] # Guardar en memoria el producto consultado
        if len(prods) == 1:
            p = prods[0]
            msg = f"{p['n']}: {fmt_money(p['p'])} por {p['u']}.\n"
            if p["s"] == 0:
                msg += "Momentáneamente agotado. "
            elif p["s"] <= 3:
                msg += f"¡Date prisa! Últimas {int(p['s'])} unidades."
            else:
                msg += f"Stock disponible: {int(p['s'])} {p['u']}."
            return msg
        else:
            msg = f"Encontré {len(prods)} resultados:\n\n"
            for p in prods[:8]:
                si = f" | {int(p['s'])} {p['u']}" if p["s"] > 0 else " | AGOTADO"
                msg += f" - {p['n']}: {fmt_money(p['p'])}{si}\n"
            return msg + "\n¿Te interesa alguno en particular?"

    return ("Con gusto te ayudo. Puedes preguntarme sobre productos, precios, "
            "ofertas, stock, o escribir 'ayuda' para ver todo lo que puedo hacer.")
