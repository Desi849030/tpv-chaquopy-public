# -*- coding: utf-8 -*-
"""Blueprint: Catálogo (CRUD productos, categorías, nomenclador)."""
from flask import Blueprint, request, jsonify
from decorators import login_required, requiere_rol, usuario_actual

catalogo_bp = Blueprint('catalogo_bp', __name__, url_prefix='/api')


@catalogo_bp.route("/productos", methods=["GET"])
@login_required
def api_listar_productos():
    from db_connection import obtener_conexion
    try:
        conn = obtener_conexion()
        cursor = conn.execute(
            "SELECT producto_id, nombre, precio, costo, categoria, "
            "unidad_medida, imagen, en_oferta, activo "
            "FROM productos ORDER BY nombre"
        )
        productos = []
        for r in cursor.fetchall():
            productos.append({
                "id": r["producto_id"], "nombre": r["nombre"],
                "precio": r["precio"], "costo": r["costo"],
                "categoria": r["categoria"], "um": r["unidad_medida"],
                "imagen": r["imagen"], "onSale": bool(r["en_oferta"]),
                "activo": bool(r["activo"]),
            })
        conn.close()
        return jsonify({"ok": True, "productos": productos})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/productos/crear", methods=["POST"])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_crear_producto():
    from db_connection import obtener_conexion
    import uuid
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre obligatorio"}), 400
    producto_id = datos.get("id") or f"prod-{uuid.uuid4().hex[:8]}"
    precio = float(datos.get("precio") or 0)
    costo = float(datos.get("costo") or datos.get("costoUnitario") or 0)
    categoria = datos.get("categoria") or "General"
    um = datos.get("um") or datos.get("unidad_medida") or "Unidad"
    imagen = datos.get("imagen") or ""
    en_oferta = 1 if datos.get("onSale") else 0
    try:
        conn = obtener_conexion()
        existing = conn.execute(
            "SELECT producto_id FROM productos WHERE producto_id = ?", (producto_id,)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({"ok": False, "error": "Producto ya existe"}), 400
        conn.execute(
            "INSERT INTO productos "
            "(producto_id, nombre, precio, costo, categoria, unidad_medida, "
            "en_oferta, imagen, activo) VALUES (?,?,?,?,?,?,?,?,?)",
            (producto_id, nombre, precio, costo, categoria, um, en_oferta, imagen, 1)
        )
        conn.execute(
            "INSERT OR IGNORE INTO inventario_general "
            "(producto_id, nombre, stock_actual, stock_minimo, precio_compra, "
            "precio_venta, categoria, unidad_medida, actualizado) "
            "VALUES (?, ?, 0, 5, ?, ?, ?, ?, datetime('now'))",
            (producto_id, nombre, costo, precio, categoria, um)
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "producto_id": producto_id, "mensaje": f"Producto '{nombre}' creado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/productos/<producto_id>", methods=["DELETE"])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_eliminar_producto(producto_id):
    from db_connection import obtener_conexion
    try:
        conn = obtener_conexion()
        result = conn.execute("UPDATE productos SET activo = 0 WHERE producto_id = ?", (producto_id,))
        conn.commit()
        conn.close()
        if result.rowcount == 0:
            return jsonify({"ok": False, "error": "Producto no encontrado"}), 404
        return jsonify({"ok": True, "mensaje": f"Producto {producto_id} eliminado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/productos/<producto_id>", methods=["PUT"])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_actualizar_producto(producto_id):
    from db_connection import obtener_conexion
    datos = request.get_json(silent=True) or {}
    try:
        conn = obtener_conexion()
        campos, valores = [], []
        for campo_db, campo_json in [("nombre","nombre"),("precio","precio"),("costo","costo"),("categoria","categoria"),("unidad_medida","um"),("imagen","imagen"),("en_oferta","onSale")]:
            if campo_json in datos:
                val = datos[campo_json]
                if campo_json == "onSale": val = 1 if val else 0
                campos.append(f"{campo_db} = ?")
                valores.append(val)
        if not campos:
            return jsonify({"ok": False, "error": "Nada que actualizar"}), 400
        valores.append(producto_id)
        conn.execute(f"UPDATE productos SET {', '.join(campos)} WHERE producto_id = ?", valores)
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": f"Producto {producto_id} actualizado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/categorias", methods=["GET"])
@login_required
def api_listar_categorias_admin():
    from db_connection import obtener_conexion
    try:
        conn = obtener_conexion()
        cursor = conn.execute(
            "SELECT categoria, COUNT(*) as total, SUM(CASE WHEN activo=1 THEN 1 ELSE 0 END) as activos FROM productos GROUP BY categoria ORDER BY categoria"
        )
        categorias = [{"nombre": r["categoria"], "total": r["total"], "activos": r["activos"]} for r in cursor.fetchall()]
        conn.close()
        return jsonify({"ok": True, "categorias": categorias})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/categorias/crear", methods=["POST"])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_crear_categoria():
    from db_connection import obtener_conexion
    import uuid
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre obligatorio"}), 400
    try:
        conn = obtener_conexion()
        existing = conn.execute("SELECT COUNT(*) as c FROM productos WHERE categoria = ?", (nombre,)).fetchone()
        if existing["c"] > 0:
            conn.close()
            return jsonify({"ok": False, "error": "Categoría ya existe"}), 400
        producto_id = f"cat-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT INTO productos (producto_id, nombre, precio, costo, categoria, unidad_medida, en_oferta, imagen, activo) VALUES (?,?,?,?,?,?,?,?,?)",
            (producto_id, f"[Categoría: {nombre}]", 0, 0, nombre, "Unidad", 0, "", 0)
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "categoria": nombre, "mensaje": f"Categoría '{nombre}' creada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@catalogo_bp.route("/nomenclador", methods=["GET"])
@login_required
def api_nomenclador():
    nomencladores = {
        "USD": [100, 50, 20, 10, 5, 1],
        "EUR": [100, 50, 20, 10, 5],
        "CUP": [1000, 500, 200, 100, 50, 20, 10, 5, 1],
        "MXN": [500, 200, 100, 50, 20, 10, 5, 2, 1],
    }
    return jsonify({"ok": True, "nomencladores": nomencladores, "default": "USD"})


@catalogo_bp.route("/catalogo/sync", methods=["POST"])
@login_required
def api_catalogo_sync():
    from db_connection import obtener_conexion
    datos = request.get_json(silent=True) or {}
    productos = datos.get("productos", [])
    if not productos:
        return jsonify({"ok": False, "error": "No hay productos"}), 400
    try:
        conn = obtener_conexion()
        for p in productos:
            pid = p.get("id") or p.get("producto_id")
            if not pid: continue
            conn.execute(
                "INSERT OR REPLACE INTO productos (producto_id, nombre, precio, costo, categoria, unidad_medida, en_oferta, imagen, activo) VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, p.get("nombre",""), float(p.get("precio",0)), float(p.get("costo",0)), p.get("categoria","General"), p.get("um","Unidad"), 1 if p.get("onSale") else 0, p.get("imagen",""), 1)
            )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": f"{len(productos)} productos sincronizados"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
