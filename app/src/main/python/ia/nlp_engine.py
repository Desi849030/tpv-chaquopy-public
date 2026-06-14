"""nlp_engine.py - Clasificador de Intenciones (TF-IDF + Softmax) v2.0
Ampliado de 7 a 20+ intenciones para el agente TPV."""
import math
import unicodedata
from collections import defaultdict

class NLPEngine:
    def __init__(self):
        self.intents = {
            "GREETING": [
                "hola", "buenos dias", "buenas tardes", "buenas noches",
                "quien eres", "saludos", "hey", "que tal", "buenas",
                "buen dia", "como estas",
            ],
            "GOODBYE": [
                "adios", "hasta luego", "chao", "nos vemos", "bye",
                "hasta manana", "me voy", "gracias adios",
            ],
            "HELP": [
                "ayuda", "que puedes hacer", "como funciona", "opciones",
                "menu", "que haces", "instrucciones", "comandos",
                "funciones", "capacidades",
            ],
            "FINANCE": [
                "cuanto vendimos", "ganancias hoy", "dinero", "ventas totales",
                "reporte economico", "balance", "ingresos", "gastos",
                "margen", "comision", "rentabilidad", "utilidad",
                "flujo de caja", "ganancia neta", "facturacion",
            ],
            "SALES": [
                "ventas hoy", "cuanto vendi", "recaude", "caja",
                "cuanto llevo", "como voy", "ticket promedio",
                "transacciones de hoy", "cuantas ventas",
            ],
            "STOCK": [
                "falta stock", "inventario bajo", "que comprar",
                "productos agotados", "reponer", "reabastecer",
                "critico", "poco stock", "faltante", "stock bajo",
            ],
            "STOCK_QUERY": [
                "cuanto hay de", "stock de", "quedan de", "tengo de",
                "disponibilidad de", "existencia de", "hay en inventario",
                "cuantas unidades", "cuanto queda",
            ],
            "PRODUCT_SEARCH": [
                "buscar producto", "precio de", "cuanto cuesta",
                "cuanto vale", "busco", "tiene", "hay", "donde esta",
                "info del producto", "informacion de",
            ],
            "TRENDS": [
                "lo mas vendido", "producto estrella", "tendencia",
                "top ventas", "mejor producto", "ranking", "popular",
                "prediccion", "proyeccion", "pronostico", "forecast",
            ],
            "TOP_PRODUCTS": [
                "top productos", "mas vendidos", "productos estrella",
                "mejor vendido", "ranking productos", "productos top",
            ],
            "CATEGORIES": [
                "categorias", "catalogo", "que tienen", "secciones",
                "que venden", "departamento", "rubros", "tipos de producto",
            ],
            "OFFERS": [
                "ofertas", "descuentos", "rebajas", "promocion",
                "barato", "mejor precio", "liquidacion", "ganga",
                "en oferta", "descuento especial",
            ],
            "RECOMMEND": [
                "recomiendame", "recomendar", "recomendacion", "sugerir",
                "sugerencia", "que me recomiendas", "aconsejar",
                "aconsejame", "propuesta", "proponer", "que llevo",
            ],
            "ABC": [
                "analisis abc", "pareto", "clasificacion abc",
                "abc productos", "curva abc",
            ],
            "PREDICTIONS": [
                "prediccion ventas", "pronostico", "proyeccion",
                "cuanto venderemos", "estimar ventas", "forecast",
            ],
            "ROTATION": [
                "rotacion", "indice rotacion", "velocidad venta",
                "movimiento inventario", "rotacion stock",
            ],
            "EXPENSES": [
                "gastos", "egresos", "costos fijos", "gastos del dia",
                "cuanto gaste", "gastos operativos",
            ],
            "DASHBOARD": [
                "dashboard", "resumen", "estado general", "kpi",
                "panel", "como va el negocio", "resumen general",
            ],
            "SYSTEM": [
                "estado sistema", "logs", "errores", "metricas sistema",
                "debug", "salud del sistema", "estado servidor",
            ],
            "LOGIN": [
                "iniciar sesion", "login", "entrar", "acceder",
                "contrasena", "password", "credenciales", "cuenta",
            ],
            "PAYMENT": [
                "metodo de pago", "pagar", "efectivo", "tarjeta",
                "transferencia", "codigo qr", "cobrar",
            ],
            "LOYALTY": [
                "puntos", "lealtad", "fidelidad", "recompensa",
                "beneficio", "acumular puntos", "canjear",
            ],
            "HISTORY": [
                "historial", "compras", "recibo", "factura",
                "registros", "movimientos", "historial ventas",
            ],
            "EOQ": [
                "eoq", "lote optimo", "pedido optimo",
                "cantidad optima", "reorden",
            ],
            "BACKUP": [
                "respaldo", "backup", "copia seguridad",
                "guardar datos", "exportar datos",
            ],
        }
        self.vocab = set()
        self.idf = {}
        self.weights = defaultdict(lambda: defaultdict(float))
        self._train()

    @staticmethod
    def _normalize(text):
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def _tokenize(self, text):
        text = self._normalize(text.lower().strip())
        for c in '.,;:!?()[]{}"\'-¿¡':
            text = text.replace(c, ' ')
        return [w for w in text.split() if len(w) > 1]

    def _train(self):
        all_docs = []
        for intent, phrases in self.intents.items():
            for p in phrases:
                tokens = set(self._tokenize(p))
                all_docs.append(tokens)
                for t in tokens:
                    self.vocab.add(t)
        N = len(all_docs)
        for word in self.vocab:
            df = sum(1 for doc in all_docs if word in doc)
            self.idf[word] = math.log((N + 1) / (df + 1)) + 1
        for intent, phrases in self.intents.items():
            for p in phrases:
                tokens = self._tokenize(p)
                for word in tokens:
                    self.weights[intent][word] += self.idf.get(word, 1)

    def predict_intent(self, text):
        if not text or len(text.strip()) < 2:
            return "UNKNOWN", 0.0
        tokens = self._tokenize(text)
        scores = defaultdict(float)
        for intent in self.intents:
            for word in tokens:
                if word in self.vocab:
                    scores[intent] += self.weights[intent][word]
        if not scores:
            return "UNKNOWN", 0.0
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best] / total if total > 0 else 0
        # Minimum confidence threshold
        if scores[best] < 1.0:
            return "UNKNOWN", confidence
        return best, confidence

    def get_all_intents(self):
        """Returns list of all recognized intents."""
        return list(self.intents.keys())
