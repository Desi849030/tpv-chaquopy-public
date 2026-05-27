from auth_decorator import login_required
from auth_decorator import login_required
"""i18n_routes.py - API de diccionario i18n con aprendizaje"""
import json, os

DICT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n_dictionary.json")

def _load():
    try:
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"es": {}, "en": {}}

def _save(d):
    try:
        with open(DICT_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        pass

from flask import Blueprint, jsonify, request

i18n_bp = Blueprint("i18n", __name__)

@login_required
@i18n_bp.route("/api/i18n/dict")
def get_dict():
    d = _load()
    return jsonify({"es": d.get("es", {}), "en": d.get("en", {})})

@login_required
@i18n_bp.route("/api/i18n/translate", methods=["POST"])
def translate():
    data = request.get_json(force=True) or {}
    text = data.get("text", "").strip()
    to_lang = data.get("lang", "en")
    if not text:
        return jsonify({"translation": text})
    d = _load()
    other = "en" if to_lang == "es" else "es"
    found = d.get(other, {}).get(text)
    if found:
        return jsonify({"translation": found, "learned": False})
    return jsonify({"translation": text, "learned": False})

@login_required
@i18n_bp.route("/api/i18n/learn", methods=["POST"])
def learn():
    data = request.get_json(force=True) or {}
    es = data.get("es", "").strip()
    en = data.get("en", "").strip()
    if not es or not en:
        return jsonify({"ok": False, "error": "Se necesitan es y en"})
    d = _load()
    d.setdefault("es", {})[es] = es
    d.setdefault("en", {})[es] = en
    d["en"][en] = en
    d["es"][en] = es
    _save(d)
    return jsonify({"ok": True, "total_es": len(d.get("es", {})), "total_en": len(d.get("en", {}))})
