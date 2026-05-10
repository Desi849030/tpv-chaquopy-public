# -*- coding: utf-8 -*-
"""diccionario_tpv.py — Diccionario español sinónimos/definiciones offline para el agente IA TPV.

Incluye:
- Busqueda de sinónimos
- Definiciones breves de términos comerciales
- Corrección ortográfica básica (distancia Levenshtein)
- Expansión de consultas (sinónimos para búsqueda de productos)
"""

import unicodedata, re

# ── DICCIONARIO DE SINÓNIMOS COMERCIALES ──
_SINONIMOS = {
    # Productos comunes
    "arroz": ["arroz", "arroz blanco", "arroz precocido"],
    "pan": ["pan", "pan de molde", "pan fresco", "pan integral"],
    "leche": ["leche", "leche entera", "leche descremada", "leche evaporada"],
    "cafe": ["café", "cafe molido", "cafe en grano", "cafe instantaneo"],
    "azucar": ["azúcar", "azucar blanca", "azucar morena"],
    "aceite": ["aceite", "aceite vegetal", "aceite de cocina", "aceite comestible"],
    "gaseosa": ["gaseosa", "refresco", "soda", "bebida gaseosa"],
    "agua": ["agua", "agua embotellada", "agua mineral"],
    "pollo": ["pollo", "pechuga de pollo", "muslo de pollo"],
    "carne": ["carne", "carne de res", "res", " carne molida", "carne para cocinar"],
    "cerdo": ["cerdo", "carne de cerdo", "chuleta", "costilla"],
    "huevo": ["huevo", "huevos", "huevo de gallina"],
    "jabon": ["jabón", "jabon de tocador", "jabon en barra"],
    "pasta": ["pasta", "espagueti", "fideo", "tallarines", "macarrones"],
    "tomate": ["tomate", "jitomate", "tomate rojo"],
    "cebolla": ["cebolla", "cebolla blanca", "cebolla morada"],
    "ajo": ["ajo", "cabeza de ajo", "dientes de ajo"],
    "sal": ["sal", "sal fina", "sal gruesa"],
    "harina": ["harina", "harina de trigo", "harina de maiz"],
    "queso": ["queso", "queso blanco", "queso amarillo", "queso cremoso"],
    "yogur": ["yogur", "yogurt", "yogurth"],
    "detergente": ["detergente", "detergente en polvo", "detergente liquido", "jabon para ropa"],
    "papel": ["papel higienico", "papel de baño", "rollo de papel"],

    # Verbos de búsqueda
    "buscar": ["buscar", "encontrar", "localizar", "consultar", "ver"],
    "comprar": ["comprar", "adquirir", "obtener"],
    "vender": ["vender", "ofrecer", "comercializar"],
    "precio": ["precio", "costo", "valor", "cuanto cuesta", "cuanto vale"],
    "stock": ["stock", "inventario", "existencia", "disponibilidad", "cantidades"],
    "gasto": ["gasto", "egreso", "salida", "costo operativo"],
    "ganancia": ["ganancia", "utilidad", "beneficio", "rentabilidad", "margen"],
    "venta": ["venta", "transaccion", "operacion", "facturacion"],
}

# ── DEFINICIONES COMERCIALES ──
_DEFINICIONES = {
    "precio de venta": "Monto al que se ofrece un producto al cliente final. Es la base para calcular ganancias y márgenes.",
    "precio de compra": "Costo que pagó el negocio al proveedor por adquirir el producto. También llamado costo o precio de adquisición.",
    "ganancia": "Diferencia entre el precio de venta y el precio de compra. Si es positiva, el negocio gana dinero.",
    "margen": "Porcentaje de ganancia sobre el precio de venta. Fórmula: (precio_venta - precio_compra) / precio_venta × 100.",
    "inventario": "Conjunto de productos disponibles en el almacén o tienda. Incluye cantidades y precios.",
    "stock minimo": "Cantidad mínima de un producto que debe haber disponible. Si baja, se debe reordenar.",
    "ticket promedio": "Valor promedio de cada venta. Se calcula: ingresos totales / número de transacciones.",
    "kpi": "Indicador Clave de Rendimiento (Key Performance Indicator). Métrica para evaluar el desempeño del negocio.",
    "cross-selling": "Venta cruzada: sugerir productos complementarios al cliente para aumentar el ticket promedio.",
    "abc": "Análisis ABC: clasificar productos según su contribución a las ventas. A=80% ventas, B=15%, C=5%.",
    "punto de reorden": "Stock mínimo que activa una nueva orden de compra al proveedor.",
    "vaucher": "Documento fiscal que respalda cada transacción de venta. Obligatorio para la contabilidad.",
    "factura": "Documento comercial detallado con los productos vendidos, precios, impuestos y total.",
    "devolucion": "Retorno de un producto por parte del cliente. Genera reembolso o cambio.",
    "descuento": "Reducción del precio de venta. Puede ser porcentual o en monto fijo.",
    "impuesto": "Tasa que se añade al precio de venta. Ejemplo: IVA, ITBIS, ISS.",
    "proveedor": "Persona o empresa que suministra productos al negocio.",
    "cliente": "Persona que compra productos en el establecimiento.",
    "lealtad": "Programa para fidelizar clientes mediante puntos, descuentos o beneficios acumulables.",
}

