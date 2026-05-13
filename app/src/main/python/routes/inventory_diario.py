from routes.inventory_bp import inv_bp
from routes.inventory_helpers import *

@inv_bp.route("/api/inventario/asignar-diario", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_asignar_inventario():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    vendedor_id = datos.get("vendedor_id","")
    productos = datos.get("productos", [])
    resultado = asignar_inventario_diario(vendedor_id, productos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@inv_bp.route("/api/inventario/diario/<vendedor_id>", methods=["GET"])
@requiere_login
def api_inventario_diario(vendedor_id):
    try:
        fecha = request.args.get("fecha")
        return jsonify({"inventario": obtener_inventario_diario(vendedor_id, fecha)})
    except Exception as e:
        return jsonify({"error": f"Error inventario diario: {str(e)}"}), 500

@inv_bp.route("/api/inventario/diario/conteo", methods=["POST"])
@requiere_login
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
        conn.execute("""
            UPDATE inventario_diario SET cant_vendida = ?
            WHERE vendedor_id = ? AND producto_id = ? AND fecha = ?
        """, (cant_final, vendedor_id, producto_id, fecha_hoy))
        conn.commit()
        agregar_log(f"Conteo final: {cant_final} de {producto_id} por {u['usuario_id']}", "info")
        return jsonify({"ok": True, "mensaje": "Conteo guardado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/api/inventario/diario/cierre", methods=["POST"])
@requiere_login
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
        return jsonify({"error": "Solo puedes cerrar tu propio dia"}), 403
    conn = obtener_conexion()
    try:
        _cierre_existia = conn.execute(
            "SELECT 1 FROM cierres_diario WHERE vendedor_id=? AND fecha=?",
            (vendedor_id, fecha)
        ).fetchone()
        conn.execute("""
            INSERT INTO cierres_diario
            (vendedor_id, fecha, total_ventas, total_costo, ganancia_neta, items_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vendedor_id, fecha) DO UPDATE SET
                total_ventas=excluded.total_ventas,
                total_costo=excluded.total_costo,
                ganancia_neta=excluded.ganancia_neta,
                items_json=excluded.items_json,
                creado_en=datetime('now','localtime')
        """, (vendedor_id, fecha, total_ventas, total_costo, ganancia,
              _json.dumps(items, ensure_ascii=False)))
        fecha_sig = (datetime.strptime(fecha, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        for item in items:
            pid = item.get("producto_id","")
            nombre = item.get("nombre", pid)
            cant_final = float(item.get("cant_final") or item.get("cant_asignada", 0))
            pv = float(item.get("precio_venta", 0))
            pc = float(item.get("precio_costo", 0))
            if not pid: continue
            conn.execute("""
                INSERT INTO inventario_diario
                (fecha, vendedor_id, producto_id, nombre, cant_asignada, cant_vendida, cant_final, precio_venta, precio_costo)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                ON CONFLICT(fecha, vendedor_id, producto_id) DO UPDATE SET
                    cant_asignada=excluded.cant_asignada,
                    precio_venta=excluded.precio_venta,
                    precio_costo=excluded.precio_costo
            """, (fecha_sig, vendedor_id, pid, nombre, cant_final, cant_final, pv, pc))
        if not _cierre_existia:
            for item in items:
                pid = item.get("producto_id", "")
                cant_final = float(item.get("cant_final") or 0)
                if not pid or cant_final <= 0: continue
                conn.execute("""
                    UPDATE inventario_general SET stock_actual=stock_actual+?, actualizado=datetime('now','localtime')
                    WHERE producto_id=?
                """, (cant_final, pid))
        conn.commit()
        agregar_log(f"Cierre {fecha} vendedor {vendedor_id}: ventas=${total_ventas:.2f}", "info")
        return jsonify({"ok": True, "mensaje": f"Dia {fecha} cerrado. Sobrante devuelto al almacen."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inv_bp.route("/api/inventario/diario/historial/<vendedor_id>", methods=["GET"])
@requiere_login
def api_historial_cierres(vendedor_id):
    u = usuario_actual()
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Sin permisos"}), 403
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT fecha, total_ventas, total_costo, ganancia_neta, creado_en
            FROM cierres_diario WHERE vendedor_id=?
            ORDER BY fecha DESC LIMIT 90
        """, (vendedor_id,)).fetchall()
        return jsonify({"historial": [dict(r) for r in rows]})
    finally:
        conn.close()


