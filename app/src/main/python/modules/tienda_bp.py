# -*- coding: utf-8 -*-
"""Blueprint: Tienda — rutas mínimas para evitar 404"""
from flask import Blueprint, jsonify, request

tienda_bp = Blueprint('tienda', __name__)


@tienda_bp.route('/api/tiendas')
def api_tiendas():
    """Lista tiendas configuradas."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        try:
            rows = conn.execute("SELECT * FROM tiendas ORDER BY nombre LIMIT 20").fetchall()
            tiendas = [dict(r) for r in rows]
        except Exception:
            tiendas = []
        conn.close()
        return jsonify({"ok": True, "tiendas": tiendas})
    except Exception:
        return jsonify({"ok": True, "tiendas": []})


@tienda_bp.route('/api/tiendas', methods=['POST'])
def api_crear_tienda():
    """Crear/actualizar tienda."""
    d = request.get_json(silent=True) or {}
    nombre = d.get('nombre', '').strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400
    try:
        from db_connection import obtener_conexion
        import uuid
        conn = obtener_conexion()
        tid = f"tienda-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT OR REPLACE INTO tiendas (tienda_id, nombre, direccion, telefono) "
            "VALUES (?, ?, ?, ?)",
            (tid, nombre, d.get('direccion', ''), d.get('telefono', '')))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "tienda_id": tid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
