# -*- coding: utf-8 -*-
"""Blueprint: Catálogo de productos (CRUD + sincronización)"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

catalogo_bp = Blueprint('catalogo', __name__)


@catalogo_bp.route('/api/catalogo')
def catalogo():
    """Lista el catálogo de productos activos desde la BD."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.producto_id, p.nombre, COALESCE(p.categoria,'General'), "
            "p.precio, COALESCE(p.unidad_medida,'Un'), COALESCE(p.costo,0), "
            "CAST(COALESCE(ig.stock_actual, 0) AS INTEGER) "
            "FROM productos p "
            "LEFT JOIN inventario_general ig ON p.producto_id = ig.producto_id "
            "WHERE p.activo=1"
        )
        _EMOJIS = ["🍚", "🫘", "🫒", "🥤", "🧴", "🍬", "☕", "🥛", "🥚", "🍞", "🧼", "🪥"]
        prods = []
        for i, row in enumerate(cursor.fetchall()):
            prods.append({
                "id": row[0], "nombre": row[1], "categoria": row[2],
                "precio": row[3], "um": row[4], "costo": row[5],
                "stock": row[6], "codigo": row[0][:6],
                "imagen": _EMOJIS[i % len(_EMOJIS)],
            })
        conn.close()
        cats = sorted(set(p["categoria"] for p in prods))
        return jsonify({"ok": True, "productos": prods, "total": len(prods), "categorias": cats})
    except Exception as e:
        print(f"Catálogo error: {e}")
        return jsonify({"ok": False, "error": "No se pudo cargar el catálogo", "productos": []}), 500