# ── CORRECCIONES ORTOGRÁFICAS COMUNES ──
_CORRECCIONES = {
    "parce": "precio", "presio": "precio", "prezio": "precio",
    "astes": "hasta", "asta": "hasta",
    "bevida": "bebida", "bevidas": "bebidas",
    "asucar": "azúcar", "azucar": "azúcar",
    "jabon": "jabón",
    "manteka": "manteca", "mantéka": "manteca",
    "aseite": "aceite", "aseinte": "aceite",
    "aves": "huevo", "guebo": "huevo",
    "queso": "queso", "quezo": "queso",
    "tomate": "tomate", "jitomarte": "jitomate",
    "cebolla": "cebolla", "sebolla": "cebolla",
    "puela": "pollo", "poyo": "pollo",
    "gaseosa": "gaseosa", "gasiosa": "gaseosa",
    "dentrigente": "detergente", "deterjente": "detergente",
    "pan": "pan", "pam": "pan",
    "leche": "leche", "lece": "leche",
    "cafe": "café", "café": "café", "cafeé": "café",
    "aros": "arroz", "arro": "arroz", "arroz": "arroz",
    "sal": "sal", "zal": "sal",
    "gansia": "ganancia", "gananccia": "ganancia",
    "benta": "venta", "vent": "venta",
    "stoock": "stock", "stok": "stock", "estok": "stock",
    "imventorio": "inventario", "inventário": "inventario",
    "margen": "margen", "margem": "margen",
    "proveeor": "proveedor", "porveedor": "proveedor",
    "clinte": "cliente", "liente": "cliente",
    "deskontar": "descuento", "decuento": "descuento",
}


def _levenshtein(a, b):
    """Distancia de Levenshtein entre dos cadenas."""
    a = _sin_tildes(a).lower()
    b = _sin_tildes(b).lower()
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + cost, prev[j] + 1))
        prev = curr
    return prev[-1]


def _sin_tildes(text):
    """Elimina tildes para comparación."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def buscar_sinonimos(palabra):
    """Busca sinónimos de una palabra. Retorna lista."""
    key = _sin_tildes(palabra).lower().strip()
    for k, v in _SINONIMOS.items():
        if _sin_tildes(k) == key:
            return v
        for s in v:
            if _sin_tildes(s) == key:
                return v
    # Búsqueda fuzzy
    resultados = []
    for k, v in _SINONIMOS.items():
        dist = _levenshtein(key, _sin_tildes(k))
        if dist <= 2:
            resultados.extend(v)
    return list(set(resultados))[:8] if resultados else []


def definir_termino(termino):
    """Busca definición de un término comercial."""
    key = _sin_tildes(termino).lower().strip()
    for k, v in _DEFINICIONES.items():
        if _sin_tildes(k) == key:
            return v
        # Búsqueda parcial
        if key in _sin_tildes(k) or _sin_tildes(k) in key:
            return v
    return None


def corregir(palabra):
    """Sugiere corrección ortográfica. Retorna la corrección o None."""
    key = _sin_tildes(palabra).lower().strip()
    if key in _CORRECCIONES:
        return _CORRECCIONES[key]
    # Búsqueda fuzzy en correcciones
    mejor = None
    mejor_dist = 999
    for mal, bien in _CORRECCIONES.items():
        dist = _levenshtein(key, _sin_tildes(mal))
        if dist <= 2 and dist < mejor_dist:
            mejor = bien
            mejor_dist = dist
    return mejor


def expandir_consulta(texto):
    """Expande una consulta con sinónimos para mejorar búsqueda.
    Retorna la consulta original + sinónimos relevantes.
    """
    palabras = re.split(r'[\s,;:]+', texto.lower().strip())
    expandidas = []
    for p in palabras:
        if len(p) <= 2:
            continue
        expandidas.append(p)
        sins = buscar_sinonimos(p)
        if sins:
            expandidas.extend(sins)
    return list(set(expandidas))


# ══════════════════════════════════════════════
#  FLASK BLUEPRINT — Endpoints API
# ══════════════════════════════════════════════
from flask import Blueprint, request, jsonify

diccionario_bp = Blueprint("diccionario", __name__)


def _dev_check():
    """Verifica rol para acceso (desarrollador/admin)."""
    from flask import session
    r = session.get("rol", "")
    return r in ("desarrollador", "administrador", "vendedor")


@diccionario_bp.route("/api/diccionario/sinonimos")
def api_sinonimos():
    if not _dev_check():
        return jsonify({"error": "sin permisos"}), 403
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "parametro q requerido"}), 400
    results = buscar_sinonimos(q)
    return jsonify({"palabra": q, "sinonimos": results, "total": len(results)})


@diccionario_bp.route("/api/diccionario/definicion")
def api_definicion():
    if not _dev_check():
        return jsonify({"error": "sin permisos"}), 403
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "parametro q requerido"}), 400
    definicion = definir_termino(q)
    if definicion:
        return jsonify({"termino": q, "definicion": definicion})
    # Búsqueda fuzzy en definiciones
    sugerencias = []
    for k in _DEFINICIONES:
        dist = _levenshtein(_sin_tildes(q), _sin_tildes(k))
        if dist <= 3:
            sugerencias.append(k)
    return jsonify({"termino": q, "definicion": None, "sugerencias": sugerencias[:5]})


@diccionario_bp.route("/api/diccionario/corregir")
def api_corregir():
    if not _dev_check():
        return jsonify({"error": "sin permisos"}), 403
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "parametro q requerido"}), 400
    correccion = corregir(q)
    if correccion:
        return jsonify({"original": q, "correccion": correccion})
    return jsonify({"original": q, "correccion": None})
