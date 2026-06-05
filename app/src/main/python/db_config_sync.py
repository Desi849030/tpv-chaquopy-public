from __future__ import annotations

"""db_config_sync.py - Extracted from db_config.py"""
"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE
from db_users import _crear_desarrollador_default

from db.schema import crear_tablas_schema
from db_connection import obtener_conexion
from db_users import _crear_desarrollador_default

# === ESTADO Y SINCRONIZACION ===


__all__ = ['cargar_estado', 'guardar_estado', '_sincronizar_tablas_relacionales']
def cargar_estado():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM app_state WHERE clave = ?", ("estado_tpv",))
        fila = cursor.fetchone()
        return json.loads(fila["valor"]) if fila else None
    except Exception as e:
        print(f"❌ Error cargar estado: {e}")
        return None
    finally:
        conn.close()



def guardar_estado(estado):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        valor_json = json.dumps(estado, ensure_ascii=False)
        ahora      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT OR REPLACE INTO app_state (clave, valor, actualizado) VALUES (?, ?, ?)
        """, ("estado_tpv", valor_json, ahora))
        conn.commit()
        _sincronizar_tablas_relacionales(cursor, conn, estado)
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error guardar estado: {e}")
        return False
    finally:
        conn.close()



def _sincronizar_tablas_relacionales(cursor, conn, estado):
    for venta in estado.get("historialVentas", []):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO historial_ventas
                    (venta_id, producto_id, nombre, cantidad, precio_unit,
                     total, metodo_pago, vendedor_id, vendedor_nombre, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (venta.get("id",""), venta.get("productoId",""), venta.get("nombre",""),
                  venta.get("cantidad",1), venta.get("precio",0), venta.get("total",0),
                  venta.get("metodoPago","efectivo"), venta.get("vendedorId",None),
                  venta.get("vendedorNombre",None),
                  venta.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
        except sqlite3.Error:
            pass

    for p in estado.get("productos", []):
        try:
            pid  = p.get("id","")
            nom  = p.get("nombre","")
            pv   = float(p.get("precio", 0) or 0)
            pc   = float(p.get("costoUnitario", p.get("costo", 0)) or 0)
            cat  = p.get("categoria","General") or "General"
            um   = p.get("um", p.get("unidadMedida","C/U")) or "C/U"
            oferta = 1 if p.get("onSale", p.get("enOferta", False)) else 0
            img  = p.get("imagen","")
            if not pid: continue
            cursor.execute("""
                INSERT OR REPLACE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, nom, pv, pc, cat, um, oferta, img))
            # Mantener inventario_general sincronizado (solo metadatos, nunca stock)
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id, nombre, stock_actual, stock_minimo,
                     precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                VALUES (?, ?, 0, 5, ?, ?, ?, ?, ?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    stock_actual  = MAX(inventario_general.stock_actual, excluded.stock_actual),
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra > 0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (pid, nom, pc, pv, cat, um, ahora))
        except sqlite3.Error:
            pass

    for c in estado.get("cierresCaja", []):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO cierres_caja
                    (fecha, total_ventas, total_costos, total_comisiones, ganancia_total)
                VALUES (?, ?, ?, ?, ?)
            """, (c.get("fecha","")[:10], c.get("totalVentas",0), c.get("totalCostos",0),
                  c.get("totalComisiones",0), c.get("gananciaTotal",0)))
        except sqlite3.Error:
            pass
    conn.commit()

# ══════════════════════════════════════════════════════════════
#  CONSULTAS REPORTES
# ══════════════════════════════════════════════════════════════
# === CONSULTAS DE VENTAS ===

