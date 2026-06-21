from __future__ import annotations
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE



def obtener_productos_catalogo():
    """
    Devuelve catálogo activo desde la tabla productos.
    NO hace auto-repoblación — si está vacío, devuelve lista vacía.
    """
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT producto_id AS id, nombre, precio,
                   costo AS costoUnitario, categoria,
                   unidad_medida AS um, en_oferta AS onSale, imagen
            FROM productos ORDER BY categoria, nombre ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()




def sincronizar_productos_catalogo(productos, admin_id):
    """
    Sincroniza productos del cliente → servidor.
    Actualiza tabla productos e inventario_general simultáneamente.
    El stock_actual del almacén NUNCA se modifica.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador","desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede sincronizar catálogo"}
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in productos:
            pid  = p.get("id","");
            if not pid: continue
            nom  = p.get("nombre","")
            pv   = float(p.get("precio",0))
            pc   = float(p.get("costoUnitario",0))
            cat  = p.get("categoria","General") or "General"
            um   = p.get("um","C/U") or "C/U"
            oferta = 1 if p.get("onSale") else 0
            img  = p.get("imagen","")
            # tabla productos
            cursor.execute("""
                INSERT INTO productos
                    (producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,imagen,activo)
                VALUES (?,?,?,?,?,?,?,?,1)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre=excluded.nombre, precio=excluded.precio, costo=excluded.costo,
                    categoria=excluded.categoria, unidad_medida=excluded.unidad_medida,
                    en_oferta=excluded.en_oferta, imagen=excluded.imagen, activo=1
            """, (pid,nom,pv,pc,cat,um,oferta,img))
            # inventario_general: actualiza metadatos, NUNCA stock
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id,nombre,stock_actual,stock_minimo,
                     precio_compra,precio_venta,categoria,unidad_medida,actualizado)
                VALUES (?,?,0,5,?,?,?,?,?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra>0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (pid,nom,pc,pv,cat,um,ahora))
        ids = [p.get("id","") for p in productos if p.get("id","")]
        if ids:
            ph = ",".join("?"*len(ids))
            cursor.execute(f"UPDATE productos SET activo=0 WHERE producto_id NOT IN ({ph})",ids)
        conn.commit()
        return {"ok": True, "sincronizados": len(productos)}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()




def importar_catalogo_a_inventario(admin_id):
    """Catálogo → inventario_general. Nuevos: stock 0. Existentes: conserva stock."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?",(admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador","desarrollador"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}
        cursor.execute("SELECT producto_id,nombre,precio,costo,categoria,unidad_medida FROM productos")
        prods = cursor.fetchall()
        if not prods:
            return {"ok": False, "mensaje": "Catálogo vacío"}
        ahora   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevos  = existentes = 0
        for p in prods:
            cursor.execute("""
                INSERT OR IGNORE INTO inventario_general
                    (producto_id,nombre,stock_actual,stock_minimo,
                     precio_compra,precio_venta,categoria,unidad_medida,actualizado)
                VALUES (?,?,0,5,?,?,?,?,?)
            """, (p["producto_id"],p["nombre"],
                  float(p["costo"] or 0), float(p["precio"] or 0),
                  p["categoria"] or "General", p["unidad_medida"] or "C/U", ahora))
            if cursor.rowcount > 0:
                nuevos += 1
            else:
                cursor.execute("""
                    UPDATE inventario_general SET
                        nombre=?, precio_venta=?,
                        precio_compra=CASE WHEN ?> 0 THEN ? ELSE precio_compra END,
                        categoria=?, unidad_medida=?, actualizado=?
                    WHERE producto_id=?
                """, (p["nombre"], float(p["precio"] or 0),
                      float(p["costo"] or 0), float(p["costo"] or 0),
                      p["categoria"] or "General", p["unidad_medida"] or "C/U",
                      ahora, p["producto_id"]))
                existentes += 1
        conn.commit()
        agregar_log(f"Import catálogo→almacén: {nuevos} nuevos, {existentes} actualizados", "info")
        return {"ok":True,"nuevos":nuevos,"existentes":existentes,"total":len(prods),
                "mensaje":f"{nuevos} nuevos · {existentes} actualizados (stock conservado)"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()




def eliminar_producto_inventario_general(producto_id, admin_id):
    """Borra producto del almacén y lo desactiva en catálogo."""
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM inventario_general WHERE producto_id=?", (producto_id,))
        conn.execute("UPDATE productos SET activo=0 WHERE producto_id=?", (producto_id,))
        conn.commit()
        agregar_log(f"Producto {producto_id} eliminado del almacén", "warning")
        return {"ok": True, "mensaje": "Eliminado"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



# ══════════════════════════════════════════════════════════════
#  SINCRONIZACIÓN COMPLETA — une productos ↔ inventario_general
# ══════════════════════════════════════════════════════════════


def consultar_inventario_actual():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT producto_id AS id, nombre, precio, costo, categoria,
                   unidad_medida, CASE WHEN en_oferta=1 THEN 'Sí' ELSE 'No' END AS en_oferta
            FROM productos WHERE activo = 1 ORDER BY categoria, nombre ASC
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



