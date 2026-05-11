"""handlers_cliente.py - Extracted from handlers.py"""
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


from ia.handlers_base import _fm, _follow, _get_sug

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
