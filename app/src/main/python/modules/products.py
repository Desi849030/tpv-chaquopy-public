from auth_decorator import login_required
from flask import Blueprint, request, jsonify, session
from functools import wraps
from database import obtener_productos_catalogo, sincronizar_productos_catalogo, sincronizar_estado_completo

prod_bp = Blueprint('products', __name__, url_prefix='/api')




@prod_bp.route("/catalogo", methods=["GET"])
@login_required
def api_get_catalogo():
    productos = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": productos, "total": len(productos)})

@prod_bp.route("/catalogo/sync", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_sync_catalogo():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    productos = datos.get("productos", [])
    resultado = sincronizar_productos_catalogo(productos, u["usuario_id"])
    if resultado.get("ok"):
        sincronizar_estado_completo(u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)
