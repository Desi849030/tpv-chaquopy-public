# -*- coding: utf-8 -*-
"""publico_bp.py v8.9 - Endpoints públicos + identidad anónima persistente."""

from flask import Blueprint, jsonify, request, session

from anon_identity import identity_payload, meta_payload

publico_bp = Blueprint('publico', __name__)


def _get_db():
    from db_connection import obtener_conexion
    return obtener_conexion()


def _ok(payload: dict, status: int = 200):
    payload = dict(payload or {})
    payload.setdefault("ok", True)
    payload.setdefault("meta", meta_payload(request, session))
    return jsonify(payload), status


def _err(error: str, extra=None, status: int = 200):
    payload = {"ok": False, "error": error, "meta": meta_payload(request, session)}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


@publico_bp.route('/api/publico/identity', methods=['GET'])
def api_publico_identity():
    """Devuelve identidad persistente del visitante anónimo o usuario actual."""
    return jsonify(identity_payload(request, session))


@publico_bp.route('/api/publico/catalogo', methods=['GET'])
def api_publico_catalogo():
    """Catálogo público de productos activos."""
    try:
        conn = _get_db()
        rows = conn.execute(
            """
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
            """
        ).fetchall()
        conn.close()
        return _ok({"total": len(rows), "productos": [dict(r) for r in rows]})
    except Exception as e:
        return _err(str(e), {"productos": []})


@publico_bp.route('/api/publico/buscar', methods=['GET'])
def api_publico_buscar():
    """Busca productos por nombre/categoría. Ej: ?q=cafe."""
    q = (request.args.get('q', '') or '').strip()
    if not q or len(q) < 2:
        return _err("Consulta muy corta", {"productos": []})
    try:
        conn = _get_db()
        like = "%" + q + "%"
        rows = conn.execute(
            """
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
            """,
            (like, like, q, q + "%"),
        ).fetchall()
        conn.close()
        return _ok({"consulta": q, "total": len(rows), "productos": [dict(r) for r in rows]})
    except Exception as e:
        return _err(str(e), {"productos": []})


@publico_bp.route('/api/publico/ofertas', methods=['GET'])
def api_publico_ofertas():
    """Productos en oferta."""
    try:
        conn = _get_db()
        rows = conn.execute(
            """
            SELECT p.producto_id as id, p.nombre, p.precio, p.categoria,
                   p.unidad_medida as unidad,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1 AND COALESCE(p.en_oferta, 0) = 1
            ORDER BY p.precio
            LIMIT 30
            """
        ).fetchall()
        conn.close()
        return _ok({"total": len(rows), "ofertas": [dict(r) for r in rows]})
    except Exception as e:
        return _err(str(e), {"ofertas": []})


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
            (producto_id,),
        ).fetchone()
        if not producto:
            conn.close()
            return _err("Producto no encontrado", status=404)

        inv = conn.execute(
            "SELECT stock_actual, stock_minimo FROM inventario_general WHERE producto_id = ?",
            (producto_id,),
        ).fetchone()
        stock = int(inv['stock_actual']) if inv else 0
        conn.close()

        return _ok({
            "producto": dict(producto),
            "stock_disponible": stock,
            "disponible": stock > 0,
        })
    except Exception as e:
        return _err(str(e))


@publico_bp.route('/api/publico/categorias', methods=['GET'])
def api_publico_categorias():
    """Lista de categorías con conteo."""
    try:
        conn = _get_db()
        rows = conn.execute(
            """
            SELECT categoria, COUNT(*) as total
            FROM productos
            WHERE COALESCE(activo, 1) = 1 AND categoria IS NOT NULL
              AND categoria != ''
            GROUP BY categoria
            ORDER BY total DESC
            """
        ).fetchall()
        conn.close()
        return _ok({"total": len(rows), "categorias": [dict(r) for r in rows]})
    except Exception as e:
        return _err(str(e), {"categorias": []})


@publico_bp.route('/api/publico/categoria/<nombre>', methods=['GET'])
def api_publico_categoria(nombre):
    """Productos de una categoría específica."""
    try:
        conn = _get_db()
        rows = conn.execute(
            """
            SELECT p.producto_id as id, p.nombre, p.precio,
                   p.unidad_medida as unidad,
                   COALESCE(p.en_oferta, 0) as oferta,
                   COALESCE(i.stock_actual, 0) as stock_total
            FROM productos p
            LEFT JOIN inventario_general i ON i.producto_id = p.producto_id
            WHERE COALESCE(p.activo, 1) = 1
              AND LOWER(p.categoria) = LOWER(?)
            ORDER BY p.nombre
            """,
            (nombre,),
        ).fetchall()
        conn.close()
        return _ok({"categoria": nombre, "total": len(rows), "productos": [dict(r) for r in rows]})
    except Exception as e:
        return _err(str(e), {"productos": []})


@publico_bp.route('/api/publico/tiendas-info', methods=['GET'])
def api_publico_tiendas_info():
    """Info pública (al no haber tabla tiendas, devuelve info estática)."""
    return _ok({
        "total": 1,
        "tiendas": [{
            "nombre": "Tienda Principal",
            "direccion": "Consulta horarios y dirección con el personal",
            "horario": "08:00 - 20:00",
            "telefono": "",
        }],
    })
