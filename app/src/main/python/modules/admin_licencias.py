from flask import request
from decorators import login_required, admin_required
from modules.admin_helpers import admin_bp, request, jsonify, requiere_login, requiere_rol, usuario_actual, crear_licencia, listar_licencias, verificar_licencia_activa, desactivar_licencia, _sb
# ── Licencias (sistema DB original) ──────────────────────────
@login_required
@admin_required
@admin_bp.route("/api/licencias", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_licencias():
    u = usuario_actual()
    admin_filtro = request.args.get("admin_id")
    licencias = listar_licencias(u["usuario_id"], admin_filtro)
    return jsonify({"licencias": licencias, "total": len(licencias)})

@login_required
@admin_required
@admin_bp.route("/api/licencias/crear", methods=["POST"])
@requiere_rol("desarrollador")
def api_crear_licencia():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    tipo_dias = {"diaria":1,"mensual":30,"anual":365,"ilimitada":99999}
    tipo = datos.get("tipo", "anual")
    dias = datos.get("dias") or tipo_dias.get(tipo, 365)
    resultado = crear_licencia(
        admin_id=datos.get("admin_id",""), tipo=tipo, dias=int(dias),
        notas=datos.get("notas",""), dev_id=u["usuario_id"],
        cliente_id=datos.get("cliente_id",""),
        clave_activacion=datos.get("clave_activacion","")
    )
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@login_required
@admin_required
@admin_bp.route("/api/licencias/<licencia_id>", methods=["DELETE"])
@requiere_rol("desarrollador")
def api_desactivar_licencia(licencia_id):
    u = usuario_actual()
    resultado = desactivar_licencia(licencia_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@login_required
@admin_required
@admin_bp.route("/api/licencias/verificar/<admin_id>", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_verificar_licencia(admin_id):
    lic = verificar_licencia_activa(admin_id)
    return jsonify({"tiene_licencia": lic is not None, "licencia": lic})
