"""ai_briefing.py - Briefing Matutino Proactivo"""
from datetime import datetime

class BriefingEngine:
    def __init__(self, db_query):
        self.db = db_query
    
    def generate_briefing(self, role="administrador"):
        briefing = []
        yesterday = self.db("SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','-1 day')", one=True)
        avg_week = self.db("SELECT COALESCE(AVG(daily),0) a FROM (SELECT SUM(total) daily FROM historial_ventas WHERE fecha>=DATE('now','-7 days') GROUP BY DATE(fecha))", one=True)
        if yesterday and avg_week and avg_week['a'] > 0:
            cambio = ((yesterday['r'] - avg_week['a']) / avg_week['a']) * 100
            if cambio > 10: briefing.append(f"Ventas ayer: +{cambio:.0f}% vs promedio")
            elif cambio < -10: briefing.append(f"Ventas ayer: {cambio:.0f}% vs promedio")
        critical = self.db("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual<=3 AND stock_actual>=0", one=True)
        if critical and critical['c'] > 0: briefing.append(f"{critical['c']} productos en stock critico")
        hoy = self.db("SELECT COALESCE(SUM(total),0) r FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if hoy and hoy['r'] > 0:
            h = datetime.now().hour or 1
            briefing.append(f"Proyeccion hoy: ${(hoy['r']/h*24):,.0f}")
        return " | ".join(briefing) if briefing else "Sistema operando normalmente."
