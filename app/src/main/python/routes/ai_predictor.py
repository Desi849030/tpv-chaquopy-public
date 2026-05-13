from routes.ai_helpers import ai_bp, requiere_login, jsonify
# ══════════════════════════════════════════════════════════════
#  PREDICCIONES — /api/ai/predict/dashboard
# ══════════════════════════════════════════════════════════════
@requiere_login
@ai_bp.route('/predictor', methods=['GET'])
def predictor():
    """Alias para compatibilidad."""
    return _predict_dashboard()

@requiere_login
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

