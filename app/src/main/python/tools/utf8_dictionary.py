
"""
utf8_dictionary.py - Diccionario UTF-8 para TPV UltraSmart
Normalización inteligente: mantiene tildes, corrige caracteres problemáticos
"""
import unicodedata
import re

# Caracteres a normalizar (NO incluye tildes ni eñes)
CHAR_MAP = {
    # Comillas tipográficas → rectas
    '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
    # Guiones
    '\u2013': '-', '\u2014': '-', '\u2015': '-',
    # Espacios especiales
    '\u00a0': ' ', '\u202f': ' ',
    # Símbolos
    '\u20ac': '€', '\u00a3': '£', '\u00a5': '¥',
    '\u2264': '<=', '\u2265': '>=', '\u2260': '!=',
    '\u00d7': 'x', '\u00f7': '/',
    '\u00bd': '1/2', '\u00bc': '1/4', '\u00be': '3/4',
    '\u00a9': '(c)', '\u00ae': '(r)', '\u2122': '(tm)',
    '\u00b0': '°', '\u00ba': '°',
    '\u00bf': '¿', '\u00a1': '¡',
    '\u2026': '...', '\u2022': '*',
}

BUSINESS_SYNONYMS = {
    'venta': ['ventas', 'vender', 'vendido', 'facturar', 'facturación', 'cobro'],
    'producto': ['productos', 'artículo', 'artículos', 'item', 'items'],
    'cliente': ['clientes', 'comprador', 'compradores'],
    'stock': ['inventario', 'existencias', 'disponible'],
    'precio': ['precios', 'costo', 'costos', 'valor', 'importe'],
    'categoría': ['categorías', 'tipo', 'tipos', 'rubro'],
    'pago': ['pagos', 'abonar', 'abono', 'liquidar'],
    'compra': ['compras', 'adquirir', 'proveedor', 'proveedores'],
    'ganancia': ['ganancias', 'beneficio', 'utilidad', 'rentabilidad'],
    'gasto': ['gastos', 'egreso', 'egresos'],
    'reporte': ['reportes', 'informe', 'informes', 'estadística'],
    'alerta': ['alertas', 'aviso', 'avisos', 'notificación'],
    'descuento': ['descuentos', 'rebaja', 'promoción', 'ofertas'],
    'cierre': ['cierres', 'arqueo', 'balance'],
    'importar': ['importación', 'excel', 'csv'],
    'exportar': ['exportación', 'descargar'],
    'pedido': ['pedidos', 'orden', 'órdenes'],
    'qr': ['código', 'barras', 'escanear'],
    'sincronizar': ['sync', 'nube', 'supabase', 'online'],
    'ayuda': ['help', 'soporte', 'asistencia'],
    'error': ['errores', 'fallo', 'bug', 'problema'],
    'buscar': ['búsqueda', 'encontrar', 'localizar', 'search'],
    'guardar': ['salvar', 'almacenar', 'save'],
    'eliminar': ['borrar', 'remover', 'quitar'],
    'agregar': ['añadir', 'crear', 'nuevo', 'insertar'],
    'editar': ['modificar', 'cambiar', 'edit'],
    'imprimir': ['print', 'ticket', 'tickets', 'factura'],
}


def normalize_utf8(text: str, remove_accents: bool = False) -> str:
    """
    Normaliza texto UTF-8.
    - remove_accents=False: mantiene tildes y eñes, corrige comillas/guiones
    - remove_accents=True: elimina tildes (para APIs, slugs, JSON keys)
    """
    if not text:
        return ""

    text = str(text)

    # Normalizar Unicode (NFD separa tildes de letras)
    text = unicodedata.normalize('NFKD', text)

    # Reemplazar caracteres mapeados
    for char, replacement in CHAR_MAP.items():
        text = text.replace(char, replacement)

    if remove_accents:
        # Eliminar tildes (diacríticos)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        # Eliminar caracteres no ASCII
        text = text.encode('ascii', 'ignore').decode('ascii')
    else:
        # Recomponer caracteres con tilde (NFC)
        text = unicodedata.normalize('NFC', text)

    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def slugify(text: str) -> str:
    """Convierte a slug URL-safe (sin tildes)"""
    text = normalize_utf8(text, remove_accents=True).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text


def safe_json_key(text: str) -> str:
    """Convierte a clave JSON segura (sin tildes ni espacios)"""
    text = normalize_utf8(text, remove_accents=True)
    text = re.sub(r'[^a-zA-Z0-9_]', '_', text).lower()
    return text


def has_special_chars(text: str) -> bool:
    """Detecta si el texto tiene caracteres especiales (comillas, guiones, etc.)"""
    return text != normalize_utf8(text, remove_accents=False)


def extract_keywords(text: str) -> list:
    """Extrae palabras clave manteniendo tildes"""
    normalized = normalize_utf8(text, remove_accents=False)
    words = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{2,}\b', normalized.lower())
    return list(set(words))


def find_synonyms(word: str) -> list:
    """Encuentra sinónimos (funciona con o sin tildes)"""
    word_no_accents = normalize_utf8(word, remove_accents=True).lower()
    word_with = normalize_utf8(word, remove_accents=False).lower()

    # Buscar en el diccionario
    for key, syns in BUSINESS_SYNONYMS.items():
        key_no = normalize_utf8(key, remove_accents=True).lower()
        if word_no_accents == key_no or word_with == key.lower():
            return syns
        for s in syns:
            s_no = normalize_utf8(s, remove_accents=True).lower()
            if word_no_accents == s_no or word_with == s.lower():
                return [key] + [x for x in syns if x != word]

    return []


def expand_query(query: str) -> str:
    """Expande consulta con sinónimos"""
    words = extract_keywords(query)
    expanded = set()
    for word in words:
        syns = find_synonyms(word)
        expanded.add(word)
        expanded.update(syns[:2])
    return ' '.join(expanded)


# Herramientas para el agente IA
def tool_normalize_text(text: str) -> str:
    """Normaliza texto manteniendo tildes"""
    return normalize_utf8(text, remove_accents=False)


def tool_remove_accents(text: str) -> str:
    """Elimina tildes (para APIs)"""
    return normalize_utf8(text, remove_accents=True)


def tool_slugify(text: str) -> str:
    """Convierte a slug URL-safe"""
    return slugify(text)


def tool_find_synonyms(word: str) -> list:
    """Encuentra sinónimos comerciales"""
    return find_synonyms(word)


def tool_expand_query(query: str) -> str:
    """Expande consulta con sinónimos"""
    return expand_query(query)


def tool_has_special_chars(text: str) -> bool:
    """Detecta caracteres especiales"""
    return has_special_chars(text)


def tool_safe_json_key(text: str) -> str:
    """Convierte a clave JSON segura"""
    return safe_json_key(text)


def tool_extract_keywords(text: str) -> list:
    """Extrae palabras clave manteniendo tildes"""
    return extract_keywords(text)


print(f"📖 Diccionario UTF-8: {len(CHAR_MAP)} chars, {len(BUSINESS_SYNONYMS)} categorías")
