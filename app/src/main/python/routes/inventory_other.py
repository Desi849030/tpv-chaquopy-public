from routes.inventory_bp import inv_bp
from routes.inventory_helpers import *

@inv_bp.route("/api/inventario/importar-catalogo", methods=["POST"])
# @requiere_rol desactivado para pruebas
def api_importar_catalogo():
    u = usuario_actual()
    r = importar_catalogo_a_inventario(u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)

@inv_bp.route("/api/inventario/cierre-admin", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_cierre_admin():
    datos = request.get_json(force=True, silent=True) or {}
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    items = datos.get("items", [])
    conn = obtener_conexion()
    try:
        actualizados = 0
        for item in items:
            pid = item.get("producto_id", "")
            cant_final = float(item.get("cant_final") or 0)
            if not pid: continue
            conn.execute("""
                UPDATE inventario_general SET stock_actual=?, actualizado=datetime('now','localtime')
                WHERE producto_id=?
            """, (max(0, cant_final), pid))
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                actualizados += 1
        conn.commit()
        agregar_log(f"Cierre admin {fecha}: {actualizados} productos actualizados en almacen", "info")
        return jsonify({"ok": True, "actualizados": actualizados,
                        "mensaje": f"Almacen actualizado: {actualizados} productos"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/api/importar-validado", methods=["POST"])
# @requiere_rol desactivado para pruebas
def api_importar_validado():
    """Pipeline v4: Dry Run + Transaccion Atomica."""
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        productos = datos.get("productos", [])
        ejecutar = datos.get("ejecutar", False)
        resultado = validar_productos_lote(productos)
        if not resultado.valido:
            return jsonify({"ok": False, "fase": "validacion", "validacion": resultado.to_dict()}), 400
        if not ejecutar:
            return jsonify({"ok": True, "fase": "validacion_ok", "validacion": resultado.to_dict(),
                "mensaje": f"Validacion exitosa: {len(resultado.productos_validos)} productos listos."})
        r = importar_productos_validados(u["usuario_id"], resultado.productos_validos)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
