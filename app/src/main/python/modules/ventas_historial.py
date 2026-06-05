from flask import request
from auth_decorator import login_required
from modules.ventas_helpers import ventas_bp, datetime, request, jsonify, requiere_login, usuario_actual, guardar_historial_diario_local, obtener_historial_diario_local, obtener_historial_detalle_local, guardar_historial_diario, obtener_historial_diario, obtener_historial_detalle, obtener_config_actual, verificar_tablas_supabase, obtener_sql_completo, setup_supabase, _sb
# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO
# ══════════════════════════════════════════════════════════════

@login_required
@ventas_bp.route("/api/historial/diario", methods=["GET"])
@requiere_login
def api_historial_get():
    limite = int(request.args.get("limite", 30))
    try:
        res_sb = obtener_historial_diario(limite=limite)
        if res_sb.get("ok") and res_sb.get("historial"):
            return jsonify({"ok": True, "historial": res_sb["historial"], "fuente": "supabase"})
        historial_local = obtener_historial_diario_local(limite=limite)
        return jsonify({"ok": True, "historial": historial_local, "fuente": "local"})
    except Exception as e:
        return jsonify({"ok": False, "historial": [], "mensaje": str(e)}), 500

@login_required
@ventas_bp.route("/api/historial/diario", methods=["POST"])
@requiere_login
def api_historial_post():
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    datos = request.get_json(force=True) or {}
    try:
        ok_local = guardar_historial_diario_local(datos)
        ok_sb = guardar_historial_diario(datos)
        return jsonify({
            "ok": ok_local or ok_sb.get("ok", False),
            "local": ok_local,
            "supabase": ok_sb.get("ok", False),
            "mensaje": f"Snapshot {datos.get('fecha','?')} guardado",
        })
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@login_required
@ventas_bp.route("/api/historial/diario/<fecha>", methods=["GET"])
@requiere_login
def api_historial_detalle(fecha):
    try:
        res_sb = obtener_historial_detalle(fecha)
        if res_sb.get("ok"):
            return jsonify(res_sb)
        local = obtener_historial_detalle_local(fecha)
        if local:
            return jsonify({"ok": True, "dia": local, "fuente": "local"})
        return jsonify({"ok": False, "mensaje": f"Sin historial para {fecha}"}), 404
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500
