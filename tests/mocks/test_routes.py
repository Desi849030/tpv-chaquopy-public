from flask import Blueprint, jsonify, request
test_bp = Blueprint("test_bp", __name__)
@test_bp.route("/api/auth/biometric", methods=["POST"])
def bio():
    d = request.get_json() or {}
    if not d.get("huella") or not d.get("usuario"): return jsonify({"ok": False, "error": "incompletos"}), 400
    if d["usuario"] == "admin" and d["huella"] == "huella_valida": return jsonify({"ok": True, "token": "test_token"}), 200
    return jsonify({"ok": False, "error": "invalida"}), 401
@test_bp.route("/api/licencias", methods=["GET"])
@test_bp.route("/api/licencias/verificar", methods=["POST"])
@test_bp.route("/api/licencia/verificar", methods=["POST", "GET"])
def lic(): return jsonify({"ok": True, "valida": True, "estado": "activa", "licencias": [{"id":1,"estado":"activa"}]}), 200
