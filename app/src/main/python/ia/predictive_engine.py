"""predictive_engine.py - Analítica Predictiva"""
import math

class PredictiveEngine:
    def calculate_rop(self, avg_daily_demand, lead_time, safety_stock=0):
        return math.ceil((avg_daily_demand * lead_time) + safety_stock)
    
    def predict_stockout_days(self, current_stock, sales_history):
        if not sales_history:
            return 999, "Sin datos historicos"
        n = len(sales_history)
        pesos = list(range(1, n + 1))
        wma_demand = sum(s * p for s, p in zip(sales_history, pesos)) / sum(pesos) if sum(pesos) > 0 else 0
        if wma_demand <= 0:
            return 999, "Sin demanda reciente"
        days_left = current_stock / wma_demand
        return round(days_left, 1), f"Se agotara en {days_left:.0f} dias"
    
    def analyze_pareto(self, products_revenue):
        if not products_revenue:
            return []
        sorted_p = sorted(products_revenue, key=lambda x: x.get('revenue', 0), reverse=True)
        total = sum(p.get('revenue', 0) for p in sorted_p)
        if total == 0:
            return []
        cum = 0; top = []
        threshold = max(1, len(sorted_p) // 5)
        for i, p in enumerate(sorted_p):
            cum += p.get('revenue', 0)
            top.append(p['name'])
            if cum / total >= 0.8 or i >= threshold:
                break
        return top
    
    def trend_direction(self, data):
        if len(data) < 3:
            return 0
        n = len(data)
        x = list(range(n))
        sx, sy = sum(x), sum(data)
        sxy = sum(x[i]*data[i] for i in range(n))
        sx2 = sum(v*v for v in x)
        m = (n*sxy - sx*sy)/(n*sx2 - sx*sx) if (n*sx2 - sx*sx) != 0 else 0
        return 1 if m > 0.5 else -1 if m < -0.5 else 0
