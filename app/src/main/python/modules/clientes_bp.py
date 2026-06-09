# -*- coding: utf-8 -*-
"""Blueprint: Clientes"""
from flask import Blueprint, request, jsonify
import uuid

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/api/clientes/registrar', methods=['POST'])
def registrar_cliente():
    d = request.get_json(silent=True) or {}
    nombre = d.get('nombre', '').strip()
    telefono = d.get('telefono', '')
    email = d.get('email', '')
    if not nombre:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        cid = f"cli-{uuid.uuid4().hex[:8]}"
        c.execute(
            "INSERT INTO clientes (cliente_id,nombre,telefono,email) VALUES (?,?,?,?)",
            (cid, nombre, telefono, email),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "cliente_id": cid, "nombre": nombre})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@clientes_bp.route('/api/clientes')
def listar_clientes():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT cliente_id,nombre,telefono,email FROM clientes ORDER BY nombre LIMIT 50")
        clientes = [{"id": r[0], "nombre": r[1], "telefono": r[2], "email": r[3]}
                     for r in c.fetchall()]
        conn.close()
        return jsonify({"ok": True, "clientes": clientes})
    except Exception:
        return jsonify({"ok": True, "clientes": []})
