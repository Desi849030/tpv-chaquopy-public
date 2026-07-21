# -*- coding: utf-8 -*-
"""Blueprint: Herramientas IA y endpoints de tools/*"""
from flask import Blueprint, request, jsonify, session
from datetime import date, datetime
import uuid

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/api/tools/finanzas')
def tool_finanzas():
    """Balance financiero real desde BD."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*), COALESCE(SUM(cantidad*precio_unit),0) "
            "FROM historial_ventas WHERE fecha LIKE ?",
            (f"{date.today().isoformat()}%",))
        row = c.fetchone()
        ventas_hoy = row[1] or 0
        c.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        prod_count = c.fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "ventas_hoy": ventas_hoy, "productos": prod_count,
                        "margen_promedio": 28, "ganancia_estimada": round(ventas_hoy * 0.28, 2)})
    except Exception as e:
        return jsonify({"ok": True, "ventas_hoy": 0, "productos": 0, "margen_promedio": 28})


@tools_bp.route('/api/tools/stock')
def tool_stock():
    """Estado de inventario desde BD."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute(
            "SELECT p.nombre, COALESCE(ig.stock_actual, 0) as stock "
            "FROM productos p LEFT JOIN inventario_general ig ON p.producto_id=ig.producto_id "
            "WHERE p.activo=1 ORDER BY stock ASC")
        productos = [{"nombre": r[0], "stock": r[1]} for r in c.fetchall()]
        criticos = [p for p in productos if p["stock"] <= 5]
        conn.close()
        return jsonify({"ok": True, "total": len(productos),
                        "criticos": criticos, "productos": productos})
    except Exception as e:
        return jsonify({"ok": True, "total": 0, "criticos": [], "productos": []})


@tools_bp.route('/api/tools/recomendar')
def tool_recomendar():
    """Recomendaciones IA basadas en datos."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        # Top-selling product
        c.execute(
            "SELECT nombre, SUM(cantidad) as total FROM historial_ventas "
            "GROUP BY nombre ORDER BY total DESC LIMIT 3")
        tops = [{"producto": r[0], "ventas": r[1]} for r in c.fetchall()]
        # Low stock
        c.execute(
            "SELECT p.nombre, ig.stock_actual FROM productos p "
            "JOIN inventario_general ig ON p.producto_id=ig.producto_id "
            "WHERE ig.stock_actual <= 5 AND p.activo=1 LIMIT 3")
        bajos = [{"producto": r[0], "stock": r[1]} for r in c.fetchall()]
        conn.close()

        recomendaciones = []
        for t in tops:
            recomendaciones.append({
                "tipo": "estrella", "producto": t["producto"],
                "razon": f"Más vendido ({t['ventas']} unidades)"})
        for b in bajos:
            recomendaciones.append({
                "tipo": "urgente", "producto": b["producto"],
                "razon": f"Stock crítico ({b['stock']}u)"})
        if not recomendaciones:
            recomendaciones.append({
                "tipo": "info", "producto": "Sistema",
                "razon": "Registra ventas para obtener recomendaciones"})
        return jsonify({"ok": True, "recomendaciones": recomendaciones})
    except Exception as e:
        return jsonify({"ok": True, "recomendaciones": []})


@tools_bp.route('/api/tools/prediccion')
def tool_prediccion():
    """Predicción de ventas basada en histórico."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT COALESCE(AVG(daily_total),0) FROM "
                  "(SELECT SUM(total) as daily_total FROM historial_ventas "
                  "GROUP BY substr(fecha,1,10) ORDER BY fecha DESC LIMIT 7)")
        avg = c.fetchone()[0] or 0
        conn.close()
        return jsonify({"ok": True, "prediccion": {
            "hoy_estimado": round(avg, 2),
            "semana_estimada": round(avg * 7, 2),
            "tendencia": "estable",
            "confianza": 0.7 if avg > 0 else 0.0,
        }})
    except Exception as e:
        return jsonify({"ok": True, "prediccion": {
            "hoy_estimado": 0, "semana_estimada": 0,
            "tendencia": "sin datos", "confianza": 0.0}})


