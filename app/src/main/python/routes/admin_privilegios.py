from routes.admin_helpers import admin_bp, request, jsonify, requiere_login, requiere_rol, agregar_log, _obtener_privilegios_rol, _guardar_privilegios_rol, _MODULOS_DISPONIBLES, _PRIVILEGIOS_DEFAULT
@admin_bp.route("/api/privilegios/<rol>", methods=["GET"])
@requiere_rol("desarrollador","administrador","supervisor")
def api_get_privilegios(rol):
    u = usuario_actual()
    if rol == "desarrollador" and u["rol"] != "desarrollador":
        return jsonify({"error": "Sin permisos"}), 403
    p = _obtener_privilegios_rol(rol)
    if p is None:
        p = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    return jsonify({"ok":True,"rol":rol,"privilegios":p,"modulos":_MODULOS_DISPONIBLES,"default":_PRIVILEGIOS_DEFAULT.get(rol,{})})

@admin_bp.route("/api/privilegios/<rol>", methods=["PUT"])
@requiere_rol("desarrollador","administrador","supervisor")
def api_set_privilegios(rol):
    u = usuario_actual()
    d = request.get_json(force=True, silent=True) or {}
    n = d.get("privilegios", {})
    if not isinstance(n, dict): return jsonify({"error": "Formato invalido"}), 400
    if rol == "desarrollador" and u["rol"] != "desarrollador": return jsonify({"error": "Sin permisos"}), 403
    if u["rol"] == "administrador":
        for m in ("debug","privilegios","licencias"):
            if n.get(m): n[m] = False
    if rol == "desarrollador": n = {m: True for m in _MODULOS_DISPONIBLES}
    if _guardar_privilegios_rol(rol, n):
        return jsonify({"ok": True, "mensaje": f"Privilegios de '{rol}' actualizados"})
    return jsonify({"error": "No se pudieron guardar"}), 500

@admin_bp.route("/api/privilegios/<rol>/restablecer", methods=["POST"])
@requiere_rol("desarrollador","administrador","supervisor")
def api_reset_privilegios(rol):
    u = usuario_actual()
    if rol == "desarrollador" and u["rol"] != "desarrollador": return jsonify({"error": "Sin permisos"}), 403
    d = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    if _guardar_privilegios_rol(rol, d):
        return jsonify({"ok":True,"mensaje":f"Privilegios de '{rol}' restablecidos","privilegios":d})
    return jsonify({"error": "No se pudieron guardar"}), 500
