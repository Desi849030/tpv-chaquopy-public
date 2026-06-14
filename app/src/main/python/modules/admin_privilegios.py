"""Rutas de privilegios por rol — GET/PUT/RESET"""
from modules.admin_helpers import (
    admin_bp, request, jsonify, requiere_login, requiere_rol,
    usuario_actual, agregar_log, _obtener_privilegios_rol,
    _guardar_privilegios_rol, _MODULOS_DISPONIBLES, _PRIVILEGIOS_DEFAULT
)


@admin_bp.route("/api/privilegios/<rol>", methods=["GET"])
@requiere_login
def api_get_privilegios(rol):
    u = usuario_actual()
    mi_rol = u.get("rol", "")
    # Solo admin, desarrollador y supervisor pueden ver privilegios
    if mi_rol not in ("desarrollador", "administrador", "supervisor"):
        return jsonify({"error": "Sin permisos"}), 403
    if rol == "desarrollador" and mi_rol != "desarrollador":
        return jsonify({"error": "Sin permisos"}), 403
    p = _obtener_privilegios_rol(rol)
    if p is None:
        p = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    return jsonify({
        "ok": True, "rol": rol, "privilegios": p,
        "modulos": _MODULOS_DISPONIBLES,
        "default": _PRIVILEGIOS_DEFAULT.get(rol, {}),
    })


@admin_bp.route("/api/privilegios/<rol>", methods=["PUT"])
@requiere_login
def api_set_privilegios(rol):
    u = usuario_actual()
    mi_rol = u.get("rol", "")
    if mi_rol not in ("desarrollador", "administrador"):
        return jsonify({"error": "Sin permisos"}), 403
    d = request.get_json(force=True, silent=True) or {}
    n = d.get("privilegios", {})
    if not isinstance(n, dict):
        return jsonify({"error": "Formato inválido"}), 400
    if rol == "desarrollador" and mi_rol != "desarrollador":
        return jsonify({"error": "Sin permisos"}), 403
    # Admin no puede dar debug/privilegios/licencias
    if mi_rol == "administrador":
        for m in ("debug", "privilegios", "licencias"):
            if n.get(m):
                n[m] = False
    # Desarrollador siempre tiene todo
    if rol == "desarrollador":
        n = {m: True for m in _MODULOS_DISPONIBLES}
    if _guardar_privilegios_rol(rol, n):
        return jsonify({"ok": True, "mensaje": f"Privilegios de '{rol}' actualizados"})
    return jsonify({"error": "No se pudieron guardar"}), 500


@admin_bp.route("/api/privilegios/<rol>/restablecer", methods=["POST"])
@requiere_login
def api_reset_privilegios(rol):
    u = usuario_actual()
    mi_rol = u.get("rol", "")
    if mi_rol not in ("desarrollador", "administrador"):
        return jsonify({"error": "Sin permisos"}), 403
    if rol == "desarrollador" and mi_rol != "desarrollador":
        return jsonify({"error": "Sin permisos"}), 403
    d = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    if _guardar_privilegios_rol(rol, d):
        return jsonify({"ok": True, "mensaje": f"Privilegios de '{rol}' restablecidos", "privilegios": d})
    return jsonify({"error": "No se pudieron guardar"}), 500
