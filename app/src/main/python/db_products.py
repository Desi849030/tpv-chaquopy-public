"""db_products.py - Productos, inventario, catalogo, importacion (DAO)"""
from __future__ import annotations
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE

def cargar_stock_masivo(admin_id, items):
    """
    Carga stock a múltiples productos del almacén general de una vez.
    items = [{ producto_id, cantidad, precio_compra }]
    Suma la cantidad al stock_actual existente (igual que registrar_entrada).
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}

        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok = 0
        for item in items:
            pid  = item.get("producto_id", "")
            cant = float(item.get("cantidad", 0) or 0)
            pc   = float(item.get("precio_compra", 0) or 0)
            if not pid or cant <= 0:
                continue
            # Solo actualiza stock si el producto ya existe en inventario_general
            cursor.execute("""
                UPDATE inventario_general
                SET stock_actual  = stock_actual + ?,
                    precio_compra = CASE WHEN ? > 0 THEN ? ELSE precio_compra END,
                    actualizado   = ?
                WHERE producto_id = ?
            """, (cant, pc, pc, fecha_ahora, pid))
            if cursor.rowcount > 0:
                ok += 1
        conn.commit()
        agregar_log(f"Stock masivo: {ok} productos actualizados por {admin_id}", "info")
        return {"ok": True, "actualizados": ok,
                "mensaje": f"✅ Stock cargado en {ok} productos"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def registrar_entrada_producto(datos, admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede registrar entradas"}

        producto_id   = datos.get("producto_id", "")
        nombre        = datos.get("nombre", "")
        cantidad      = float(datos.get("cantidad", 0))
        precio_compra = float(datos.get("precio_compra", 0))
        precio_venta  = float(datos.get("precio_venta",  0))
        categoria     = datos.get("categoria", "General")
        unidad_medida = datos.get("unidad_medida", "Un")
        proveedor     = datos.get("proveedor", "")
        nota          = datos.get("nota", "")

        if not producto_id or cantidad <= 0:
            return {"ok": False, "mensaje": "producto_id y cantidad > 0 son obligatorios"}

        entrada_id  = f"ent-{uuid.uuid4().hex[:8]}"
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO entradas_productos
                (entrada_id, producto_id, nombre, cantidad, precio_compra,
                 proveedor, nota, registrado_por, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entrada_id, producto_id, nombre, cantidad, precio_compra,
              proveedor, nota, admin_id, fecha_ahora))

        # Guardar precio_venta, categoria y unidad también para uso en asignación
        cursor.execute("""
            INSERT INTO inventario_general
                (producto_id, nombre, stock_actual, precio_compra, precio_venta,
                 categoria, unidad_medida, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(producto_id) DO UPDATE SET
                stock_actual  = stock_actual + excluded.stock_actual,
                precio_compra = excluded.precio_compra,
                precio_venta  = CASE WHEN excluded.precio_venta > 0
                                     THEN excluded.precio_venta
                                     ELSE inventario_general.precio_venta END,
                categoria     = CASE WHEN excluded.categoria != ''
                                     THEN excluded.categoria
                                     ELSE inventario_general.categoria END,
                unidad_medida = CASE WHEN excluded.unidad_medida != ''
                                     THEN excluded.unidad_medida
                                     ELSE inventario_general.unidad_medida END,
                actualizado   = excluded.actualizado
        """, (producto_id, nombre, cantidad, precio_compra, precio_venta,
              categoria, unidad_medida, fecha_ahora))

        conn.commit()
        agregar_log(f"Entrada: +{cantidad} '{nombre}' por {admin_id}", "info")
        return {"ok": True, "mensaje": f"+{cantidad} '{nombre}'", "entrada_id": entrada_id}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def obtener_inventario_general(admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return []
        cursor.execute("""
            SELECT ig.producto_id, ig.nombre, ig.stock_actual, ig.stock_minimo,
                   ig.precio_compra, ig.precio_venta, ig.categoria, ig.unidad_medida,
                   ig.actualizado, COALESCE(SUM(e.cantidad),0) AS total_entradas
            FROM inventario_general ig
            LEFT JOIN entradas_productos e ON ig.producto_id = e.producto_id
            GROUP BY ig.producto_id ORDER BY ig.nombre ASC
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



def obtener_historial_entradas(admin_id, producto_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        if producto_id:
            cursor.execute("""
                SELECT e.*, u.nombre AS admin_nombre FROM entradas_productos e
                LEFT JOIN usuarios u ON e.registrado_por = u.usuario_id
                WHERE e.producto_id = ? ORDER BY e.fecha DESC
            """, (producto_id,))
        else:
            cursor.execute("""
                SELECT e.*, u.nombre AS admin_nombre FROM entradas_productos e
                LEFT JOIN usuarios u ON e.registrado_por = u.usuario_id
                ORDER BY e.fecha DESC LIMIT 100
            """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  INVENTARIO DIARIO
# ══════════════════════════════════════════════════════════════
# === INVENTARIO DIARIO ===

def asignar_inventario_diario(vendedor_id, productos, admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede asignar inventario"}

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        errores   = []
        asignados = 0
        for prod in productos:
            pid  = prod.get("producto_id", "")
            cant = float(prod.get("cant_asignada", 0))
            if not pid or cant <= 0:
                continue

            cursor.execute("SELECT stock_actual FROM inventario_general WHERE producto_id = ?", (pid,))
            row = cursor.fetchone()
            stock_disp = row["stock_actual"] if row else 0

            # Si stock insuficiente, asignar lo que haya si > 0
            cant_real = cant if (stock_disp >= cant) else stock_disp
            if cant_real <= 0:
                errores.append(f"'{prod.get('nombre','?')}': sin stock (disponible: {stock_disp})")
                continue

            comision_pct = float(prod.get("comision_pct", 0))  # % comisión del admin

            cursor.execute("""
                INSERT INTO inventario_diario
                    (fecha, vendedor_id, producto_id, nombre, cant_asignada,
                     precio_venta, precio_costo, unidad_medida)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fecha, vendedor_id, producto_id) DO UPDATE SET
                    cant_asignada = cant_asignada + excluded.cant_asignada,
                    precio_venta  = excluded.precio_venta,
                    precio_costo  = excluded.precio_costo,
                    unidad_medida = excluded.unidad_medida,
                    activo = 1
            """, (fecha_hoy, vendedor_id, pid, prod.get("nombre",""), cant_real,
                  float(prod.get("precio_venta", 0)),
                  float(prod.get("precio_costo", 0)),
                  prod.get("unidad_medida", "Un")))

            cursor.execute("""
                UPDATE inventario_general
                SET stock_actual = MAX(0, stock_actual - ?), actualizado = ?
                WHERE producto_id = ?
            """, (cant_real, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pid))
            asignados += 1

        conn.commit()
        msg = f"{asignados} productos asignados"
        if errores:
            msg += f" | Sin stock: {', '.join(errores)}"
        return {"ok": asignados > 0 or not errores, "mensaje": msg, "errores": errores, "asignados": asignados}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def obtener_inventario_diario(vendedor_id, fecha=None):
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id.producto_id, id.nombre, id.cant_asignada, id.cant_vendida,
                   id.cant_final,
                   id.cant_asignada - id.cant_vendida AS cant_disponible,
                   id.precio_venta, id.precio_costo,
                   COALESCE(NULLIF(id.unidad_medida,''), ig.unidad_medida, 'Un') AS um
            FROM inventario_diario id
            LEFT JOIN inventario_general ig ON ig.producto_id = id.producto_id
            WHERE id.vendedor_id = ? AND id.fecha = ? AND id.activo = 1
            ORDER BY id.nombre ASC
        """, (vendedor_id, fecha))
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



def actualizar_vendido_diario(vendedor_id, producto_id, cantidad_vendida):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = obtener_conexion()
    try:
        conn.execute("""
            UPDATE inventario_diario SET cant_vendida = cant_vendida + ?
            WHERE vendedor_id = ? AND producto_id = ? AND fecha = ?
        """, (cantidad_vendida, vendedor_id, producto_id, fecha_hoy))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  LIMPIAR INVENTARIOS DIARIOS
# ══════════════════════════════════════════════════════════════

def limpiar_inventarios_diarios(admin_id, vendedor_id=None, fecha=None):
    """Elimina registros de inventario_diario. Si vendedor_id=None limpia todos."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede limpiar inventarios"}
        if vendedor_id and fecha:
            cursor.execute("DELETE FROM inventario_diario WHERE vendedor_id = ? AND fecha = ?", (vendedor_id, fecha))
        elif vendedor_id:
            cursor.execute("DELETE FROM inventario_diario WHERE vendedor_id = ?", (vendedor_id,))
        elif fecha:
            cursor.execute("DELETE FROM inventario_diario WHERE fecha = ?", (fecha,))
        else:
            cursor.execute("DELETE FROM inventario_diario")
        eliminados = cursor.rowcount
        conn.commit()
        agregar_log(f"Inventarios limpiados ({eliminados} registros) por {admin_id}", "info")
        return {"ok": True, "eliminados": eliminados, "mensaje": f"{eliminados} registros eliminados"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  CATÁLOGO DE PRODUCTOS (server-side, compartido entre roles)
# ══════════════════════════════════════════════════════════════
# === CATALOGO Y PRODUCTOS ===

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
        if not u or u["rol"] not in ("administrador","desarrollador","vendedor"):
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
        if not u or u["rol"] not in ("administrador","desarrollador","vendedor"):
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