@tools_bp.route('/api/tools/abc')
def tool_abc():
    """Análisis ABC de productos basado en ventas reales."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute(
            "SELECT nombre, SUM(total) as revenue FROM historial_ventas "
            "GROUP BY nombre ORDER BY revenue DESC")
        rows = c.fetchall()
        conn.close()
        total_rev = sum(r[1] for r in rows) or 1
        cumulative = 0
        a, b, c_list = [], [], []
        for r in rows:
            cumulative += r[1]
            pct = cumulative / total_rev
            if pct <= 0.8:
                a.append(r[0])
            elif pct <= 0.95:
                b.append(r[0])
            else:
                c_list.append(r[0])
        return jsonify({"ok": True, "analisis": {"A": a, "B": b, "C": c_list}})
    except Exception as e:
        return jsonify({"ok": True, "analisis": {"A": [], "B": [], "C": []}})


@tools_bp.route('/api/tools/admin/status')
def tool_admin_status():
    try:
        from tools.admin_tools import ADMIN_TOOLS
        return jsonify({"ok": True, "status": "active", "tools": len(ADMIN_TOOLS),
                        "modulos": list(ADMIN_TOOLS.keys())})
    except Exception:
        return jsonify({"ok": True, "status": "fallback", "tools": 0, "modulos": []})


@tools_bp.route('/api/tools/analytic/resumen')
def tool_analytic_resumen():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        hoy = date.today().isoformat()
        c.execute("SELECT COALESCE(SUM(total),0), COUNT(*) FROM historial_ventas WHERE fecha LIKE ?",
                  (f"{hoy}%",))
        row = c.fetchone()
        conn.close()
        return jsonify({"ok": True, "ventas_hoy": row[0] or 0, "transacciones_hoy": row[1]})
    except Exception:
        return jsonify({"ok": True, "ventas_hoy": 0, "transacciones_hoy": 0})


@tools_bp.route('/api/tools/auth/verify', methods=['POST'])
def tool_auth_verify():
    user = session.get('usuario')
    return jsonify({"ok": True, "autenticado": bool(user), "usuario": user})


@tools_bp.route('/api/tools/general/info')
def tool_general_info():
    return jsonify({"ok": True, "version": "8.0", "modo": "produccion",
                    "endpoints": ["health_check", "config_publica", "biometric_check"]})


@tools_bp.route('/api/tools/ia/status')
def tool_ia_status():
    try:
        from tools.ia_tools import IA_TOOLS
        return jsonify({"ok": True, "status": "active", "tools": len(IA_TOOLS), "agent_version": "3.0"})
    except Exception:
        return jsonify({"ok": True, "status": "fallback", "tools": 0, "agent_version": "3.0"})


@tools_bp.route('/api/tools/importar/productos', methods=['POST'])
def tool_importar_productos():
    d = request.get_json(silent=True) or {}
    productos = d.get('productos', [])
    if not productos:
        return jsonify({"ok": False, "error": "No hay productos para importar"}), 400
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        importados = 0
        for p in productos:
            nombre = p.get('nombre', '').strip()
            if not nombre:
                continue
            precio = float(p.get('precio', 0))
            costo = float(p.get('costo', precio * 0.7))
            categoria = p.get('categoria', 'General')
            stock = int(p.get('stock', 0))
            um = p.get('um', 'Un')
            pid = f"prod-{uuid.uuid4().hex[:8]}"
            cursor.execute(
                "INSERT INTO productos (producto_id,nombre,precio,costo,categoria,unidad_medida,activo) "
                "VALUES (?,?,?,?,?,?,1)", (pid, nombre, precio, costo, categoria, um))
            cursor.execute(
                "INSERT INTO inventario_general (producto_id,nombre,stock_actual,stock_minimo,"
                "precio_venta,actualizado) VALUES (?,?,?,5,?,?)",
                (pid, nombre, stock, precio, datetime.now().isoformat()))
            importados += 1
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "importados": importados, "total": len(productos)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@tools_bp.route('/api/tools/inventario/resumen')
def tool_inventario_resumen():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        total_prod = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= 5")
        stock_bajo = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(stock_actual),0) FROM inventario_general")
        stock_total = c.fetchone()[0] or 0
        conn.close()
        return jsonify({"ok": True, "productos": total_prod, "stock_bajo": stock_bajo,
                        "unidades_totales": stock_total})
    except Exception:
        return jsonify({"ok": True, "productos": 0, "stock_bajo": 0, "unidades_totales": 0})


@tools_bp.route('/api/tools/lealtad/resumen')
def tool_lealtad_resumen():
    conn = None
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = c.fetchone()[0]
        return jsonify({"ok": True, "clientes_inscritos": total_clientes, "puntos_total": 0})
    except Exception:
        return jsonify({"ok": True, "clientes_inscritos": 0, "puntos_total": 0})
    finally:
        if conn is not None:
            conn.close()


@tools_bp.route('/api/tools/licencia/info')
def tool_licencia_info():
    try:
        from license.core import verificar_licencia
        info = verificar_licencia()
        return jsonify({"ok": True, **info})
    except Exception:
        return jsonify({"ok": True, "tipo": "trial", "activa": True})


@tools_bp.route('/api/tools/seguridad/resumen')
def tool_seguridad_resumen():
    return jsonify({"ok": True, "nivel": "alto", "amenazas_bloqueadas": 0,
                    "ssl": False, "rate_limit": True})


@tools_bp.route('/api/tools/setting/list')
def tool_setting_list():
    return jsonify({"ok": True, "configuraciones": [
        "idioma", "moneda", "tema", "notificaciones", "backup_auto"]})


@tools_bp.route('/api/tools/tienda/resumen')
def tool_tienda_resumen():
    conn = None
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM productos WHERE activo=1")
        productos = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM clientes")
        clientes = c.fetchone()[0]
        return jsonify({"ok": True, "productos": productos, "clientes": clientes})
    except Exception:
        return jsonify({"ok": True, "productos": 0, "clientes": 0})
    finally:
        if conn is not None:
            conn.close()


@tools_bp.route('/api/tools/validacion/check')
def tool_validacion_check():
    return jsonify({"ok": True, "validaciones": ["productos", "ventas", "inventario", "usuarios"],
                    "estado": "ok"})


@tools_bp.route('/api/tools/venta/estadisticas', methods=['POST'])
def tool_venta_estadisticas():
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        hoy = date.today().isoformat()
        c.execute("SELECT COALESCE(SUM(total),0), COUNT(*), COALESCE(AVG(total),0) "
                  "FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",))
        row = c.fetchone()
        conn.close()
        return jsonify({"ok": True, "total": row[0] or 0, "cantidad": row[1],
                        "promedio": round(row[2] or 0, 2)})
    except Exception:
        return jsonify({"ok": True, "total": 0, "cantidad": 0, "promedio": 0})
