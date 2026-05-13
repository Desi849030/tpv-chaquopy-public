"""fuzzy_match.py - Coincidencia difusa sin dependencias"""
from difflib import SequenceMatcher

def fuzzy_score(text1, text2):
    """Score de similitud entre 0 y 100"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100

def best_match(query, options, threshold=60):
    """Encuentra la mejor coincidencia sobre un umbral"""
    best = None
    best_score = 0
    for option in options:
        score = fuzzy_score(query, option)
        if score > best_score:
            best_score = score
            best = option
    if best_score >= threshold:
        return best, best_score
    return None, 0


_WORD_INDEX = {}

def build_index(names):
    """Construir indice invertido de palabras para busqueda rapida O(1)"""
    global _WORD_INDEX
    _WORD_INDEX = {}
    for name in names:
        for w in name.lower().split():
            if len(w) > 2:
                _WORD_INDEX.setdefault(w, set()).add(name)

def quick_search(query, threshold=60):
    """Busqueda rapida usando indice invertido"""
    global _WORD_INDEX
    if not _WORD_INDEX:
        return best_match(query, list({n for s in _WORD_INDEX.values() for n in s}), threshold)
    words = query.lower().split()
    candidates = set()
    for w in words:
        for name in _WORD_INDEX.get(w, []):
            candidates.add(name)
    if not candidates:
        return best_match(query, list({n for s in _WORD_INDEX.values() for n in s}), threshold)
    return best_match(query, list(candidates), threshold)

def contains_frustration(text):
    """Detecta si el usuario está frustrado"""
    frustration_words = [
        "error", "mal", "no funciona", "falla", "roto", "no sirve",
        "no entiendo", "problema", "ayuda", "urgente", "pésimo"
    ]
    text_lower = text.lower()
    for word in frustration_words:
        if word in text_lower:
            return True
    return False
