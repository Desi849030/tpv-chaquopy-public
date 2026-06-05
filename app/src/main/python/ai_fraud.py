"""ai_fraud.py — Deteccion de fraude Edge AI"""
from datetime import datetime, timedelta
import math

def _get_db():
    from database import obtener_conexion
    return obtener_conexion()

def get_fraud_dashboard():
    conn = _get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        total = conn.execute("SELECT COUNT(*) FROM historial_ventas WHERE DATE(fecha)=?",(today,)).fetchone()[0]
        refunds = conn.execute("SELECT COUNT(*) FROM historial_ventas WHERE DATE(fecha)=? AND tipo LIKE '%devolucion%'",(today,)).fetchone()[0]
        amounts = conn.execute("SELECT total FROM historial_ventas WHERE DATE(fecha)=?",(today,)).fetchall()
        prices = conn.execute("SELECT precio FROM productos WHERE precio>0").fetchall()
    finally: conn.close()
    amounts = [r[0] for r in amounts if r[0]]
    first_digits = [int(str(a)[0]) for a in amounts if a >= 10]
    benford = {"applicable": len(first_digits) >= 20, "is_anomaly": False, "chi_squared": "N/A"}
    if benford["applicable"]:
        counts = {}
        for d in first_digits:
            counts[d] = counts.get(d, 0) + 1
        n = len(first_digits)
        chi = 0
        expected = {1:30.1,2:17.6,3:12.5,4:9.7,5:7.9,6:6.7,7:5.8,8:5.1,9:4.6}
        for d in range(1,10):
            obs_pct = (counts.get(d,0)/n)*100
            exp_pct = expected[d]
            chi += ((obs_pct - exp_pct)**2) / exp_pct if exp_pct > 0 else 0
        benford["chi_squared"] = round(chi, 2)
        benford["is_anomaly"] = chi > 15
    refund_ratio = refunds / total if total > 0 else 0
    refund_flag = refund_ratio > 0.10
    health = 90 if not benford["is_anomaly"] and not refund_flag else 60 if not benford["is_anomaly"] else 40
    alerts = []
    if benford["is_anomaly"]:
        alerts.append({"level":"ALTA","type":"BENFORD","details":"Anomalia en distribucion de montos. Posible manipulacion."})
    if refund_flag:
        alerts.append({"level":"MEDIA","type":"DEVOLUCIONES","details":f"Ratio de devoluciones {refund_ratio:.1%} superior al umbral 10%."})
    status = "PROTECTED" if health >= 80 else "MONITORING" if health >= 50 else "ALERT"
    recs = []
    if health < 80: recs.append("Revisa las transacciones con montos inusuales.")
    if refund_flag: recs.append(f"Investiga las devoluciones. Ratio {refund_ratio:.1%} es alto.")
    recs.append("Mantener monitoreo activo de transacciones.")
    return {
        "overall_status": status, "system_health": health,
        "total_alerts": len(alerts), "alert_distribution": {"critical": 0, "high": 1 if benford["is_anomaly"] else 0, "medium": 1 if refund_flag else 0, "low": 0},
        "recent_alerts": alerts, "benford_analysis": benford,
        "refund_ratio": {"ratio": refund_ratio, "flagged": refund_flag},
        "recommendations": recs
    }
