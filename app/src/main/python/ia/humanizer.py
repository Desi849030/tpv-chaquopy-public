"""humanizer.py - Lenguaje humano profesional + blindaje UTF-8"""

class Humanizer:
    @staticmethod
    def sanitize_text(text):
        if not text: return ""
        text = str(text)
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        text = text.replace('\x00', '').replace('\r', '')
        return text.strip()
    
    @staticmethod
    def human_help(role):
        helps = {
            "cliente": "Puedo mostrarle nuestro catalogo, precios y ofertas.",
            "vendedor": "Puedo informarle sobre ventas, stock y productos mas vendidos.",
            "supervisor": "Tengo listo el dashboard con KPIs y tendencias.",
            "administrador": "Puedo generarle reportes financieros, ABC y proyecciones.",
            "desarrollador": "Acceso total activo. Monitoreo del sistema disponible."
        }
        return helps.get(role, helps["cliente"])
