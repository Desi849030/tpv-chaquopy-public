import unicodedata, re

from .helpers import _levenshtein
from .helpers import _sin_tildes
from .helpers import buscar_sinonimos
from .helpers import definir_termino
from .helpers import corregir
from .helpers import _dev_check
from .helpers import _DEFINICIONES
from .helpers import *


@diccionario_bp.route("/api/diccionario/sinonimos", methods=["GET"])
def api_sinonimos():
    if not _dev_check():
        return jsonify({"error": "sin permisos"}), 403
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "parametro q requerido"}), 400
    results = buscar_sinonimos(q)
    return jsonify({"palabra": q, "sinonimos": results, "total": len(results)})


@diccionario_bp.route("/api/diccionario/definicion")

@diccionario_bp.route("/api/diccionario/definicion", methods=["GET"])
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

@diccionario_bp.route("/api/diccionario/corregir", methods=["GET"])
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

