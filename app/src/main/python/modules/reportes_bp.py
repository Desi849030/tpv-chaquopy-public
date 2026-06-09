# -*- coding: utf-8 -*-
"""Blueprint: Reportes y exportación"""
from flask import Blueprint, request, jsonify
from datetime import date, timedelta

reportes_bp = Blueprint('reportes', __name__)


@reportes_bp.route('/api/reportes/ventas', methods=['GET'])
def reporte_ventas():
    """Reporte de ventas con filtros por fecha."""
    desde = request.args.get('desde', date.today().isoformat())
    hasta = request.args.get('hasta', date.today().isoformat())
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT venta_id,nombre,cantidad,precio_unit,total,metodo_pago,fecha "
            "FROM historial_ventas WHERE fecha >= ? AND fecha <= ? "
            "ORDER BY fecha DESC LIMIT 200",
            (desde, hasta),
        )
        ventas = []
        total = 0
        for row in cursor.fetchall():
            ventas.append({
                "id": row[0], "producto": row[1], "cantidad": row[2],
                "precio": row[3], "total": row[4], "metodo": row[5], "fecha": row[6],
            })
            total += row[4] or 0
        conn.close()
        return jsonify({"ok": True, "ventas": ventas,
                        "total": round(total, 2), "cantidad": len(ventas)})
    except Exception as e:
        return jsonify({"ok": True, "ventas": [], "total": 0})


@reportes_bp.route('/api/reportes/exportar', methods=['GET'])
def exportar_csv():
    """Exporta ventas a CSV."""
    desde = request.args.get('desde', date.today().isoformat())
    hasta = request.args.get('hasta', date.today().isoformat())
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT fecha,venta_id,nombre,cantidad,precio_unit,total,metodo_pago "
            "FROM historial_ventas WHERE fecha >= ? AND fecha <= ? ORDER BY fecha DESC",
            (desde, hasta),
        )
        csv = "Fecha,Venta ID,Producto,Cantidad,Precio Unit,Total,Método Pago\n"
        for row in cursor.fetchall():
            csv += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}\n"
        conn.close()
        return csv, 200, {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': f'attachment; filename=ventas_{desde}_{hasta}.csv',
        }
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@reportes_bp.route('/api/reportes/resumen')
def reporte_resumen():
    """Resumen general para dashboard."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        hoy = date.today()

        cursor.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) "
            "FROM historial_ventas WHERE fecha LIKE ?",
            (f"{hoy.isoformat()}%",))
        ventas_hoy, num_hoy = cursor.fetchone()

        ayer = hoy - timedelta(days=1)
        cursor.execute(
            "SELECT COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?",
            (f"{ayer.isoformat()}%",))
        ventas_ayer = cursor.fetchone()[0] or 0

        mes = hoy.isoformat()[:7]
        cursor.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) "
            "FROM historial_ventas WHERE fecha LIKE ?",
            (f"{mes}%",))
        ventas_mes, num_mes = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        num_prod = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= 5")
        stock_bajo = cursor.fetchone()[0]

        conn.close()
        return jsonify({"ok": True, "resumen": {
            "ventas_hoy": ventas_hoy or 0, "transacciones_hoy": num_hoy,
            "ventas_ayer": ventas_ayer, "ventas_mes": ventas_mes or 0,
            "transacciones_mes": num_mes, "productos": num_prod,
            "stock_bajo": stock_bajo,
        }})
    except Exception as e:
        return jsonify({"ok": True, "resumen": {"ventas_hoy": 0}})


@reportes_bp.route('/api/metrics')
def metrics():
    """Métricas rápidas para el dashboard."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        hoy = date.today()
        mes = hoy.strftime('%Y-%m')

        c.execute(
            "SELECT COALESCE(SUM(total),0), COUNT(*) "
            "FROM historial_ventas WHERE fecha LIKE ?",
            (f"{hoy.isoformat()}%",))
        r = c.fetchone()
        ingresos_hoy = r[0] or 0
        ventas_hoy = r[1]

        c.execute(
            "SELECT COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?",
            (f"{mes}%",))
        ingresos_mes = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        num_productos = c.fetchone()[0]

        c.execute(
            "SELECT nombre, SUM(cantidad) FROM historial_ventas "
            "WHERE fecha LIKE ? GROUP BY nombre ORDER BY SUM(cantidad) DESC LIMIT 1",
            (f"{hoy.isoformat()}%",))
        top = c.fetchone()
        top_producto = top[0] if top else "N/A"

        conn.close()
        return jsonify({
            "ok": True, "ingresos_hoy": ingresos_hoy,
            "ventas_hoy": ventas_hoy, "ingresos_mes": ingresos_mes,
            "num_productos": num_productos, "top_producto": top_producto,
            "ganancia_estimada": round(ingresos_hoy * 0.30, 2),
        })
    except Exception as e:
        return jsonify({"ok": True, "ingresos_hoy": 0, "ventas_hoy": 0})
