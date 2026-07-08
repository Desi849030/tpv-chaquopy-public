"""ai_analytics.py — Analytics avanzado Edge AI"""
from datetime import datetime, timedelta

def _get_db():
    from database import obtener_conexion
    return obtener_conexion()

def _safe(func):
    try: return func()
    except: return None

def get_predictive_kpis():
    conn = _get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        t = conn.execute("SELECT COUNT(*),COALESCE(SUM(total),0),COALESCE(SUM(cantidad),0) FROM historial_ventas WHERE DATE(fecha)=?",(today,)).fetchone()
        today_data = {"transacciones": t[0], "ingresos": float(t[1]), "unidades": float(t[2]), "avg_ticket": float(t[1])/t[0] if t[0]>0 else 0}
        since = (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d")
        w = conn.execute("SELECT COUNT(*),COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha>=?",(since,)).fetchone()
        last_w = conn.execute("SELECT COUNT(*),COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha>=date('now','-14 days') AND fecha<date('now','-7 days')").fetchone()
        weekly = {"total_transacciones": w[0], "total_ingresos": float(w[1]), "avg_diario": float(w[1])/7}
        this_w = float(w[1])
        prev_w = float(last_w[1]) if last_w else 0
        trend_pct = ((this_w - prev_w)/prev_w*100) if prev_w > 0 else 0
        direction = "creciente" if trend_pct > 5 else "decreciente" if trend_pct < -5 else "estable"
        forecast_rev = this_w * (1 + trend_pct/200)
    finally: conn.close()
    return {"today": today_data, "weekly": weekly, "forecast": {"next_week_revenue": round(forecast_rev,2), "trend_direction": direction, "weekly_trend_pct": round(trend_pct,1)}}

def get_analytics_dashboard():
    kpis = get_predictive_kpis()
    t = kpis["today"]
    conn = _get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        peak = conn.execute("SELECT strftime('%H',fecha) as h, COUNT(*) FROM historial_ventas WHERE DATE(fecha)=? GROUP BY h ORDER BY 2 DESC LIMIT 1",(today,)).fetchone()
        seller = conn.execute("SELECT vendedor_nombre, COALESCE(SUM(total),0) FROM historial_ventas WHERE DATE(fecha)=? AND vendedor_nombre IS NOT NULL GROUP BY vendedor_nombre ORDER BY 2 DESC LIMIT 1",(today,)).fetchone()
        products = conn.execute("SELECT nombre, SUM(total) as rev FROM historial_ventas WHERE DATE(fecha)=? GROUP BY nombre ORDER BY rev DESC",(today,)).fetchall()
        total_rev = sum(r[1] for r in products) if products else 1
    finally: conn.close()
    abc = {"A":[],"B":[],"C":[]}
    cum = 0
    for p in products:
        pct = p[1]/total_rev*100 if total_rev>0 else 0
        cum += pct
        if cum <= 80: abc["A"].append(p)
        elif cum <= 95: abc["B"].append(p)
        else: abc["C"].append(p)
    score = 70
    if t["ingresos"] > 1000: score += 10
    if t["avg_ticket"] > 50: score += 10
    if peak and peak[1] > 5: score += 5
    if seller: score += 5
    status = "EXCELLENT" if score>=90 else "GOOD" if score>=70 else "NEEDS_ATTENTION" if score>=50 else "CRITICAL"
    return {"business_health_score": min(score,100), "health_status": status, "kpis": kpis, "abc_analysis": {"categories": {"A":{"count":len(abc["A"])},"B":{"count":len(abc["B"])},"C":{"count":len(abc["C"])}}, "insight": [f"{len(abc['A'])} productos generan 80% de ingresos" if abc["A"] else "Sin datos ABC"]}}

def price_optimization_suggestions():
    conn = _get_db()
    try:
        rows = conn.execute("SELECT nombre, precio, costo FROM productos WHERE precio>0 AND costo>0 AND stock>0 ORDER BY (precio-costo)/precio ASC LIMIT 20").fetchall()
    finally: conn.close()
    suggestions = []
    for r in rows:
        name, price, cost = r[0], float(r[1]), float(r[2])
        margin = ((price-cost)/price)*100
        if margin < 30:
            new_price = cost / 0.7
            new_margin = 30
            suggestions.append({"nombre":name,"current_price":price,"current_margin":round(margin,1),"suggested_price":round(new_price,2),"new_margin":new_margin,"estimated_extra_profit":round((new_price-price)*5,2)})
    dead = []
    conn2 = _get_db()
    try:
        d = conn2.execute("SELECT nombre, stock FROM productos WHERE stock > 0 ORDER BY stock DESC LIMIT 20").fetchall()
    finally: conn2.close()
    return {"price_suggestions": suggestions[:5], "dead_products": [], "total_price_opportunities": len(suggestions)}

def cross_selling_analysis():
    conn = _get_db()
    try:
        rows = conn.execute("SELECT vendedor_nombre, GROUP_CONCAT(nombre) as items FROM historial_ventas WHERE DATE(fecha)>=date('now','-7 days') AND nombre IS NOT NULL GROUP BY vendedor_nombre").fetchall()
    finally: conn.close()
    recs = []
    return {"recommendations": recs[:5], "total_baskets": len(rows)}

def abc_analysis():
    data = get_analytics_dashboard()
    abc = data.get("abc_analysis", {})
    cats = abc.get("categories", {})
    # Asegurar revenue_pct para el frontend
    total_a = sum(p[1] for p in abc.get("A", [])) if abc.get("A") else 0
    total_b = sum(p[1] for p in abc.get("B", [])) if abc.get("B") else 0
    total_c = sum(p[1] for p in abc.get("C", [])) if abc.get("C") else 0
    total_all = total_a + total_b + total_c
    cats["A"] = {"count": len(abc.get("A", [])), "revenue_pct": round(total_a/total_all*100, 1) if total_all > 0 else 0}
    cats["B"] = {"count": len(abc.get("B", [])), "revenue_pct": round(total_b/total_all*100, 1) if total_all > 0 else 0}
    cats["C"] = {"count": len(abc.get("C", [])), "revenue_pct": round(total_c/total_all*100, 1) if total_all > 0 else 0}
    abc["categories"] = cats
    return abc
