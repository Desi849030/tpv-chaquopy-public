from auth_decorator import login_required
from database import obtener_conexion
from routes.ventas_helpers import ventas_bp, request, jsonify, requiere_login, requiere_rol, usuario_actual, datetime, consultar_ventas_por_fecha, consultar_resumen_ventas, consultar_ganancias_por_dia, _sb
# ══════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════

@login_required
@ventas_bp.route("/api/reportes/ventas", methods=["GET"])
@requiere_login
def api_reporte_ventas():
    u = usuario_actual()
    fecha_inicio = request.args.get("desde", "2000-01-01")
    fecha_fin = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify({"ventas": consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vid)})

@login_required
@ventas_bp.route("/api/reportes/resumen", methods=["GET"])
@requiere_login
def api_resumen():
    u = usuario_actual()
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify(consultar_resumen_ventas(vid))

@login_required
@ventas_bp.route("/api/reportes/ganancias", methods=["GET"])
@requiere_rol("administrador","desarrollador","supervisor")
def api_ganancias():
    return jsonify({"ganancias": consultar_ganancias_por_dia()})


@login_required
@ventas_bp.route("/api/dashboard/data", methods=["GET"])
@requiere_login
def api_dashboard_data():
    from datetime import datetime, timedelta
    conn = obtener_conexion()
    hoy = datetime.now().strftime("%Y-%m-%d")
    try:
        kpi = conn.execute(
            "SELECT COUNT(*) tx, COALESCE(SUM(total),0) ingresos, "
            "COALESCE(AVG(total),0) ticket, "
            "COALESCE(SUM(cantidad*precio_unit),0) costo "
            "FROM historial_ventas WHERE DATE(fecha)=?", (hoy,)
        ).fetchone()
        kpi_dict = {"tx": kpi[0], "ingresos": float(kpi[1]),
                     "ticket": float(kpi[2]), "costo": float(kpi[3])}
        dias7 = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            r = conn.execute(
                "SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=?", (d,)
            ).fetchone()
            dias7.append({"fecha": d, "total": float(r[0])})
        return jsonify({"ok": True, "kpi": kpi_dict, "dias7": dias7})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
