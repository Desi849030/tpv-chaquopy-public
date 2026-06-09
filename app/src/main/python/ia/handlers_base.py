# -*- coding: utf-8 -*-
"""
Handlers Base del Agente - Funciones compartidas por handlers especializados
"""
import logging

logger = logging.getLogger(__name__)


def _fm(agent, text, keywords, threshold=0.85):
    """Fuzzy match: verifica si el texto contiene alguno de los keywords.
    Coincidencia exacta primero; fallback difuso con umbral ALTO (0.85) para
    evitar falsos positivos (ej. 'critico' confundido con 'comision')."""
    if not text or not keywords:
        return False
    tl = text.lower().strip()
    # Coincidencia exacta primero (rapido y preciso)
    for kw in keywords:
        if kw.lower() in tl:
            return True
    # Fallback: coincidencia difusa solo para palabras de longitud similar
    try:
        from ia.fuzzy_match import best_match
        for word in tl.split():
            if len(word) < 4:
                continue
            match, score = best_match(word, [kw.lower() for kw in keywords],
                                      threshold=threshold * 100)
            # Exigir longitud parecida para evitar match espurio
            if match and abs(len(word) - len(match)) <= 2:
                return True
    except Exception:  # noqa: broad-except - graceful degradation
        pass
    return False


def _follow(role='cliente'):
    """Mensaje de seguimiento contextual segun el rol."""
    followups = {
        'cliente': "¿Algo mas en lo que pueda ayudarle?",
        'vendedor': "¿Necesita algo mas? Ventas, stock, top.",
        'supervisor': "¿Consulto algo mas? Dashboard, tendencias, inventario.",
        'administrador': "¿Requiere otro reporte? Finanzas, ABC, EOQ.",
        'desarrollador': "¿Debug algo mas? Logs, metricas, estado del sistema."
    }
    return followups.get(role, followups['cliente'])


def _get_sug(role='cliente'):
    """Sugerencias contextuales segun el rol."""
    suggestions = {
        'cliente': ["ofertas", "categorias", "precio de producto"],
        'vendedor': ["ventas hoy", "stock bajo", "top productos"],
        'supervisor': ["dashboard", "predicciones", "rotacion"],
        'administrador': ["finanzas", "ABC", "punto equilibrio"],
        'desarrollador': ["metricas", "logs", "estado sistema"]
    }
    return suggestions.get(role, suggestions['cliente'])


def greet(role='cliente', name='amigo'):
    if role == 'administrador':
        return f"¡Hola {name}! Panel de administración activo."
    elif role == 'vendedor':
        return f"¡Hola {name}! Listo para vender."
    else:
        return f"¡Hola {name}! Bienvenido ☕"


def handle_products(role='cliente'):
    return "📦 Consultando productos..."


def handle_stock(role='cliente'):
    if role in ['administrador', 'vendedor']:
        return "📦 Inventario completo disponible."
    else:
        return "📦 Tenemos productos disponibles."


def say_goodbye(name='amigo'):
    return f"¡Hasta luego, {name}! 👋"


def help_text(role='cliente'):
    """Texto de ayuda contextual segun el rol."""
    helps = {
        'cliente': "Puedo mostrarle nuestro catalogo, precios y ofertas.",
        'vendedor': "Puedo informarle sobre ventas, stock y productos mas vendidos.",
        'supervisor': "Tengo listo el dashboard con KPIs y tendencias.",
        'administrador': "Puedo generarle reportes financieros, ABC y proyecciones.",
        'desarrollador': "Acceso total activo. Monitoreo del sistema disponible."
    }
    return helps.get(role, helps['cliente'])


def handle_unknown(text):
    return f"No entendí: {text}. ¿Puedes repetir?"
