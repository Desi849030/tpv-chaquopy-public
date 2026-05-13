from __future__ import annotations

"""db_config_inventario.py - Extracted from db_config.py"""
"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE
from db.users import _crear_desarrollador_default

from db.schema import crear_tablas_schema
from db_connection import obtener_conexion

# === INVENTARIO GENERAL ===


__all__ = ['sincronizar_estado_completo', 'limpiar_tablas_completo', 'reconstruir_desde_productos']
def sincronizar_estado_completo(admin_id):
    """
    Sincronización en cascada:
      1. productos  →  inventario_general  (metadatos, nunca stock)
      2. inventario_general  →  productos  (productos huérfanos del almacén)
    Devuelve resumen de lo sincronizado.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede sincronizar"}

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. productos → inventario_general
        cursor.execute("SELECT * FROM productos")
        prods = cursor.fetchall()
        sync_p2i = 0
        for p in prods:
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id, nombre, stock_actual, stock_minimo,
                     precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                VALUES (?, ?, 0, 5, ?, ?, ?, ?, ?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra > 0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (p["producto_id"], p["nombre"],
                  float(p["costo"] or 0), float(p["precio"] or 0),
                  p["categoria"] or "General", p["unidad_medida"] or "C/U", ahora))
            sync_p2i += 1

        # 2. inventario_general → productos (huérfanos)
        cursor.execute("""
            SELECT * FROM inventario_general
            WHERE producto_id NOT IN (SELECT producto_id FROM productos)
        """)
        huerfanos = cursor.fetchall()
        sync_i2p = 0
        for ig in huerfanos:
            cursor.execute("""
                INSERT OR IGNORE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen, activo)
                VALUES (?, ?, ?, ?, ?, ?, 0, '', 1)
            """, (ig["producto_id"], ig["nombre"],
                  float(ig["precio_venta"] or 0), float(ig["precio_compra"] or 0),
                  ig["categoria"] or "General", ig["unidad_medida"] or "C/U"))
            sync_i2p += 1

        conn.commit()
        agregar_log(
            f"Sync completo: {sync_p2i} productos→almacén, {sync_i2p} huérfanos recuperados",
            "info"
        )
        return {
            "ok": True,
            "productos_a_almacen": sync_p2i,
            "huerfanos_recuperados": sync_i2p,
            "mensaje": f"✅ {sync_p2i} productos sincronizados al almacén · {sync_i2p} huérfanos recuperados"
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def limpiar_tablas_completo(admin_id):
    """
    Borrado total y real en todos los almacenes del servidor:
      - productos
      - inventario_general
      - entradas_productos
      - inventario_diario
      - inventarios
      - app_state  (estado JSON del cliente)
    NO toca: usuarios, licencias, cierres_caja, gastos, historial_ventas, logs.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}

        tablas = [
            "productos",
            "inventario_general",
            "entradas_productos",
            "inventario_diario",
            "inventarios",
        ]
        conteos = {}
        for t in tablas:
            cursor.execute(f"DELETE FROM {t}")
            conteos[t] = cursor.rowcount

        # Borrar el estado JSON guardado
        cursor.execute("DELETE FROM app_state WHERE clave='estado_tpv'")
        conn.commit()

        resumen = " · ".join(f"{t}: {n}" for t, n in conteos.items())
        agregar_log(f"Limpieza completa por {admin_id}: {resumen}", "warning")
        return {
            "ok":      True,
            "conteos": conteos,
            "mensaje": f"🗑️ Limpieza completa: {resumen}"
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def reconstruir_desde_productos(admin_id, productos_js):
    agregar_log(f"[v25] reconstruir: admin={admin_id}, n={len(productos_js)}", "info")
    """
    Recibe la lista de productos del cliente (JS) y reconstruye
    productos + inventario_general desde cero.
    Acepta campo opcional 'stock_actual' en cada producto para
    poblar el almacén con el stock real del Excel importado.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = 0
        for p in productos_js:
            pid = p.get("id", "")
            if not pid: continue
            nom    = p.get("nombre", "")
            pv     = float(p.get("precio", 0) or 0)
            pc     = float(p.get("costoUnitario", p.get("costo", 0)) or 0)
            cat    = p.get("categoria", "General") or "General"
            um     = p.get("um", p.get("unidadMedida", "C/U")) or "C/U"
            oferta = 1 if p.get("onSale", p.get("enOferta", False)) else 0
            img    = p.get("imagen", "")
            # Stock real del XLSX si viene; si no, conservar el existente o 0
            stock  = p.get("stock_actual", None)

            cursor.execute("""
                INSERT OR REPLACE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen, activo)
                VALUES (?,?,?,?,?,?,?,?,1)
            """, (pid, nom, pv, pc, cat, um, oferta, img))

            if stock is not None:
                # Stock explícito enviado desde el cliente (viene del XLSX)
                cursor.execute("""
                    INSERT OR REPLACE INTO inventario_general
                        (producto_id, nombre, stock_actual, stock_minimo,
                         precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                    VALUES (?,?,?,5,?,?,?,?,?)
                """, (pid, nom, float(stock), pc, pv, cat, um, ahora))
            else:
                # Sin stock explícito: insertar con 0, o actualizar solo metadatos si ya existe
                cursor.execute("""
                    INSERT INTO inventario_general
                        (producto_id, nombre, stock_actual, stock_minimo,
                         precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                    VALUES (?,?,0,5,?,?,?,?,?)
                    ON CONFLICT(producto_id) DO UPDATE SET
                        nombre        = excluded.nombre,
                        precio_venta  = excluded.precio_venta,
                        precio_compra = CASE WHEN excluded.precio_compra > 0
                                        THEN excluded.precio_compra
                                        ELSE inventario_general.precio_compra END,
                        categoria     = excluded.categoria,
                        unidad_medida = excluded.unidad_medida,
                        actualizado   = excluded.actualizado
                """, (pid, nom, pc, pv, cat, um, ahora))
            total += 1

        conn.commit()
        agregar_log(f"Reconstrucción: {total} productos desde cliente", "info")
        return {"ok": True, "total": total,
                "mensaje": f"✅ {total} productos reconstruidos en servidor"}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  ESTADO JSON
# ══════════════════════════════════════════════════════════════
