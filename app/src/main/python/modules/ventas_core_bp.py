# -*- coding: utf-8 -*-
"""Blueprint: Ventas — registro, consulta, cierres, totales"""
from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
import uuid

ventas_core_bp = Blueprint('ventas_core', __name__)


@ventas_core_bp.route('/api/ventas/registrar', methods=['POST'])
def registrar_venta():
    """Registra una venta en la BD."""
    d = request.get_json(silent=True) or {}
    items = d.get('items', [])
    metodo_pago = d.get('metodo_pago', 'efectivo')
    vendedor = d.get('vendedor', 'desconocido')

    if not items:
        return jsonify({"ok": False, "error": "No hay productos"}), 400

    conn = None
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()

        venta_id = f"vta-{uuid.uuid4().hex[:8]}"
        fecha = datetime.now().isoformat()
        total = 0

        # Transaccion atomica: la venta entera se confirma o se revierte completa
        cursor.execute("BEGIN")

        for item in items:
            producto_id = item.get('id', f'prod-{uuid.uuid4().hex[:6]}')
            nombre = item.get('nombre', 'Producto')
            cantidad = float(item.get('cantidad', 1))
            precio = float(item.get('precio', 0))
            subtotal = cantidad * precio
            total += subtotal
            cursor.execute(
                "INSERT INTO historial_ventas "
                "(venta_id,producto_id,nombre,cantidad,precio_unit,total,"
                "metodo_pago,fecha,vendedor_id,vendedor_nombre) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (venta_id, producto_id, nombre, cantidad, precio, subtotal,
                 metodo_pago, fecha, vendedor, vendedor),
            )
            # Actualizar stock
            cursor.execute(
                "UPDATE inventario_general "
                "SET stock_actual = MAX(0, stock_actual - ?), actualizado = ? "
                "WHERE producto_id = ?",
                (cantidad, fecha, producto_id),
            )

        conn.commit()
        return jsonify({"ok": True, "venta_id": venta_id,
                        "total": round(total, 2), "items": len(items), "fecha": fecha})
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()


@ventas_core_bp.route('/api/ventas/hoy')
def ventas_hoy():
    """Ventas del día actual."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        hoy = date.today().isoformat()
        cursor.execute(
            "SELECT venta_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha "
            "FROM historial_ventas WHERE fecha LIKE ? ORDER BY fecha DESC",
            (f"{hoy}%",),
        )
        ventas = []
        total = 0
        for row in cursor.fetchall():
            ventas.append({
                "venta_id": row[0], "producto": row[1], "cantidad": row[2],
                "precio_unit": row[3], "total": row[4], "metodo_pago": row[5],
                "fecha": row[6],
            })
            total += row[4] or 0
        conn.close()
        return jsonify({"ok": True, "ventas": ventas,
                        "total": round(total, 2), "cantidad": len(ventas)})
    except Exception as e:
        return jsonify({"ok": True, "ventas": [], "total": 0})


@ventas_core_bp.route('/api/ventas/cierre', methods=['POST'])
def cierre_caja():
    """Cierre de caja del día."""
    d = request.get_json(silent=True) or {}
    fecha = d.get('fecha', date.today().isoformat())
    cerrado_por = d.get('cerrado_por', 'sistema')
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) FROM historial_ventas WHERE fecha LIKE ?",
            (f"{fecha}%",),
        )
        total_ventas, num_ventas = cursor.fetchone()
        cursor.execute(
            "INSERT OR REPLACE INTO cierres_caja "
            "(fecha,total_ventas,num_transacciones,cerrado_por) VALUES (?,?,?,?)",
            (fecha, total_ventas or 0, num_ventas, cerrado_por),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "fecha": fecha,
                        "total_ventas": total_ventas or 0, "num_transacciones": num_ventas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@ventas_core_bp.route('/api/ventas/cierres')
def listar_cierres():
    """Lista cierres de caja."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cierre_id,fecha,total_ventas,num_transacciones,"
            "efectivo,tarjeta,transferencia,cerrado_por,creado "
            "FROM cierres_caja ORDER BY fecha DESC LIMIT 30"
        )
        cierres = []
        for row in cursor.fetchall():
            cierres.append({
                "id": row[0], "fecha": row[1], "total": row[2],
                "transacciones": row[3], "efectivo": row[4], "tarjeta": row[5],
                "transferencia": row[6], "cerrado_por": row[7],
            })
        conn.close()
        return jsonify({"ok": True, "cierres": cierres})
    except Exception as e:
        return jsonify({"ok": True, "cierres": []})


@ventas_core_bp.route('/api/ventas/totales')
def totales_ventas():
    """Resumen de totales hoy/mes."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        hoy = date.today().isoformat()
        mes = hoy[:7]

        cursor.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) "
            "FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",))
        total_hoy, num_hoy = cursor.fetchone()

        cursor.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) "
            "FROM historial_ventas WHERE fecha LIKE ?", (f"{mes}%",))
        total_mes, num_mes = cursor.fetchone()

        conn.close()
        return jsonify({"ok": True,
                        "hoy": {"total": total_hoy or 0, "ventas": num_hoy},
                        "mes": {"total": total_mes or 0, "ventas": num_mes}})
    except Exception as e:
        return jsonify({"ok": True,
                        "hoy": {"total": 0, "ventas": 0},
                        "mes": {"total": 0, "ventas": 0}})
