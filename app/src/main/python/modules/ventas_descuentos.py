from db_connection import obtener_conexion
from flask import request
from auth_decorator import login_required
from modules.ventas_helpers import ventas_bp, request, jsonify, requiere_login, requiere_rol, agregar_log, obtener_conexion
# ══════════════════════════════════════════════════════════════
#  DESCUENTOS
# ══════════════════════════════════════════════════════════════

@ventas_bp.route("/api/descuentos", methods=["GET"])
@login_required
def api_listar_descuentos():
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT * FROM descuentos_config WHERE activo=1 ORDER BY nombre"
        ).fetchall()
        conn.close()
        return jsonify({"ok": True, "descuentos": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@ventas_bp.route("/api/descuentos", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_crear_descuento():
    try:
        d = request.get_json(force=True, silent=True) or {}
        nombre = d.get("nombre", "Descuento").strip()
        tipo = d.get("tipo", "porcentaje")
        valor = float(d.get("valor", 0))
        if tipo not in ("porcentaje", "fijo") or valor < 0:
            return jsonify({"ok": False, "error": "Parametros invalidos"}), 400
        conn = obtener_conexion()
        cur = conn.execute(
            "INSERT INTO descuentos_config(nombre,tipo,valor) VALUES(?,?,?)",
            (nombre, tipo, valor)
        )
        conn.commit(); conn.close()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@ventas_bp.route("/api/descuentos/<int:did>", methods=["DELETE"])
@requiere_rol("administrador", "desarrollador")
def api_eliminar_descuento(did):
    try:
        conn = obtener_conexion()
        conn.execute("UPDATE descuentos_config SET activo=0 WHERE id=?", (did,))
        conn.commit(); conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

