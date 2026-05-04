"""insight_engine.py - Motor de Anomalias y Proactividad"""
import math

class InsightEngine:
    def detect_anomaly(self, current_value, history, threshold=2.5):
        if len(history) < 5:
            return {"is_anomaly": False, "z_score": 0}
        mean = sum(history) / len(history)
        var = sum((d - mean) ** 2 for d in history) / len(history)
        std = math.sqrt(var)
        if std == 0:
            return {"is_anomaly": False, "z_score": 0}
        z = (current_value - mean) / std
        return {"is_anomaly": abs(z) > threshold, "z_score": round(z, 2)}
    
    def generate_alerts(self, db_query_func):
        alerts = []
        try:
            low = db_query_func("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual<=3 AND stock_actual>=0", one=True)
            if low and low['c'] > 0:
                alerts.append({"type":"STOCK_CRITICAL","icon":"🔴","message":f"{low['c']} productos criticos"})
        except: pass
        return alerts
