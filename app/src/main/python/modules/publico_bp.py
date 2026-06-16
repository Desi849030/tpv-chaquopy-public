# -*- coding: utf-8 -*-
"""publico_bp.py v8.8 - Endpoints publicos adaptados al esquema real.

Esquema confirmado:
- productos: id(INT), producto_id(TEXT), nombre, precio, costo, categoria,
             unidad_medida, en_oferta, imagen, activo, creado
- inventario_general: id, producto_id, nombre, stock_actual, stock_minimo,
                      precio_compra, precio_venta, categoria, unidad_medida
- (no hay tabla tiendas)
"""

from flask import Blueprint, jsonify, request

publico_bp = Blueprint('publico', __name__)


def _get_db():
    from db_connection import obtener_conexion
    return obtener_conexion()


@publico_bp.route('/api/publico/catalogo', methods=['GET'])
def api_publico_catalogo():
    """Catalogo publico de productos activos."""
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT p.producto_id as id, p.nombre, p.precio, p.categoria,
                   p.unidad_medida as unidad,
                   COALESCE(p.imagen, '') as imagen,
                   COALESCE(p.en_oferta, 0) as oferta,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
            ORDER BY p.nombre
            LIMIT 200
        """).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "total": len(rows),
            "productos": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "productos": []})


@publico_bp.route('/api/publico/buscar', methods=['GET'])
def api_publico_buscar():
    """Busca productos por nombre/categoria. Ej: ?q=cafe"""
    q = (request.args.get('q', '') or '').strip()
    if not q or len(q) < 2:
        return jsonify({"ok": False, "error": "Consulta muy corta", "productos": []})
    try:
        conn = _get_db()
        like = "%" + q + "%"
        rows = conn.execute("""
            SELECT p.producto_id as id, p.nombre, p.precio, p.categoria,
                   p.unidad_medida as unidad,
                   COALESCE(p.en_oferta, 0) as oferta,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
              AND (LOWER(p.nombre) LIKE LOWER(?) OR LOWER(p.categoria) LIKE LOWER(?))
            ORDER BY
              CASE WHEN LOWER(p.nombre) = LOWER(?) THEN 0
                   WHEN LOWER(p.nombre) LIKE LOWER(?) THEN 1
                   ELSE 2 END,
              p.nombre
            LIMIT 20
        """, (like, like, q, q + "%")).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "consulta": q,
            "total": len(rows),
            "productos": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "productos": []})


@publico_bp.route('/api/publico/ofertas', methods=['GET'])
def api_publico_ofertas():
    """Productos en oferta."""
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT p.producto_id as id, p.nombre, p.precio, p.categoria,
                   p.unidad_medida as unidad,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1 AND COALESCE(p.en_oferta, 0) = 1
            ORDER BY p.precio
            LIMIT 30
        """).fetchall()
        conn.close()
        return jsonify({"ok": True, "total": len(rows),
                        "ofertas": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "ofertas": []})


@publico_bp.route('/api/publico/producto/<producto_id>', methods=['GET'])
def api_publico_producto_detalle(producto_id):
    """Detalle de un producto + stock disponible."""
    try:
        conn = _get_db()
        producto = conn.execute(
            "SELECT producto_id as id, nombre, precio, categoria, "
            "unidad_medida as unidad, COALESCE(imagen,'') as imagen, "
            "COALESCE(en_oferta, 0) as oferta "
            "FROM productos WHERE producto_id = ? AND COALESCE(activo,1)=1",
            (producto_id,)
        ).fetchone()
        if not producto:
            conn.close()
            return jsonify({"ok": False, "error": "Producto no encontrado"}), 404

        inv = conn.execute(
            "SELECT stock_actual, stock_minimo "
            "FROM inventario_general WHERE producto_id = ?",
            (producto_id,)
        ).fetchone()
        stock = int(inv['stock_actual']) if inv else 0
        conn.close()

        return jsonify({
            "ok": True,
            "producto": dict(producto),
            "stock_disponible": stock,
            "disponible": stock > 0
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@publico_bp.route('/api/publico/categorias', methods=['GET'])
def api_publico_categorias():
    """Lista de categorias con conteo."""
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT categoria, COUNT(*) as total
            FROM productos
            WHERE COALESCE(activo, 1) = 1 AND categoria IS NOT NULL
              AND categoria != ''
            GROUP BY categoria
            ORDER BY total DESC
        """).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "total": len(rows),
            "categorias": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "categorias": []})


@publico_bp.route('/api/publico/categoria/<nombre>', methods=['GET'])
def api_publico_categoria(nombre):
    """Productos de una categoria especifica."""
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT p.producto_id as id, p.nombre, p.precio,
                   p.unidad_medida as unidad,
                   COALESCE(p.en_oferta, 0) as oferta,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
              AND LOWER(p.categoria) = LOWER(?)
            ORDER BY p.nombre
        """, (nombre,)).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "categoria": nombre,
            "total": len(rows),
            "productos": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "productos": []})


@publico_bp.route('/api/publico/tiendas-info', methods=['GET'])
def api_publico_tiendas_info():
    """Info publica (al no haber tabla tiendas, devuelve info estatica)."""
    return jsonify({
        "ok": True,
        "total": 1,
        "tiendas": [{
            "nombre": "Tienda Principal",
            "direccion": "Consulta horarios y dirección con el personal",
            "horario": "08:00 - 20:00",
            "telefono": ""
        }]
    })
