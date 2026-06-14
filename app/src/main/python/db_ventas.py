"""db_ventas.py - Ventas, historial, ganancias (DAO)"""
from __future__ import annotations
import sqlite3, json
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE

def consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vendedor_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        if vendedor_id:
            cursor.execute("""
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? AND vendedor_id = ?
                ORDER BY fecha DESC
            """, (fecha_inicio, fecha_fin + " 23:59:59", vendedor_id))
        else:
            cursor.execute("""
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC
            """, (fecha_inicio, fecha_fin + " 23:59:59"))
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



def consultar_resumen_ventas(vendedor_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        base_totales = ("SELECT COUNT(*) AS num_ventas, SUM(total) AS total_ingresos, "
                        "AVG(total) AS promedio_venta, MAX(total) AS venta_maxima, "
                        "MIN(total) AS venta_minima, SUM(cantidad) AS unidades_vendidas "
                        "FROM historial_ventas")
        base_top = ("SELECT nombre AS producto, SUM(cantidad) AS total_unidades, "
                    "SUM(total) AS total_ingresos, COUNT(*) AS num_transacciones "
                    "FROM historial_ventas")
        base_metodo = ("SELECT metodo_pago, COUNT(*) AS num_ventas, SUM(total) AS total "
                       "FROM historial_ventas")
        if vendedor_id:
            where = " WHERE vendedor_id = ?"
            params = (vendedor_id,)
        else:
            where = ""
            params = ()
        cursor.execute(base_totales + where, params)
        totales = dict(cursor.fetchone())
        cursor.execute(base_top + where + " GROUP BY nombre ORDER BY total_unidades DESC LIMIT 5", params)
        top = [dict(f) for f in cursor.fetchall()]
        cursor.execute(base_metodo + where + " GROUP BY metodo_pago ORDER BY total DESC", params)
        por_metodo = [dict(f) for f in cursor.fetchall()]
        return {"totales": totales, "top_productos": top, "por_metodo_pago": por_metodo}
    finally:
        conn.close()



def consultar_ganancias_por_dia():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DATE(fecha) AS dia, COUNT(*) AS num_ventas,
                   SUM(cantidad) AS unidades_vendidas, SUM(total) AS total_ingresos
            FROM historial_ventas GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 30
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO LOCAL
# ══════════════════════════════════════════════════════════════
# === HISTORIAL DIARIO ===

def guardar_historial_diario_local(snapshot: dict) -> bool:
    """Guarda un snapshot diario en SQLite historial_diario."""
    conn = obtener_conexion()
    try:
        fecha = snapshot.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        conn.execute("""
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
        """, (
            fecha,
            float(snapshot.get("total_ventas", 0)),
            int(snapshot.get("num_transacciones", 0)),
            int(snapshot.get("productos_activos", 0)),
            int(snapshot.get("inventario_items", 0)),
            json.dumps(snapshot.get("ventas_data", []), ensure_ascii=False),
            json.dumps(snapshot.get("inventario_data", []), ensure_ascii=False),
            json.dumps(snapshot.get("config_snapshot", {}), ensure_ascii=False),
            snapshot.get("ts_guardado", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ))
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
        rows = conn.execute("""
            SELECT fecha, total_ventas, num_transacciones,
                   productos_activos, inventario_items, ts_guardado
            FROM historial_diario
            ORDER BY fecha DESC LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()



def obtener_historial_detalle_local(fecha: str) -> dict:
    """Devuelve el detalle completo de un día."""
    conn = obtener_conexion()
    try:
        row = conn.execute("SELECT * FROM historial_diario WHERE fecha=?", (fecha,)).fetchone()
        if not row: return {}
        d = dict(row)
        d["ventas_data"]    = json.loads(d.get("ventas_data",    "[]"))
        d["inventario_data"]= json.loads(d.get("inventario_data","[]"))
        d["config_snapshot"]= json.loads(d.get("config_snapshot","{}"))
        return d
    finally:
        conn.close()


# === LOGS Y AUDITORIA ===

