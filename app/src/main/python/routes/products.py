from flask import Blueprint, request, jsonify, session
from functools import wraps
from database import obtener_productos_catalogo, sincronizar_productos_catalogo, sincronizar_estado_completo

prod_bp = Blueprint('products', __name__, url_prefix='/api')

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            u = session.get("usuario")
            if not u or u.get("rol") not in roles:
                return jsonify({"error": "Permiso denegado"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def usuario_actual():
    return session.get("usuario", {})

@prod_bp.route("/catalogo", methods=["GET"])
@requiere_login
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
