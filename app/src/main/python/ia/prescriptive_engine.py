"""prescriptive_engine.py - De descriptivo a prescriptivo"""
class PrescriptiveEngine:
    def __init__(self, db_query):
        self.db = db_query
    
    def analyze_star_product(self, product_name):
        sales = self.db("SELECT SUM(cantidad) q FROM historial_ventas WHERE nombre=? AND fecha>=DATE('now','-30 days')", (product_name,), one=True)
        stock = self.db("SELECT stock_actual s FROM inventario_general WHERE nombre=?", (product_name,), one=True)
        if not sales or not stock: return None
        qty = sales['q'] or 0; s = stock['s'] or 0
        if qty > 20 and s < 10: return f"'{product_name}' es estrella pero stock bajo ({s:.0f}uds). Sugiero aumentar pedido 30%."
        if qty > 10 and s < 5: return f"'{product_name}' tiene buena demanda pero stock critico. Pedido urgente."
        return None
    
    def get_prescriptive_insight(self, context="general"):
        top = self.db("SELECT p.nombre, SUM(h.total) rev FROM productos p JOIN historial_ventas h ON p.nombre=h.nombre WHERE h.fecha>=DATE('now','-30 days') GROUP BY p.nombre ORDER BY rev DESC LIMIT 3")
        if top:
            for prod in top:
                insight = self.analyze_star_product(prod['nombre'])
                if insight: return insight
        return "Todos los productos estrella tienen stock adecuado."
