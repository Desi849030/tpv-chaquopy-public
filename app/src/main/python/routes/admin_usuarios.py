from auth_decorator import login_required, admin_required
from routes.admin_helpers import admin_bp, request, jsonify, requiere_login, requiere_rol, usuario_actual, crear_usuario, listar_usuarios, desactivar_usuario, resetear_password, sincronizar_usuario_nuevo, _sb

# ── Usuarios ─────────────────────────────────────────────────
@login_required
@admin_required
@admin_bp.route("/api/usuarios/crear", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_crear_usuario():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = crear_usuario(datos, creado_por_rol=u["rol"], creado_por_id=u["usuario_id"])
    if resultado.get("ok") and resultado.get("usuario_id") and _sb.SUPABASE_OK:
        threading.Thread(target=sincronizar_usuario_nuevo, args=(resultado["usuario_id"],), daemon=True).start()
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@login_required
@admin_required
@admin_bp.route("/api/usuarios", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_usuarios():
    try:
        u = usuario_actual()
        usuarios = listar_usuarios(u["rol"], u["usuario_id"])
        return jsonify({"usuarios": usuarios, "total": len(usuarios)})
    except Exception as e:
        return jsonify({"error": f"Error al listar usuarios: {str(e)}"}), 500

@login_required
@admin_required
@admin_bp.route("/api/usuarios/<usuario_id>", methods=["DELETE"])
@requiere_rol("desarrollador","administrador")
def api_desactivar_usuario(usuario_id):
    u = usuario_actual()
    resultado = desactivar_usuario(usuario_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@login_required
@admin_required
@admin_bp.route("/api/usuarios/<usuario_id>/reset-password", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_reset_password(usuario_id):
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = resetear_password(usuario_id, datos.get("password_nueva",""), u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

