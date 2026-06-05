from db_connection import obtener_conexion
from flask import Blueprint, jsonify, request
import uuid

tienda_tiendas_bp = Blueprint('tienda_tiendas', __name__)

@tienda_tiendas_bp.route('/api/tiendas', methods=['GET'])
def api_listar_tiendas():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tiendas WHERE activo=1")
        tiendas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"ok": True, "tiendas": tiendas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
