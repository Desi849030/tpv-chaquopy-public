from flask import request
from auth_decorator import login_required
from modules.inventory_bp import inv_bp
from modules.inventory_helpers import *

@login_required
@inv_bp.route("/api/inventario/entrada", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_entrada_producto():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = registrar_entrada_producto(datos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@login_required
@inv_bp.route("/api/inventario/general", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def api_inventario_general():
    try:
        u = usuario_actual()
        return jsonify({"inventario": obtener_inventario_general(u["usuario_id"])})
    except Exception as e:
        return jsonify({"error": f"Error inventario general: {str(e)}"}), 500

@login_required
@inv_bp.route("/api/inventario/general/eliminar", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_eliminar_inventario_general():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    r = eliminar_producto_inventario_general(datos.get("producto_id",""), u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)

@login_required
@inv_bp.route("/api/inventario/entradas", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def api_historial_entradas():
    u = usuario_actual()
    producto_id = request.args.get("producto_id")
    return jsonify({"entradas": obtener_historial_entradas(u["usuario_id"], producto_id)})

# ══════════════════════════════════════════════════════════════
#  CATÁLOGO DE PRODUCTOS
# ══════════════════════════════════════════════════════════════

@login_required
@inv_bp.route("/api/stock/masivo", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_stock_masivo():
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        items = datos.get("items", [])
        r = cargar_stock_masivo(u["usuario_id"], items)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@login_required
@inv_bp.route("/api/limpiar-tablas", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_limpiar_tablas():
    try:
        u = usuario_actual()
        r = limpiar_tablas_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@login_required
@inv_bp.route("/api/reconstruir-desde-productos", methods=["POST"])
@requiere_rol("administrador","desarrollador","vendedor")
def api_reconstruir_desde_productos():
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        productos = datos.get("productos", [])
        r = reconstruir_desde_productos(u["usuario_id"], productos)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  INVENTARIO DIARIO
# ══════════════════════════════════════════════════════════════

@login_required
@inv_bp.route("/api/inventario/diario/limpiar", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_limpiar_inventarios():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id")
    fecha = datos.get("fecha")
    resultado = limpiar_inventarios_diarios(u["usuario_id"], vendedor_id, fecha)
    return jsonify(resultado), (200 if resultado["ok"] else 400)

