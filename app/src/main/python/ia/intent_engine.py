"""intent_engine.py - Clasificador agentic de intenciones con matching difuso"""
INTENTS = {
    "GREETING": {"k": ["hola","buenos dias","buenas tardes","buenas noches","hey","que tal","saludos","buenas","como estas","buen dia"], "t": "greeting"},
    "FAREWELL": {"k": ["adios","chao","bye","gracias","hasta luego","nos vemos","hasta pronto","nos vemos"], "t": "farewell"},
    "HELP": {"k": ["ayuda","help","que puedes","que sabes","funciones","menu","que haces","como funciona","opciones"], "t": "help"},
    "SALES": {"k": ["ventas","caja","recaude","cuanto vendi","como voy","cuanto llevo","total vendido","facturacion","ticket","cobrado","facture"], "t": "sales"},
    "FINANCE": {"k": ["finanza","ganancia","margen","ingreso","balance","rentabilidad","comision","utilidad","perdida","profit"], "t": "finance"},
    "EXPENSES": {"k": ["gasto","egreso","costo fijo","gastos","pago","pague","gaste"], "t": "expenses"},
    "STOCK_LOW": {"k": ["stock bajo","agotado","critico","reabastecer","faltante","poco stock","sin stock","reponer","falta"], "t": "stock_low"},
    "STOCK_QUERY": {"k": ["stock","inventario","disponible","cuanto hay","hay de","quedan","existencia","cuantas unidades","cuanto hay de"], "t": "stock_query"},
    "TOP_PRODUCTS": {"k": ["top","mas vendido","popular","ranking","mejor","vendidos","producto estrella","lo mas vendido","favoritos"], "t": "top"},
    "TRENDS": {"k": ["tendencia","prediccion","proyeccion","forecast","pronostico","como va el negocio","futuro"], "t": "trends"},
    "ROTATION": {"k": ["rotacion","indice rotacion","movimiento inventario","giro"], "t": "rotation"},
    "ABC": {"k": ["abc","pareto","clasificacion","categorias producto","analisis abc"], "t": "abc"},
    "EOQ": {"k": ["eoq","lote optimo","pedido optimo","cuanto pedir","cuanto ordenar"], "t": "eoq"},
    "OFFERS": {"k": ["oferta","descuento","rebaja","mejor precio","barato","promo","promocion","liquidacion","ganga"], "t": "offers"},
    "CATEGORIES": {"k": ["categorias","catalogo","que tienen","secciones","que venden","departamento","tipos","rubros"], "t": "categories"},
    "PRODUCT_SEARCH": {"k": ["precio","cuanto cuesta","valor","busco","necesito","quiero comprar","donde encuentro","tiene"], "t": "product_search"},
    "LOYALTY": {"k": ["puntos","lealtad","fidelidad","recompensa","beneficio","acumulado","canjear"], "t": "loyalty"},
    "PAYMENT": {"k": ["pago","pagar","efectivo","tarjeta","transferencia","metodo","forma de pago","cobrar"], "t": "payment"},
    "HISTORY": {"k": ["mis compras","historial","compre","recibo","factura","compras anteriores"], "t": "history"},
    "DASHBOARD": {"k": ["dashboard","resumen","estado","kpi","metricas","panel","general","como vamos"], "t": "dashboard"},
    "FRUSTRATION": {"k": ["error","mal","no funciona","falla","roto","no sirve","no entiendo","problema","urgente","pesimo"], "t": "frustration"},
}

ROLE_ACCESS = {
    "cliente": {"GREETING","FAREWELL","HELP","OFFERS","CATEGORIES","PRODUCT_SEARCH","LOYALTY","PAYMENT","HISTORY","STOCK_QUERY","FRUSTRATION"},
    "vendedor": {"GREETING","FAREWELL","HELP","SALES","STOCK_LOW","STOCK_QUERY","TOP_PRODUCTS","OFFERS","PRODUCT_SEARCH","DASHBOARD","FRUSTRATION"},
}

def detect_intents(text, role="cliente"):
    import re
    from ia.normalizer import contains_any, normalize
    results = []
    normalized = normalize(text)
    for intent_name, intent_data in INTENTS.items():
        keywords = intent_data["k"]
        if not keywords: continue
        # Farewells are security/control-flow intents: require complete words or
        # phrases. Fuzzy matching previously classified "Chaquopy" as "chao".
        if intent_name == "FAREWELL":
            matched = keyword = None
            score = 0.0
            for candidate in keywords:
                normalized_candidate = normalize(candidate)
                if re.search(r"(?:^|\s)" + re.escape(normalized_candidate) + r"(?:$|\s)", normalized):
                    matched, keyword, score = True, candidate, 1.0
                    break
        else:
            matched, keyword, score = contains_any(text, keywords, threshold=0.6)
        if matched:
            results.append({"intent": intent_name, "confidence": score, "keyword": keyword, "type": intent_data["t"]})
    results.sort(key=lambda x: x["confidence"], reverse=True)
    if not results:
        results.append({"intent": "GENERAL", "confidence": 0.3, "keyword": "", "type": "general"})
    return results

def get_suggestions(primary_intent, role="cliente"):
    SUG = {
        "GREETING": {"cliente": ["ofertas","que productos tienen","mis puntos"], "vendedor": ["ventas de hoy","stock bajo"], "supervisor": ["dashboard","ventas"], "administrador": ["finanzas","ABC"]},
        "SALES": {"cliente": ["top vendidos","ofertas"], "vendedor": ["gastos del dia","proyeccion","top vendidos"], "supervisor": ["finanzas","top vendidos"], "administrador": ["gastos","predicciones"]},
        "FINANCE": {"cliente": [], "vendedor": ["ventas","gastos"], "supervisor": ["gastos","ABC","predicciones"], "administrador": ["ABC","gastos","EOQ"]},
        "STOCK_LOW": {"cliente": [], "vendedor": ["top vendidos","orden de pedido"], "supervisor": ["orden de pedido","ventas"], "administrador": ["orden de pedido","EOQ"]},
        "STOCK_QUERY": {"cliente": ["ofertas","categorias"], "vendedor": ["stock bajo","top vendidos"], "supervisor": ["stock bajo","rotacion"], "administrador": ["rotacion","ABC"]},
        "TOP_PRODUCTS": {"cliente": ["ofertas"], "vendedor": ["stock bajo","finanzas"], "supervisor": ["finanzas","ABC"], "administrador": ["ABC","EOQ"]},
        "OFFERS": {"cliente": ["categorias","stock disponible"], "vendedor": ["margen","top vendidos"], "supervisor": ["finanzas","top vendidos"], "administrador": ["ABC","margen"]},
        "PRODUCT_SEARCH": {"cliente": ["ofertas","categorias"], "vendedor": ["stock","margen"], "supervisor": ["finanzas"], "administrador": ["rotacion"]},
        "CATEGORIES": {"cliente": ["ofertas","stock disponible"], "vendedor": ["top vendidos"], "supervisor": ["ventas"], "administrador": ["ABC"]},
        "TRENDS": {"cliente": [], "vendedor": ["ventas"], "supervisor": ["finanzas","ABC"], "administrador": ["EOQ","rotacion"]},
        "FRUSTRATION": {"cliente": ["ayuda"], "vendedor": ["ayuda","ventas"], "supervisor": ["dashboard"], "administrador": ["dashboard"]},
    }
    if primary_intent in SUG:
        rs = SUG[primary_intent]
        if role in rs and rs[role]: return rs[role][:3]
    return ["ayuda"]
