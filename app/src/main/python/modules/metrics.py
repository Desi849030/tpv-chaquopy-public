from auth_decorator import login_required
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta
from database import obtener_conexion, agregar_log

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')
def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"): return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper
def usuario_actual():
    u = session.get("usuario", {}) or {}
    # Normaliza: garantizar 'usuario_id' aunque la sesion solo tenga 'id'.
    if u and "usuario_id" not in u:
        u["usuario_id"] = u.get("id") or u.get("username") or "anon"
    return u

@login_required
@metrics_bp.route('/dashboard/kpis', methods=['GET'])
@requiere_login
def api_kpis_dashboard():
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    hoy = datetime.now().strftime('%Y-%m-%d')
    conn = obtener_conexion()
    try:
        vid = u['usuario_id'] if rol == 'vendedor' else None
        filtro = "AND vendedor_id = ?" if vid else ""
        params = (vid,) if vid else ()
                # === PARCHE SQL INJECTION ===
        if vid:
# === REVISAR SQL INJECTION ===
            cursor = conn.execute("SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id = ?", (f"{hoy}%", vid))
# === FIN REVISIÓN ===
        else:
# === REVISAR SQL INJECTION ===
            cursor = conn.execute("SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",))
# === FIN REVISIÓN ===
        # === FIN PARCHE ===
        hoy_stats = dict(cursor.fetchone() or {})
        cursor = conn.execute("SELECT COUNT(*) as stock_bajo FROM inventario_general WHERE stock_actual < 5 AND stock_actual >= 0")
        stock_bajo = cursor.fetchone()['stock_bajo'] or 0
        return jsonify({"ok": True, "kpis": {
            "ventas_hoy": {"num_ventas": hoy_stats.get('num_ventas') or 0, "total_ingresos": float(hoy_stats.get('total_ingresos') or 0), "unidades": int(hoy_stats.get('unidades') or 0)},
            "stock_bajo": stock_bajo,
            "timestamp": datetime.now().isoformat()
        }})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
