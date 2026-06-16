"""db_ventas.py - Ventas, historial, ganancias (DAO)."""
from __future__ import annotations
import json
from datetime import datetime
from db_connection import obtener_conexion


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


def consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vendedor_id=None):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        if _usar_ventas_atomicas(conn):
            sql = [
                "SELECT vc.venta_id,",
                "       COALESCE(GROUP_CONCAT(vd.nombre, ' | '), '(sin detalle)') AS producto,",
                "       COALESCE(SUM(vd.cantidad), 0) AS cantidad,",
                "       CASE WHEN COALESCE(SUM(vd.cantidad), 0) > 0",
                "            THEN ROUND(vc.total / SUM(vd.cantidad), 2)",
                "            ELSE vc.total END AS precio_unitario,",
                "       vc.total AS total,",
                "       vc.metodo_pago AS metodo_pago,",
                "       vc.vendedor_nombre AS vendedor_nombre,",
                "       vc.fecha AS fecha",
                "FROM ventas_cabecera vc",
                "LEFT JOIN ventas_detalle vd ON vd.venta_id = vc.venta_id",
                "WHERE vc.fecha BETWEEN ? AND ?",
            ]
            params = [fecha_inicio, fecha_fin + " 23:59:59"]
            if vendedor_id:
                sql.append("AND vc.vendedor_id = ?")
                params.append(vendedor_id)
            sql.extend([
                "GROUP BY vc.venta_id, vc.total, vc.metodo_pago, vc.vendedor_nombre, vc.fecha",
                "ORDER BY vc.fecha DESC",
            ])
            cursor.execute("\n".join(sql), tuple(params))
            return [dict(f) for f in cursor.fetchall()]

        if vendedor_id:
            cursor.execute(
                """
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? AND vendedor_id = ?
                ORDER BY fecha DESC
                """,
                (fecha_inicio, fecha_fin + " 23:59:59", vendedor_id),
            )
        else:
            cursor.execute(
                """
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC
                """,
                (fecha_inicio, fecha_fin + " 23:59:59"),
            )
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



def consultar_resumen_ventas(vendedor_id=None):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        if _usar_ventas_atomicas(conn):
            where = " WHERE vc.vendedor_id = ?" if vendedor_id else ""
            params = (vendedor_id,) if vendedor_id else ()

            cursor.execute(
                (
                    "SELECT COUNT(*) AS num_ventas, "
                    "COALESCE(SUM(vc.total), 0) AS total_ingresos, "
                    "COALESCE(AVG(vc.total), 0) AS promedio_venta, "
                    "COALESCE(MAX(vc.total), 0) AS venta_maxima, "
                    "COALESCE(MIN(vc.total), 0) AS venta_minima "
                    "FROM ventas_cabecera vc" + where
                ),
                params,
            )
            totales = dict(cursor.fetchone())

            cursor.execute(
                (
                    "SELECT COALESCE(SUM(vd.cantidad), 0) AS unidades_vendidas "
                    "FROM ventas_detalle vd "
                    "JOIN ventas_cabecera vc ON vc.venta_id = vd.venta_id" + where
                ),
                params,
            )
            unidades = cursor.fetchone()
            totales["unidades_vendidas"] = unidades["unidades_vendidas"] if unidades else 0

            cursor.execute(
                (
                    "SELECT vd.nombre AS producto, COALESCE(SUM(vd.cantidad),0) AS total_unidades, "
                    "COALESCE(SUM(vd.subtotal),0) AS total_ingresos, "
                    "COUNT(DISTINCT vd.venta_id) AS num_transacciones "
                    "FROM ventas_detalle vd "
                    "JOIN ventas_cabecera vc ON vc.venta_id = vd.venta_id" + where + " "
                    "GROUP BY vd.nombre ORDER BY total_unidades DESC LIMIT 5"
                ),
                params,
            )
            top = [dict(f) for f in cursor.fetchall()]

            cursor.execute(
                (
                    "SELECT vc.metodo_pago, COUNT(*) AS num_ventas, COALESCE(SUM(vc.total),0) AS total "
                    "FROM ventas_cabecera vc" + where + " "
                    "GROUP BY vc.metodo_pago ORDER BY total DESC"
                ),
                params,
            )
            por_metodo = [dict(f) for f in cursor.fetchall()]
            return {"totales": totales, "top_productos": top, "por_metodo_pago": por_metodo}

        if vendedor_id:
            where = " WHERE vendedor_id = ?"
            params = (vendedor_id,)
        else:
            where = ""
            params = ()

        cursor.execute(
            (
                "SELECT COUNT(*) AS num_ventas, COALESCE(SUM(total_venta),0) AS total_ingresos, "
                "COALESCE(AVG(total_venta),0) AS promedio_venta, "
                "COALESCE(MAX(total_venta),0) AS venta_maxima, "
                "COALESCE(MIN(total_venta),0) AS venta_minima "
                "FROM (SELECT venta_id, SUM(total) AS total_venta FROM historial_ventas" + where + " GROUP BY venta_id)"
            ),
            params,
        )
        totales = dict(cursor.fetchone())

        cursor.execute(
            ("SELECT COALESCE(SUM(cantidad),0) AS unidades_vendidas FROM historial_ventas" + where),
            params,
        )
        unidades = cursor.fetchone()
        totales["unidades_vendidas"] = unidades["unidades_vendidas"] if unidades else 0

        cursor.execute(
            (
                "SELECT nombre AS producto, SUM(cantidad) AS total_unidades, "
                "SUM(total) AS total_ingresos, COUNT(DISTINCT venta_id) AS num_transacciones "
                "FROM historial_ventas" + where + " "
                "GROUP BY nombre ORDER BY total_unidades DESC LIMIT 5"
            ),
            params,
        )
        top = [dict(f) for f in cursor.fetchall()]

        cursor.execute(
            (
                "SELECT metodo_pago, COUNT(*) AS num_ventas, SUM(total_venta) AS total "
                "FROM (SELECT venta_id, MAX(metodo_pago) AS metodo_pago, SUM(total) AS total_venta "
                "      FROM historial_ventas" + where + " GROUP BY venta_id) "
                "GROUP BY metodo_pago ORDER BY total DESC"
            ),
            params,
        )
        por_metodo = [dict(f) for f in cursor.fetchall()]
        return {"totales": totales, "top_productos": top, "por_metodo_pago": por_metodo}
    finally:
        conn.close()



