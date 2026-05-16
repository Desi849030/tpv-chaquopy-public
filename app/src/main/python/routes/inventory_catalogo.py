from routes.inventory_bp import inv_bp
from routes.inventory_helpers import *

@inv_bp.route("/api/catalogo", methods=["GET"])
@requiere_login
def api_get_catalogo():
    productos = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": productos, "total": len(productos)})

@inv_bp.route("/api/catalogo/sync", methods=["POST"])
# @requiere_rol("administrador", "desarrollador")
def api_sync_catalogo():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    productos = datos.get("productos", [])
    resultado = sincronizar_productos_catalogo(productos, u["usuario_id"])
    if resultado.get("ok"):
        sincronizar_estado_completo(u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@inv_bp.route("/api/catalogo/sync-desde-inventario", methods=["POST"])
# @requiere_rol("administrador","desarrollador")
def api_sync_desde_inventario():
    prods = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": prods, "total": len(prods)})

# ══════════════════════════════════════════════════════════════
#  SINCRONIZACIÓN COMPLETA
# ══════════════════════════════════════════════════════════════

@inv_bp.route("/api/sincronizar-completo", methods=["POST"])
# @requiere_rol("administrador","desarrollador")
def api_sincronizar_completo():
    try:
        u = usuario_actual()
        r = sincronizar_estado_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