@catalogo_bp.route('/api/catalogo/crear', methods=['POST'])
def catalogo_crear():
    """Crear un producto desde el catálogo."""
    d = request.get_json(silent=True) or {}
    nombre = d.get('nombre', '').strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400

    precio = float(d.get('precio', 0))
    costo = float(d.get('costo', precio * 0.7))
    categoria = d.get('categoria', 'General')
    um = d.get('um', d.get('unidad_medida', 'Un'))
    stock = int(d.get('stock', 0))
    imagen = d.get('imagen', '')

    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        pid = f"prod-{uuid.uuid4().hex[:8]}"
        c.execute(
            "INSERT INTO productos "
            "(producto_id,nombre,precio,costo,categoria,unidad_medida,imagen,activo) "
            "VALUES (?,?,?,?,?,?,?,1)",
            (pid, nombre, precio, costo, categoria, um, imagen),
        )
        c.execute(
            "INSERT INTO inventario_general "
            "(producto_id,nombre,stock_actual,stock_minimo,precio_compra,precio_venta,"
            "categoria,unidad_medida,actualizado) VALUES (?,?,?,5,?,?,?,?,?)",
            (pid, nombre, stock, costo, precio, categoria, um,
             datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": pid, "nombre": nombre})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/catalogo/actualizar/<producto_id>', methods=['PUT'])
def catalogo_actualizar(producto_id):
    """Actualizar nombre/precio/foto de un producto."""
    d = request.get_json(silent=True) or {}
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        campos, vals = [], []
        for key, col in [('nombre', 'nombre'), ('precio', 'precio'),
                         ('costo', 'costo'), ('categoria', 'categoria'),
                         ('um', 'unidad_medida'), ('imagen', 'imagen')]:
            if key in d:
                campos.append(f"{col}=?")
                vals.append(d[key] if key not in ('precio', 'costo') else float(d[key]))
        if not campos:
            return jsonify({"ok": False, "error": "Nada que actualizar"}), 400
        vals.append(producto_id)
        c.execute(f"UPDATE productos SET {','.join(campos)} WHERE producto_id=?", vals)
        # Sincronizar precio en inventario_general
        if 'precio' in d:
            c.execute("UPDATE inventario_general SET precio_venta=? WHERE producto_id=?",
                      (float(d['precio']), producto_id))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": producto_id, "mensaje": "Producto actualizado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/catalogo/eliminar/<producto_id>', methods=['DELETE'])
def catalogo_eliminar(producto_id):
    """Soft-delete de un producto."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("UPDATE productos SET activo=0 WHERE producto_id=?", (producto_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": producto_id, "mensaje": "Producto eliminado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/catalogo/sync', methods=['POST'])
def catalogo_sync():
    """Sincroniza catálogo completo (guardar fotos sin resetear stock)."""
    d = request.get_json(silent=True) or {}
    productos = d.get('productos', [])
    if not productos:
        return jsonify({"ok": True, "sincronizados": 0})
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        sincronizados = 0
        for p in productos:
            pid = p.get('id', '')
            if not pid:
                continue
            imagen = p.get('imagen', '')
            if imagen:
                c.execute("UPDATE productos SET imagen=? WHERE producto_id=?", (imagen, pid))
            nombre = p.get('nombre')
            precio = p.get('precio')
            if nombre:
                c.execute("UPDATE productos SET nombre=? WHERE producto_id=?", (nombre, pid))
            if precio is not None:
                c.execute("UPDATE productos SET precio=? WHERE producto_id=?", (float(precio), pid))
                c.execute("UPDATE inventario_general SET precio_venta=? WHERE producto_id=?",
                          (float(precio), pid))
            sincronizados += 1
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "sincronizados": sincronizados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/productos/precio', methods=['POST'])
def actualizar_precio_producto():
    """Actualiza precio de venta y/o costo de un producto."""
    d = request.get_json(silent=True) or {}
    pid = d.get('id') or d.get('producto_id')
    if not pid:
        return jsonify({"ok": False, "error": "Falta id de producto"}), 400
    precio = d.get('precio')
    costo = d.get('costo')
    if precio is None and costo is None:
        return jsonify({"ok": False, "error": "Nada que actualizar"}), 400
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        sets, params = [], []
        if precio is not None:
            sets.append("precio=?"); params.append(float(precio))
        if costo is not None:
            sets.append("costo=?"); params.append(float(costo))
        params.append(pid)
        c.execute("UPDATE productos SET " + ", ".join(sets) + " WHERE producto_id=?", params)
        if precio is not None:
            c.execute("UPDATE inventario_general SET precio_venta=? WHERE producto_id=?",
                      (float(precio), pid))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "id": pid, "precio": precio, "costo": costo})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/productos', methods=['POST'])
def crear_producto():
    """Crear un nuevo producto (vía CRUD genérico)."""
    d = request.get_json(silent=True) or {}
    nombre = d.get('nombre', '').strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        pid = f"prod-{uuid.uuid4().hex[:8]}"
        precio = float(d.get('precio', 0))
        costo = float(d.get('costo', d.get('costoUnitario', d.get('precioCosto', 0))))
        categoria = d.get('categoria', 'General')
        um = d.get('um', 'Un')
        stock = int(d.get('stock', 0))
        cursor.execute(
            "INSERT INTO productos (producto_id,nombre,precio,costo,categoria,unidad_medida,activo) "
            "VALUES (?,?,?,?,?,?,1)", (pid, nombre, precio, costo, categoria, um))
        cursor.execute(
            "INSERT INTO inventario_general (producto_id,nombre,stock_actual,stock_minimo,"
            "precio_venta,actualizado) VALUES (?,?,?,5,?,?)",
            (pid, nombre, stock, precio, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": pid, "nombre": nombre, "precio": precio,
                        "mensaje": "Producto creado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/productos/<producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    """Actualizar un producto existente."""
    d = request.get_json(silent=True) or {}
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        campos, vals = [], []
        for key, col in [('nombre', 'nombre'), ('precio', 'precio'),
                         ('costo', 'costo'), ('categoria', 'categoria'),
                         ('um', 'unidad_medida')]:
            if key in d:
                campos.append(f"{col}=?")
                vals.append(float(d[key]) if key in ('precio', 'costo') else d[key])
        if not campos:
            return jsonify({"ok": False, "error": "No hay campos para actualizar"}), 400
        vals.append(producto_id)
        cursor.execute(f"UPDATE productos SET {','.join(campos)} WHERE producto_id=?", vals)
        if 'precio' in d:
            cursor.execute("UPDATE inventario_general SET precio_venta=? WHERE producto_id=?",
                          (float(d['precio']), producto_id))
        if 'stock' in d:
            cursor.execute("UPDATE inventario_general SET stock_actual=?, actualizado=? WHERE producto_id=?",
                          (int(d['stock']), datetime.now().isoformat(), producto_id))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": producto_id, "mensaje": "Producto actualizado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/productos/<producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    """Soft-delete de producto."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET activo=0 WHERE producto_id=?", (producto_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": producto_id, "mensaje": "Producto eliminado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route('/api/reconstruir-desde-productos', methods=['POST'])
def reconstruir_desde_productos():
    """Reconstruye inventario desde lista de productos del frontend."""
    d = request.get_json(silent=True) or {}
    productos = d.get('productos', [])
    if not productos:
        return jsonify({"ok": True, "mensaje": "Sin productos", "reconstruidos": 0})
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        reconstruidos = 0
        for p_item in productos:
            nombre = p_item.get('nombre', '').strip()
            if not nombre:
                continue
            pid = p_item.get('id', '')
            precio = float(p_item.get('precio', 0))
            costo = float(p_item.get('costo', p_item.get('costoUnitario', p_item.get('precioCosto', precio * 0.7))))
            categoria = p_item.get('categoria', 'General')
            um = p_item.get('um', 'Un')
            _stock_raw = p_item.get('stock_actual', p_item.get('stock', 0))
            try:
                stock = int(float(_stock_raw))
            except (TypeError, ValueError):
                stock = 0
            cursor.execute(
                "SELECT producto_id FROM productos WHERE producto_id=? OR nombre=?",
                (pid, nombre))
            existente = cursor.fetchone()
            if existente:
                cursor.execute(
                    "UPDATE productos SET precio=?,costo=?,categoria=?,unidad_medida=?,activo=1 "
                    "WHERE producto_id=?",
                    (precio, costo, categoria, um, existente[0]))
                cursor.execute(
                    "UPDATE inventario_general SET stock_actual=?,precio_venta=?,actualizado=? "
                    "WHERE producto_id=?",
                    (stock, precio, datetime.now().isoformat(), existente[0]))
            else:
                new_pid = pid or f"prod-{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    "INSERT INTO productos (producto_id,nombre,precio,costo,categoria,"
                    "unidad_medida,activo) VALUES (?,?,?,?,?,?,1)",
                    (new_pid, nombre, precio, costo, categoria, um))
                cursor.execute(
                    "INSERT INTO inventario_general (producto_id,nombre,stock_actual,"
                    "stock_minimo,precio_venta,actualizado) VALUES (?,?,?,5,?,?)",
                    (new_pid, nombre, stock, precio, datetime.now().isoformat()))
            reconstruidos += 1
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": f"{reconstruidos} productos reconstruidos",
                        "reconstruidos": reconstruidos, "total": reconstruidos})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
