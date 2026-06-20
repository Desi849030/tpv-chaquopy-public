# -*- coding: utf-8 -*-
"""Blueprint: Tienda — CRUD de sucursales."""
from flask import Blueprint, jsonify, request
from decorators import login_required, requiere_rol, usuario_actual

tienda_bp = Blueprint('tienda', __name__)


def _asegurar_tabla_tiendas(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tiendas (
            tienda_id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            horario TEXT,
            activo INTEGER DEFAULT 1,
            creado TEXT
        )
    """)


@tienda_bp.route('/api/tiendas')
def api_tiendas():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        _asegurar_tabla_tiendas(conn)
        count = conn.execute("SELECT COUNT(*) FROM tiendas").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO tiendas (tienda_id, nombre, direccion, telefono, horario, activo, creado) VALUES (?, ?, ?, ?, ?, 1, datetime('now'))",
                ("tnd-default", "Tienda Principal", "Calle Principal #123", "+1234567890", "08:00 - 20:00")
            )
            conn.commit()
        rows = conn.execute("SELECT tienda_id, nombre, direccion, telefono, horario, activo, creado FROM tiendas WHERE activo = 1 ORDER BY nombre LIMIT 20").fetchall()
        tiendas = [dict(r) for r in rows]
        conn.close()
        return jsonify({"ok": True, "tiendas": tiendas})
    except Exception as e:
        return jsonify({"ok": True, "tiendas": [], "error": str(e)})


@tienda_bp.route('/api/tiendas', methods=['POST'])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_crear_tienda():
    from db_connection import obtener_conexion
    import uuid
    d = request.get_json(silent=True) or {}
    nombre = d.get('nombre', '').strip()
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400
    tienda_id = f"tnd-{uuid.uuid4().hex[:8]}"
    try:
        conn = obtener_conexion()
        _asegurar_tabla_tiendas(conn)
        conn.execute(
            "INSERT INTO tiendas (tienda_id, nombre, direccion, telefono, horario, activo, creado) VALUES (?, ?, ?, ?, ?, 1, datetime('now'))",
            (tienda_id, nombre, d.get('direccion', ''), d.get('telefono', ''), d.get('horario', '08:00 - 20:00'))
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "tienda_id": tienda_id, "mensaje": f"Tienda '{nombre}' creada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@tienda_bp.route('/api/tiendas/<tienda_id>', methods=['DELETE'])
@login_required
@requiere_rol("administrador", "desarrollador")
def api_eliminar_tienda(tienda_id):
    from db_connection import obtener_conexion
    try:
        conn = obtener_conexion()
        _asegurar_tabla_tiendas(conn)
        result = conn.execute("UPDATE tiendas SET activo = 0 WHERE tienda_id = ?", (tienda_id,))
        conn.commit()
        conn.close()
        if result.rowcount == 0:
            return jsonify({"ok": False, "error": "Tienda no encontrada"}), 404
        return jsonify({"ok": True, "mensaje": f"Tienda {tienda_id} eliminada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
