"""validators.py — Validacion de entradas v2.3.0"""
import re

def sanitize_string(text, max_length=500):
    if not isinstance(text, str):
        return str(text)
    text = text.strip()
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return text[:max_length]

def validate_product_name(name):
    if not name or len(name) < 1:
        return False, "Nombre vacio"
    if len(name) > 200:
        return False, "Nombre demasiado largo (max 200)"
    return True, ""

def validate_price(price):
    try:
        p = float(price)
        if p < 0:
            return False, "Precio no puede ser negativo"
        if p > 999999999:
            return False, "Precio excesivo"
        return True, ""
    except (ValueError, TypeError):
        return False, "Precio invalido"

def validate_quantity(qty):
    try:
        q = int(qty)
        if q < 0:
            return False, "Cantidad no puede ser negativa"
        if q > 999999:
            return False, "Cantidad excesiva"
        return True, ""
    except (ValueError, TypeError):
        return False, "Cantidad invalida"

def validate_phone(phone):
    if not phone:
        return False, "Telefono vacio"
    digits = re.sub(r"[^0-9+]", "", phone)
    if len(digits) < 8 or len(digits) > 15:
        return False, "Telefono invalido"
    return True, ""
