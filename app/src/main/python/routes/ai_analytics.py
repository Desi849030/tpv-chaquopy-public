from db_connection import obtener_conexion
from auth_decorator import login_required
from routes.ai_helpers import ai_bp, requiere_login, jsonify, request
# ══════════════════════════════════════════════════════════════
#  ANALYTICS — /api/ai/analytics/*
# ══════════════════════════════════════════════════════════════
@requiere_login
@login_required
@ai_bp.route('/analytics', methods=['GET'])
def analytics():
    """Endpoint combinado para compatibilidad."""
    try:
        from ai_analytics import get_analytics_dashboard
        return jsonify(get_analytics_dashboard())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@requiere_login
@login_required
@ai_bp.route('/analytics/abc', methods=['GET'])
def analytics_abc():
    try:
        from ai_analytics import abc_analysis
        return jsonify(abc_analysis())
    except Exception as e:
        return jsonify({"error": str(e), "categories": {"A": {"count": 0, "revenue_pct": 0}, "B": {"count": 0, "revenue_pct": 0}, "C": {"count": 0, "revenue_pct": 0}}, "insight": []}), 500

@requiere_login
@login_required
@ai_bp.route('/analytics/cross-selling', methods=['GET'])
def analytics_cross_selling():
    try:
        from ai_analytics import cross_selling_analysis
        return jsonify(cross_selling_analysis())
    except Exception as e:
        return jsonify({"error": str(e), "recommendations": [], "total_baskets": 0}), 500

@requiere_login
@login_required
@ai_bp.route('/analytics/prices', methods=['GET'])
def analytics_prices():
    return _price_optimization()

@requiere_login
@login_required
@ai_bp.route('/prices', methods=['GET'])
def prices():
    """Alias para compatibilidad."""
    return _price_optimization()

def _price_optimization():
    try:
        from ai_analytics import price_optimization_suggestions
        return jsonify(price_optimization_suggestions())
    except Exception as e:
        return jsonify({"error": str(e), "price_suggestions": [], "dead_products": [], "total_price_opportunities": 0}), 500

# ══════════════════════════════════════════════════════════════
#  KPIs — /api/ai/kpis  y  /api/analytics/kpis
# ══════════════════════════════════════════════════════════════
@requiere_login
@login_required
@ai_bp.route('/kpis', methods=['GET'])
def kpis():
    return _kpis_data()

def _kpis_data():
    try:
        from ai_analytics import get_predictive_kpis
        data = get_predictive_kpis()
        # Asegurar campo ganancia_bruta para el frontend
        if data.get('today') and 'ganancia_bruta' not in data['today']:
            data['today']['ganancia_bruta'] = round(data['today'].get('ingresos', 0) * 0.35, 2)
        # Asegurar peak_hour
        if data.get('today') and 'peak_hour' not in data['today']:
            try:
                from database import obtener_conexion
                from datetime import datetime
                conn = obtener_conexion()
                today = datetime.now().strftime("%Y-%m-%d")
                peak = conn.execute(
                    "SELECT strftime('%H',fecha) as h, COUNT(*) FROM historial_ventas WHERE DATE(fecha)=? GROUP BY h ORDER BY 2 DESC LIMIT 1",
                    (today,)
                ).fetchone()
                data['today']['peak_hour'] = peak[0] + ':00' if peak else 'N/A'
                conn.close()
            except Exception:
                data['today']['peak_hour'] = 'N/A'
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "today": {"transacciones": 0, "ingresos": 0, "ganancia_bruta": 0, "avg_ticket": 0, "peak_hour": "N/A"}, "forecast": {"next_week_revenue": 0, "weekly_trend_pct": 0, "trend_direction": "estable"}}), 500

# ══════════════════════════════════════════════════════════════
#  DASHBOARD GENERAL — /api/analytics/dashboard
#  (sin prefijo /api/ai — lo registra app.py aparte)
# ══════════════════════════════════════════════════════════════
# NOTA: Esta ruta se registra con prefijo /api/analytics en app.py
# via el blueprint analytics_bp de abajo.

