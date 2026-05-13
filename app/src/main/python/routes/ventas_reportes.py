from routes.ventas_helpers import ventas_bp, request, jsonify, requiere_login, requiere_rol, usuario_actual, consultar_ventas_por_fecha, consultar_resumen_ventas, consultar_ganancias_por_dia, _sb
# ══════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════

@ventas_bp.route("/api/reportes/ventas", methods=["GET"])
@requiere_login
def api_reporte_ventas():
    u = usuario_actual()
    fecha_inicio = request.args.get("desde", "2000-01-01")
    fecha_fin = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify({"ventas": consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vid)})

@ventas_bp.route("/api/reportes/resumen", methods=["GET"])
@requiere_login
def api_resumen():
    u = usuario_actual()
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify(consultar_resumen_ventas(vid))

@ventas_bp.route("/api/reportes/ganancias", methods=["GET"])
@requiere_rol("administrador","desarrollador","supervisor")
def api_ganancias():
    return jsonify({"ganancias": consultar_ganancias_por_dia()})

