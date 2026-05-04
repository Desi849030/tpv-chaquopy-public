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
