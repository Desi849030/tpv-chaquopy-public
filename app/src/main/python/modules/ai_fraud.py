from auth_decorator import login_required
from modules.ai_helpers import ai_bp, requiere_login, jsonify
# ══════════════════════════════════════════════════════════════
#  ANTI-FRAUDE — /api/ai/fraud/dashboard
# ══════════════════════════════════════════════════════════════
@requiere_login
@login_required
@ai_bp.route('/fraud', methods=['GET'])
def fraud():
    """Alias para compatibilidad."""
    return _fraud_dashboard()

@requiere_login
@login_required
@ai_bp.route('/fraud/dashboard', methods=['GET'])
def fraud_dashboard():
    return _fraud_dashboard()

def _fraud_dashboard():
    try:
        from ai_fraud import get_fraud_dashboard
        return jsonify(get_fraud_dashboard())
    except Exception as e:
        return jsonify({"error": str(e), "overall_status": "ERROR", "system_health": 0, "total_alerts": 0, "recent_alerts": [], "benford_analysis": {"applicable": False, "reason": str(e)}, "recommendations": []}), 500

