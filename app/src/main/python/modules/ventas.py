"""
╔══════════════════════════════════════════════════════════════╗
║   ventas.py  —  TPV ULTRA SMART  v7.0 (COMPLETO)           ║
║   Ventas, gastos, cierres y reportes                        ║
╚══════════════════════════════════════════════════════════════╝
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta
from decorators import login_required, requiere_rol, usuario_actual
from database import (
    consultar_ventas_por_fecha, consultar_resumen_ventas, 
    consultar_ganancias_por_dia, obtener_conexion, agregar_log,
    obtener_historial_cierres
)

ventas_bp = Blueprint('ventas', __name__, url_prefix='/api')




# ══════════════════════════════════════════════════════════════
# GASTOS
# ══════════════════════════════════════════════════════════════
@ventas_bp.route("/gastos", methods=["GET"])
@login_required
def api_gastos():
    u = usuario_actual()
    if u["rol"] not in ("desarrollador", "administrador", "supervisor"):
        return jsonify({"error": "Sin permisos"}), 403
    desde = request.args.get("desde", "2000-01-01")
    hasta = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    conn = obtener_conexion()
    try:
        rows = conn.execute(
            "SELECT gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por, creado_en "
            "FROM gastos WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC",
            (desde, hasta)
        ).fetchall()
        return jsonify({"gastos": [dict(r) for r in rows]})
    finally:
        conn.close()

@ventas_bp.route("/gastos", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_crear_gasto():
    u = usuario_actual()
    datos = request.get_json(force=True, silent=True) or {}
    descripcion = datos.get("descripcion", "").strip()
    monto = float(datos.get("monto", 0))
    categoria = datos.get("categoria", "Otros")
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    nota = datos.get("nota", "").strip()
    
    if not descripcion or monto <= 0:
        return jsonify({"error": "Descripción y monto > 0 son obligatorios"}), 400
    
    import uuid
    gasto_id = f"gst-{uuid.uuid4().hex[:8]}"
    conn = obtener_conexion()
    try:
        conn.execute(
            "INSERT INTO gastos (gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (gasto_id, descripcion, monto, categoria, fecha, nota, u["usuario_id"])
        )
        conn.commit()
        agregar_log(f"Gasto ${monto:.2f} '{descripcion}' por {u['usuario_id']}", "info")
        return jsonify({"ok": True, "gasto_id": gasto_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@ventas_bp.route("/gastos/<gasto_id>", methods=["DELETE"])
@requiere_rol("administrador", "desarrollador")
def api_eliminar_gasto(gasto_id):
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
# CIERRES DE CAJA
# ══════════════════════════════════════════════════════════════
@ventas_bp.route("/cierres", methods=["GET"])
@login_required
def api_cierres():
    u = usuario_actual()
    desde = request.args.get("desde", "2000-01-01")
    hasta = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    conn = obtener_conexion()
    try:
        if u["rol"] == "vendedor":
            rows = conn.execute(
                "SELECT * FROM cierres_diario WHERE vendedor_id = ? AND fecha BETWEEN ? AND ? ORDER BY fecha DESC",
                (u["usuario_id"], desde, hasta)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM cierres_diario WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC",
                (desde, hasta)
            ).fetchall()
        return jsonify({"cierres": [dict(r) for r in rows]})
    finally:
        conn.close()

@ventas_bp.route("/cierres/cerrar-dia", methods=["POST"])
@login_required
def api_cerrar_dia():
    """Cierra el día actual para el vendedor o admin."""
    u = usuario_actual()
    datos = request.get_json(force=True, silent=True) or {}
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    items = datos.get("items", [])  # [{producto_id, cant_final, ...}]
    
    conn = obtener_conexion()
    try:
        # Calcular totales
        total_ventas = sum(float(i.get("importe", 0)) for i in items)
        total_costo = sum(float(i.get("precio_costo", 0) * i.get("vendido", 0)) for i in items)
        ganancia = total_ventas - total_costo
        
        # Guardar cierre
        conn.execute(
            "INSERT OR REPLACE INTO cierres_diario "
            "(vendedor_id, fecha, total_ventas, total_costo, ganancia_neta, items_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (u["usuario_id"], fecha, total_ventas, total_costo, ganancia, 
             json.dumps(items, ensure_ascii=False))
        )
        conn.commit()
        agregar_log(f"Cierre día {fecha} por {u['usuario_id']}: ${total_ventas:.2f}", "info")
        return jsonify({"ok": True, "mensaje": f"Día {fecha} cerrado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
# REPORTES
# ══════════════════════════════════════════════════════════════
@ventas_bp.route("/reportes/ventas", methods=["GET"])
@login_required
def api_reporte_ventas():
    u = usuario_actual()
    desde = request.args.get("desde", "2000-01-01")
    hasta = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    vendedor_id = u["usuario_id"] if u["rol"] == "vendedor" else request.args.get("vendedor_id")
    
    ventas = consultar_ventas_por_fecha(desde, hasta, vendedor_id)
    return jsonify({"ventas": ventas, "total": len(ventas)})

@ventas_bp.route("/reportes/resumen", methods=["GET"])
@login_required
def api_resumen_ventas():
    u = usuario_actual()
    vendedor_id = u["usuario_id"] if u["rol"] == "vendedor" else None
    resumen = consultar_resumen_ventas(vendedor_id)
    return jsonify(resumen)

@ventas_bp.route("/reportes/ganancias", methods=["GET"])
@requiere_rol("administrador", "desarrollador", "supervisor")
def api_ganancias():
    ganancias = consultar_ganancias_por_dia()
    return jsonify({"ganancias": ganancias})
