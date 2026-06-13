# -*- coding: utf-8 -*-
"""Blueprint de internacionalización (i18n).

Sirve el diccionario de traducciones ES/EN al frontend.
"""
import os
import json
import logging
from flask import Blueprint, jsonify

i18n_bp = Blueprint('i18n_bp', __name__)
log = logging.getLogger(__name__)

# Path al diccionario (al lado de app.py)
_DICT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'i18n_dictionary.json'
)

# Cache en memoria (se carga 1 vez)
_DICT_CACHE = None


def _cargar_diccionario():
    """Carga el diccionario desde disco con cache."""
    global _DICT_CACHE
    if _DICT_CACHE is not None:
        return _DICT_CACHE
    try:
        with open(_DICT_PATH, 'r', encoding='utf-8') as f:
            _DICT_CACHE = json.load(f)
        log.info(f"i18n: diccionario cargado ({len(_DICT_CACHE.get('en', {}))} entradas)")
        return _DICT_CACHE
    except FileNotFoundError:
        log.warning(f"i18n: diccionario no encontrado en {_DICT_PATH}")
        return {"es": {}, "en": {}}
    except json.JSONDecodeError as e:
        log.error(f"i18n: error parseando diccionario: {e}")
        return {"es": {}, "en": {}}


@i18n_bp.route('/api/i18n/dict', methods=['GET'])
def get_dict():
    """Devuelve el diccionario completo ES/EN."""
    return jsonify(_cargar_diccionario())


@i18n_bp.route('/api/i18n/reload', methods=['POST'])
def reload_dict():
    """Fuerza recarga del diccionario (útil tras editar el JSON)."""
    global _DICT_CACHE
    _DICT_CACHE = None
    _cargar_diccionario()
    return jsonify({"ok": True, "msg": "Diccionario recargado"})
