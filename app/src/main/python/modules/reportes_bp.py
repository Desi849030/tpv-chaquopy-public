# -*- coding: utf-8 -*-
"""Blueprint: Reportes y exportación."""
from flask import Blueprint, request, jsonify
from datetime import date, timedelta

reportes_bp = Blueprint('reportes', __name__)


def _tabla_existe(conn, nombre: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (nombre,),
    ).fetchone()
    return bool(row)


def _usar_ventas_atomicas(conn) -> bool:
    if not _tabla_existe(conn, "ventas_cabecera"):
        return False
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM ventas_cabecera").fetchone()
        return bool(row and int(row[0]) > 0)
    except Exception:
        return False


def _totales_periodo(conn, patron_fecha: str):
    if _usar_ventas_atomicas(conn):
        row = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS total, COUNT(*) AS num FROM ventas_cabecera WHERE fecha LIKE ?",
            (patron_fecha,),
        ).fetchone()
        return float(row[0] or 0), int(row[1] or 0)

    row = conn.execute(
        """
        SELECT COALESCE(SUM(total_venta),0) AS total, COUNT(*) AS num
        FROM (
            SELECT venta_id, SUM(total) AS total_venta
            FROM historial_ventas
            WHERE fecha LIKE ?
            GROUP BY venta_id
        )
        """,
        (patron_fecha,),
    ).fetchone()
    return float(row[0] or 0), int(row[1] or 0)


@reportes_bp.route('/api/reportes/ventas', methods=['GET'])
def reporte_ventas():
    """Reporte de ventas con filtros por fecha."""
    desde = request.args.get('desde', date.today().isoformat())
    hasta = request.args.get('hasta', date.today().isoformat())
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()

        if _usar_ventas_atomicas(conn):
            cursor.execute(
                """
                SELECT vc.venta_id,
                       COALESCE(GROUP_CONCAT(vd.nombre, ' | '), '(sin detalle)') AS producto,
                       COALESCE(SUM(vd.cantidad),0) AS cantidad,
                       CASE WHEN COALESCE(SUM(vd.cantidad),0) > 0
                            THEN ROUND(vc.total / SUM(vd.cantidad), 2)
                            ELSE vc.total END AS precio_unit,
                       vc.total,
                       vc.metodo_pago,
                       vc.fecha
                FROM ventas_cabecera vc
                LEFT JOIN ventas_detalle vd ON vd.venta_id = vc.venta_id
                WHERE vc.fecha >= ? AND vc.fecha <= ?
                GROUP BY vc.venta_id, vc.total, vc.metodo_pago, vc.fecha
                ORDER BY vc.fecha DESC LIMIT 200
                """,
                (desde, hasta + " 23:59:59"),
            )
        else:
            cursor.execute(
                "SELECT venta_id,nombre,cantidad,precio_unit,total,metodo_pago,fecha "
                "FROM historial_ventas WHERE fecha >= ? AND fecha <= ? "
                "ORDER BY fecha DESC LIMIT 200",
                (desde, hasta + " 23:59:59"),
            )

        ventas = []
        total = 0
        for row in cursor.fetchall():
            ventas.append({
                "id": row[0],
                "producto": row[1],
                "cantidad": row[2],
                "precio": row[3],
                "total": row[4],
                "metodo": row[5],
                "fecha": row[6],
            })
            total += row[4] or 0
        conn.close()
        return jsonify({"ok": True, "ventas": ventas,
                        "total": round(total, 2), "cantidad": len(ventas)})
    except Exception:
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
            (desde, hasta + " 23:59:59"),
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
        ayer = hoy - timedelta(days=1)
        mes = hoy.isoformat()[:7]

        ventas_hoy, num_hoy = _totales_periodo(conn, f"{hoy.isoformat()}%")
        ventas_ayer, _ = _totales_periodo(conn, f"{ayer.isoformat()}%")
        ventas_mes, num_mes = _totales_periodo(conn, f"{mes}%")

        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        num_prod = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= 5")
        stock_bajo = cursor.fetchone()[0]

        conn.close()
        return jsonify({"ok": True, "resumen": {
            "ventas_hoy": ventas_hoy,
            "transacciones_hoy": num_hoy,
            "ventas_ayer": ventas_ayer,
            "ventas_mes": ventas_mes,
            "transacciones_mes": num_mes,
            "productos": num_prod,
            "stock_bajo": stock_bajo,
        }})
    except Exception:
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

        ingresos_hoy, ventas_hoy = _totales_periodo(conn, f"{hoy.isoformat()}%")
        ingresos_mes, _ = _totales_periodo(conn, f"{mes}%")

        c.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        num_productos = c.fetchone()[0]

        c.execute(
            "SELECT nombre, SUM(cantidad) FROM historial_ventas "
            "WHERE fecha LIKE ? GROUP BY nombre ORDER BY SUM(cantidad) DESC LIMIT 1",
            (f"{hoy.isoformat()}%",),
        )
        top = c.fetchone()
        top_producto = top[0] if top else "N/A"

        conn.close()
        return jsonify({
            "ok": True,
            "ingresos_hoy": ingresos_hoy,
            "ventas_hoy": ventas_hoy,
            "ingresos_mes": ingresos_mes,
            "num_productos": num_productos,
            "top_producto": top_producto,
            "ganancia_estimada": round(ingresos_hoy * 0.30, 2),
        })
    except Exception:
        return jsonify({"ok": True, "ingresos_hoy": 0, "ventas_hoy": 0})
