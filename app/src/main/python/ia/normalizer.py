"""normalizer.py - Normalizacion de texto para matching difuso"""
import re
import unicodedata

UNACCENT = {
    "\u00e1":"a","\u00e9":"e","\u00ed":"i","\u00f3":"o","\u00fa":"u","\u00fc":"u","\u00f1":"n",
    "\u00c1":"A","\u00c9":"E","\u00cd":"I","\u00d3":"O","\u00da":"U","\u00dc":"U","\u00d1":"N"
}

def normalize(text):
    """Normaliza texto: minusculas, sin tildes, sin especiales."""
    if not text: return ""
    t = text.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def normalize_preserve(text):
    """Normaliza pero preserva tildes."""
    if not text: return ""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9\u00e1-\u00fa\u00fc\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def contains_any(text, keywords, threshold=0.7):
    """Verifica si texto contiene alguno de los keywords (fuzzy)."""
    from ia.fuzzy_match import best_match
    norm = normalize(text)
    for kw in keywords:
        norm_kw = normalize(kw)
        if norm_kw in norm:
            return True, kw, 1.0
    norms_kw = [normalize(k) for k in keywords]
    for word in norm.split():
        if len(word) < 3:
            continue
        best, score = best_match(word, norms_kw, threshold=threshold*100)
        if best:
            idx = norms_kw.index(best)
            return True, keywords[idx], score/100
    return False, None, 0

def extract_entities(text):
    """Extrae posibles nombres de productos del texto."""
    words = normalize_preserve(text).split()
    entities = []
    skip = {"el","la","los","las","un","una","de","del","en","con","por","para",
           "que","y","o","es","son","tiene","hay","cuanto","como","donde",
           "cuando","cual","quien","muy","mas","menos","sobre","entre","sin",
           "a","al","su","mi","tu","se","me","te","le","nos","les","lo",
           "este","esta","ese","esa","aqui","alli","ya","no","si","bien",
           "mal","ok","va","voy"}
    for w in words:
        if len(w) > 2 and w not in skip:
            entities.append(w)
    return entities