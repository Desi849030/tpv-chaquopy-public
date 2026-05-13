from routes.ai_helpers import analytics_bp, requiere_login, jsonify, Blueprint

@requiere_login
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

@requiere_login
@analytics_bp.route('/kpis', methods=['GET'])
def general_kpis():
    """KPIs generales llamado por ia_cargarKPIs()."""
    return _kpis_data()
