from flask import Blueprint, request, jsonify, session
from decorators import login_required, requiere_rol, usuario_actual
from database import (registrar_entrada_producto, obtener_inventario_general, obtener_historial_entradas,
                      asignar_inventario_diario, obtener_inventario_diario, actualizar_vendido_diario,
                      importar_catalogo_a_inventario, eliminar_producto_inventario_general,
                      sincronizar_estado_completo, cargar_stock_masivo, limpiar_tablas_completo,
                      reconstruir_desde_productos, limpiar_inventarios_diarios, obtener_conexion)
import supabase_sync as _sb
from datetime import datetime

inv_bp = Blueprint('inventory', __name__, url_prefix='/api')




@inv_bp.route("/inventario/entrada", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_entrada_producto():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = registrar_entrada_producto(datos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@inv_bp.route("/inventario/general", methods=["GET"])
@requiere_rol("administrador", "desarrollador", "supervisor", "vendedor")
def api_inventario_general():
    try:
        u = usuario_actual()
        return jsonify({"inventario": obtener_inventario_general(u["usuario_id"])})
    except Exception as e:
        return jsonify({"error": f"Error inventario general: {str(e)}"}), 500

@inv_bp.route("/inventario/importar-catalogo", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_importar_catalogo():
    u = usuario_actual()
    r = importar_catalogo_a_inventario(u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)

@inv_bp.route("/inventario/general/eliminar", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_eliminar_inventario_general():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    r = eliminar_producto_inventario_general(datos.get("producto_id",""), u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)

@inv_bp.route("/catalogo/sync-desde-inventario", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_sync_desde_inventario():
    prods = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": prods, "total": len(prods)})

@inv_bp.route("/sincronizar-completo", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_sincronizar_completo():
    try:
        u = usuario_actual()
        r = sincronizar_estado_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inv_bp.route("/stock/masivo", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_stock_masivo():
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        items = datos.get("items", [])
        r = cargar_stock_masivo(u["usuario_id"], items)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inv_bp.route("/limpiar-tablas", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_limpiar_tablas():
    try:
        u = usuario_actual()
        r = limpiar_tablas_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inv_bp.route("/reconstruir-desde-productos", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_reconstruir_desde_productos():
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        productos = datos.get("productos", [])
        r = reconstruir_desde_productos(u["usuario_id"], productos)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inv_bp.route("/inventario/entradas", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def api_historial_entradas():
    u = usuario_actual()
    producto_id = request.args.get("producto_id")
    return jsonify({"entradas": obtener_historial_entradas(u["usuario_id"], producto_id)})

@inv_bp.route("/inventario/asignar-diario", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_asignar_inventario():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id", "")
    productos = datos.get("productos", [])
    resultado = asignar_inventario_diario(vendedor_id, productos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@inv_bp.route("/inventario/diario/<vendedor_id>", methods=["GET"])
@login_required
def api_inventario_diario(vendedor_id):
    try:
        fecha = request.args.get("fecha")
        return jsonify({"inventario": obtener_inventario_diario(vendedor_id, fecha)})
    except Exception as e:
        return jsonify({"error": f"Error inventario diario: {str(e)}"}), 500

@inv_bp.route("/inventario/diario/conteo", methods=["POST"])
@login_required
def api_conteo_vendedor():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id", u["usuario_id"])
    producto_id = datos.get("producto_id", "")
    cant_final = float(datos.get("cant_final", 0))
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Solo puedes registrar tu propio conteo"}), 403
    conn = obtener_conexion()
    try:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        conn.execute("UPDATE inventario_diario SET cant_vendida = ? WHERE vendedor_id = ? AND producto_id = ? AND fecha = ?",
                     (cant_final, vendedor_id, producto_id, fecha_hoy))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Conteo guardado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/inventario/diario/cierre", methods=["POST"])
@login_required
def api_cierre_vendedor():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id", u["usuario_id"])
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    total_ventas = float(datos.get("total_ventas", 0))
    total_costo = float(datos.get("total_costo", 0))
    ganancia = float(datos.get("ganancia_neta", 0))
    items = datos.get("items", [])
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Solo puedes cerrar tu propio día"}), 403
    conn = obtener_conexion()
    import json as _json
    from datetime import timedelta
    try:
        conn.execute("""
            INSERT INTO cierres_diario (vendedor_id, fecha, total_ventas, total_costo, ganancia_neta, items_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vendedor_id, fecha) DO UPDATE SET
                total_ventas = excluded.total_ventas, total_costo = excluded.total_costo,
                ganancia_neta = excluded.ganancia_neta, items_json = excluded.items_json
        """, (vendedor_id, fecha, total_ventas, total_costo, ganancia, _json.dumps(items, ensure_ascii=False)))
        fecha_sig = (datetime.strptime(fecha, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        for item in items:
            pid = item.get("producto_id", "")
            nombre = item.get("nombre", pid)
            cant_final = float(item.get("cant_final") or item.get("cant_asignada", 0))
            pv = float(item.get("precio_venta", 0))
            pc = float(item.get("precio_costo", 0))
            if not pid: continue
            conn.execute("""
                INSERT INTO inventario_diario (fecha, vendedor_id, producto_id, nombre, cant_asignada, cant_vendida, cant_final, precio_venta, precio_costo)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                ON CONFLICT(fecha, vendedor_id, producto_id) DO UPDATE SET cant_asignada = excluded.cant_asignada, precio_venta = excluded.precio_venta, precio_costo = excluded.precio_costo
            """, (fecha_sig, vendedor_id, pid, nombre, cant_final, cant_final, pv, pc))
        for item in items:
            pid = item.get("producto_id", "")
            cant_final = float(item.get("cant_final") or 0)
            if not pid or cant_final <= 0: continue
            conn.execute("UPDATE inventario_general SET stock_actual = stock_actual + ?, actualizado = datetime('now','localtime') WHERE producto_id = ?", (cant_final, pid))
        conn.commit()
        return jsonify({"ok": True, "mensaje": f"Día {fecha} cerrado"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/inventario/cierre-admin", methods=["POST"])
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
            conn.execute("UPDATE inventario_general SET stock_actual = ?, actualizado = datetime('now','localtime') WHERE producto_id = ?", (max(0, cant_final), pid))
            if conn.execute("SELECT changes()").fetchone()[0] > 0: actualizados += 1
        conn.commit()
        return jsonify({"ok": True, "actualizados": actualizados, "mensaje": f"Almacén actualizado: {actualizados} productos"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/inventario/diario/limpiar", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_limpiar_inventarios():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id")
    fecha = datos.get("fecha")
    resultado = limpiar_inventarios_diarios(u["usuario_id"], vendedor_id, fecha)
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@inv_bp.route("/inventario/diario/historial/<vendedor_id>", methods=["GET"])
@login_required
def api_historial_cierres(vendedor_id):
    u = usuario_actual()
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Sin permisos"}), 403
    conn = obtener_conexion()
    try:
        rows = conn.execute("SELECT fecha, total_ventas, total_costo, ganancia_neta, creado_en FROM cierres_diario WHERE vendedor_id = ? ORDER BY fecha DESC LIMIT 90", (vendedor_id,)).fetchall()
        return jsonify({"historial": [dict(r) for r in rows]})
    finally:
        conn.close()
