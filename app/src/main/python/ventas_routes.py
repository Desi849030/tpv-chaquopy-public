"""Rutas de ventas, gastos, reportes, descuentos e historial diario"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    agregar_log, obtener_conexion,
    consultar_ventas_por_fecha, consultar_resumen_ventas,
    consultar_ganancias_por_dia,
    guardar_historial_diario_local, obtener_historial_diario_local,
    obtener_historial_detalle_local,
)
from supabase_sync import (
    guardar_historial_diario, obtener_historial_diario,
    obtener_historial_detalle, obtener_config_actual,
    verificar_tablas_supabase, obtener_sql_completo, setup_supabase,
)
import supabase_sync as _sb

ventas_bp = Blueprint('ventas', __name__)

# ══════════════════════════════════════════════════════════════
#  GASTOS / INVERSIÓN
# ══════════════════════════════════════════════════════════════

@ventas_bp.route("/api/gastos", methods=["GET"])
@requiere_login
def api_listar_gastos():
    u = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador","supervisor"):
        return jsonify({"error": "Sin permisos"}), 403
    desde = request.args.get("desde", "2000-01-01")
    hasta = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por, creado_en
            FROM gastos WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC
        """, (desde, hasta)).fetchall()
        return jsonify({"gastos": [dict(r) for r in rows]})
    finally:
        conn.close()

@ventas_bp.route("/api/gastos", methods=["POST"])
@requiere_login
def api_crear_gasto():
    u = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador"):
        return jsonify({"error": "Solo Admin/Dev puede registrar gastos"}), 403
    datos = request.get_json(force=True, silent=True) or {}
    descripcion = datos.get("descripcion","").strip()
    monto = float(datos.get("monto", 0))
    categoria = datos.get("categoria","Otros")
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    nota = datos.get("nota","").strip()
    if not descripcion:
        return jsonify({"error": "Descripcion obligatoria"}), 400
    if monto <= 0:
        return jsonify({"error": "El monto debe ser mayor a 0"}), 400
    gasto_id = "gst-" + uuid.uuid4().hex[:8]
    conn = obtener_conexion()
    try:
        conn.execute("""
            INSERT INTO gastos (gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (gasto_id, descripcion, monto, categoria, fecha, nota, u["usuario_id"]))
        conn.commit()
        agregar_log(f"Gasto ${monto:.2f} '{descripcion}' por {u['usuario_id']}", "info")
        return jsonify({"ok": True, "gasto_id": gasto_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@ventas_bp.route("/api/gastos/<gasto_id>", methods=["DELETE"])
@requiere_login
def api_eliminar_gasto(gasto_id):
    u = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador"):
        return jsonify({"error": "Sin permisos"}), 403
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM gastos WHERE gasto_id = ?", (gasto_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

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

# ══════════════════════════════════════════════════════════════
#  DESCUENTOS
# ══════════════════════════════════════════════════════════════

@ventas_bp.route("/api/descuentos", methods=["GET"])
@requiere_login
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

# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO
# ══════════════════════════════════════════════════════════════

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
