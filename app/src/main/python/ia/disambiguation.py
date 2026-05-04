"""disambiguation.py - Capa de gestión de ambigüedad"""

class DisambiguationLayer:
    CONFIDENCE_HIGH = 0.7
    CONFIDENCE_MEDIUM = 0.4
    
    @staticmethod
    def handle_confidence(intent, confidence, user_text=""):
        """Maneja la respuesta según el nivel de confianza"""
        if confidence >= DisambiguationLayer.CONFIDENCE_HIGH:
            return None
        
        if confidence >= DisambiguationLayer.CONFIDENCE_MEDIUM:
            options = {
                "FINANCE": "finanzas o balance",
                "STOCK": "inventario o stock bajo",
                "TRENDS": "productos mas vendidos o tendencias",
                "SALES": "ventas de hoy o caja",
                "OFFERS": "ofertas o descuentos",
                "GREETING": "un saludo"
            }
            hint = options.get(intent, "otra cosa")
            return f"No estoy totalmente seguro. Te refieres a {hint}?"
        
        return "No logro entender tu consulta. Puedo ayudarte con: ventas, stock, finanzas, ofertas o productos."
