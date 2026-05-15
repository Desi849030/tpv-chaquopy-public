from routes.ventas_helpers import ventas_bp, uuid, request, jsonify, requiere_login, usuario_actual, agregar_log, datetime, obtener_conexion, _sb
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

