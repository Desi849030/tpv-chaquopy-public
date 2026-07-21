"""
api_routes.py — Solo las 2 rutas que faltan en app.py (1271 lineas)
/api/health y /api/config/publica — NO requieren login
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import obtener_info_db, obtener_conexion
from version import __version__

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/health", methods=["GET"])
def api_health():
    try:
        info = obtener_info_db()
        return jsonify({
            "ok": True,
            "version": __version__,
            "timestamp": datetime.now().isoformat(),
            "db_info": {
                "archivo": info.get("archivo", ""),
                "tamano_kb": info.get("tamano_kb", 0),
                "tablas": info.get("tablas", {}),
            }
        })
    except Exception as e:
        return jsonify({"ok": True, "version": __version__, "error": str(e)})

@api_bp.route("/api/config/publica", methods=["GET"])
def api_config_publica():
    try:
        conn = obtener_conexion()
        try:
            row = conn.execute(
                "SELECT valor FROM app_state WHERE clave = ?",
                ("config_tienda",)
            ).fetchone()
            if row:
                return jsonify({"ok": True, "config": json.loads(row["valor"])})
            row2 = conn.execute(
                "SELECT valor FROM app_state WHERE clave = ?",
                ("estado_tpv",)
            ).fetchone()
            if row2:
                estado = json.loads(row2["valor"])
                cfg = estado.get("configuracion", {})
                return jsonify({
                    "ok": True,
                    "config": {
                        "nombreTienda": cfg.get("nombreTienda", "Mi Tienda"),
                        "moneda": cfg.get("moneda", "$"),
                        "mensaje": cfg.get("mensaje", ""),
                    }
                })
            return jsonify({"ok": True, "config": {"nombreTienda": "Mi Tienda", "moneda": "$"}})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
