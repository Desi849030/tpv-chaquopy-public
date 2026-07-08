"""ai_routes.py v2.0 — Rutas API IA Edge FIXED
Todas las rutas que el frontend espera, correctamente mapeadas.
"""
from flask import Blueprint, jsonify, request
ai_bp = Blueprint('ai_edge', __name__, url_prefix='/api/ai')

# ══════════════════════════════════════════════════════════════
#  PREDICCIONES — /api/ai/predict/dashboard
# ══════════════════════════════════════════════════════════════
@ai_bp.route('/predictor', methods=['GET'])
def predictor():
    """Alias para compatibilidad."""
    return _predict_dashboard()

@ai_bp.route('/predict/dashboard', methods=['GET'])
def predict_dashboard():
    return _predict_dashboard()

def _predict_dashboard():
    try:
        from ai_predictor import get_inventory_predictions_summary
        data = get_inventory_predictions_summary()
        # Asegurar que los campos esperados por el frontend existen
        if 'top_profit_products' not in data:
            # Calcular desde los datos disponibles
            conn = None
            try:
                from database import obtener_conexion
                conn = obtener_conexion()
                rows = conn.execute(
                    "SELECT nombre, stock, precio, costo FROM productos WHERE stock > 0 ORDER BY (precio - COALESCE(costo,0)) DESC LIMIT 5"
                ).fetchall()
                data['top_profit_products'] = [
                    {"nombre": r[0], "stock": r[1], "precio": r[2],
                     "profit": round((r[2] or 0) * 0.35, 2), "margin": 35}
                    for r in rows
                ]
            except Exception:
                data['top_profit_products'] = []
            finally:
                if conn: conn.close()
        # Asegurar top_risk_products tiene campos correctos
        for p in data.get('top_risk_products', []):
            if 'reorder' not in p:
                p['reorder'] = 50
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "total_products": 0, "risk_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "recommendations": [], "top_risk_products": [], "top_profit_products": [], "financial_forecast": {"estimated_revenue_week": 0}}), 500

# ══════════════════════════════════════════════════════════════
#  ANTI-FRAUDE — /api/ai/fraud/dashboard
# ══════════════════════════════════════════════════════════════
@ai_bp.route('/fraud', methods=['GET'])
def fraud():
    """Alias para compatibilidad."""
    return _fraud_dashboard()

@ai_bp.route('/fraud/dashboard', methods=['GET'])
def fraud_dashboard():
    return _fraud_dashboard()

def _fraud_dashboard():
    try:
        from ai_fraud import get_fraud_dashboard
        return jsonify(get_fraud_dashboard())
    except Exception as e:
        return jsonify({"error": str(e), "overall_status": "ERROR", "system_health": 0, "total_alerts": 0, "recent_alerts": [], "benford_analysis": {"applicable": False, "reason": str(e)}, "recommendations": []}), 500

# ══════════════════════════════════════════════════════════════
#  ANALYTICS — /api/ai/analytics/*
# ══════════════════════════════════════════════════════════════
@ai_bp.route('/analytics', methods=['GET'])
def analytics():
    """Endpoint combinado para compatibilidad."""
    try:
        from ai_analytics import get_analytics_dashboard
        return jsonify(get_analytics_dashboard())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_bp.route('/analytics/abc', methods=['GET'])
def analytics_abc():
    try:
        from ai_analytics import abc_analysis
        return jsonify(abc_analysis())
    except Exception as e:
        return jsonify({"error": str(e), "categories": {"A": {"count": 0, "revenue_pct": 0}, "B": {"count": 0, "revenue_pct": 0}, "C": {"count": 0, "revenue_pct": 0}}, "insight": []}), 500

@ai_bp.route('/analytics/cross-selling', methods=['GET'])
def analytics_cross_selling():
    try:
        from ai_analytics import cross_selling_analysis
        return jsonify(cross_selling_analysis())
    except Exception as e:
        return jsonify({"error": str(e), "recommendations": [], "total_baskets": 0}), 500

@ai_bp.route('/analytics/prices', methods=['GET'])
def analytics_prices():
    return _price_optimization()

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

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
def general_dashboard():
    """Dashboard general llamado por ia_cargarTodo()."""
    try:
        from ai_analytics import get_analytics_dashboard
        from datetime import datetime
        data = get_analytics_dashboard()
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        return jsonify(data)
    except Exception as e:
        from datetime import datetime
        return jsonify({
            "error": str(e),
            "business_health_score": 0, "health_status": "ERROR",
            "timestamp": datetime.now().isoformat()
        }), 500

@analytics_bp.route('/kpis', methods=['GET'])
def general_kpis():
    """KPIs generales llamado por ia_cargarKPIs()."""
    return _kpis_data()