def consultar_ganancias_por_dia():
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        if _usar_ventas_atomicas(conn):
            cursor.execute(
                """
                SELECT d.dia,
                       d.num_ventas,
                       COALESCE(u.unidades_vendidas, 0) AS unidades_vendidas,
                       d.total_ingresos
                FROM (
                    SELECT DATE(fecha) AS dia,
                           COUNT(*) AS num_ventas,
                           COALESCE(SUM(total), 0) AS total_ingresos
                    FROM ventas_cabecera
                    GROUP BY DATE(fecha)
                ) d
                LEFT JOIN (
                    SELECT DATE(vc.fecha) AS dia,
                           COALESCE(SUM(vd.cantidad), 0) AS unidades_vendidas
                    FROM ventas_cabecera vc
                    JOIN ventas_detalle vd ON vd.venta_id = vc.venta_id
                    GROUP BY DATE(vc.fecha)
                ) u ON u.dia = d.dia
                ORDER BY d.dia DESC LIMIT 30
                """
            )
            return [dict(f) for f in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DATE(fecha) AS dia,
                   COUNT(DISTINCT venta_id) AS num_ventas,
                   SUM(cantidad) AS unidades_vendidas,
                   SUM(total) AS total_ingresos
            FROM historial_ventas
            GROUP BY DATE(fecha)
            ORDER BY dia DESC LIMIT 30
            """
        )
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO LOCAL
# ══════════════════════════════════════════════════════════════
def guardar_historial_diario_local(snapshot: dict) -> bool:
    """Guarda un snapshot diario en SQLite historial_diario."""
    conn = obtener_conexion()
    try:
        fecha = snapshot.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        conn.execute(
            """
            INSERT INTO historial_diario
                (fecha, total_ventas, num_transacciones, productos_activos,
                 inventario_items, ventas_data, inventario_data, config_snapshot, ts_guardado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                total_ventas      = excluded.total_ventas,
                num_transacciones = excluded.num_transacciones,
                productos_activos = excluded.productos_activos,
                inventario_items  = excluded.inventario_items,
                ventas_data       = excluded.ventas_data,
                inventario_data   = excluded.inventario_data,
                config_snapshot   = excluded.config_snapshot,
                ts_guardado       = excluded.ts_guardado
            """,
            (
                fecha,
                float(snapshot.get("total_ventas", 0)),
                int(snapshot.get("num_transacciones", 0)),
                int(snapshot.get("productos_activos", 0)),
                int(snapshot.get("inventario_items", 0)),
                json.dumps(snapshot.get("ventas_data", []), ensure_ascii=False),
                json.dumps(snapshot.get("inventario_data", []), ensure_ascii=False),
                json.dumps(snapshot.get("config_snapshot", {}), ensure_ascii=False),
                snapshot.get("ts_guardado", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error guardando historial local: {e}")
        return False
    finally:
        conn.close()



def obtener_historial_diario_local(limite=30) -> list:
    """Devuelve los últimos N días del historial local."""
    conn = obtener_conexion()
    try:
        rows = conn.execute(
            """
            SELECT fecha, total_ventas, num_transacciones,
                   productos_activos, inventario_items, ts_guardado
            FROM historial_diario
            ORDER BY fecha DESC LIMIT ?
            """,
            (limite,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()



def obtener_historial_detalle_local(fecha: str) -> dict:
    """Devuelve el detalle completo de un día."""
    conn = obtener_conexion()
    try:
        row = conn.execute("SELECT * FROM historial_diario WHERE fecha=?", (fecha,)).fetchone()
        if not row:
            return {}
        d = dict(row)
        d["ventas_data"] = json.loads(d.get("ventas_data", "[]"))
        d["inventario_data"] = json.loads(d.get("inventario_data", "[]"))
        d["config_snapshot"] = json.loads(d.get("config_snapshot", "{}"))
        return d
    finally:
        conn.close()
