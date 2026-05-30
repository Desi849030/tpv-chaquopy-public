"""nlp_engine.py - Clasificador de Intenciones (TF-IDF + Softmax)"""
import math
import unicodedata
from collections import defaultdict

class NLPEngine:
    def __init__(self):
        self.intents = {
            "FINANCE": ["cuanto vendimos","ganancias hoy","dinero","ventas totales",
                       "reporte economico","balance","ingresos","gastos","margen","comision"],
            "STOCK": ["falta stock","inventario bajo","que comprar","productos agotados",
                     "reponer","reabastecer","critico","poco stock","faltante"],
            "TRENDS": ["lo mas vendido","producto estrella","tendencia","top ventas",
                      "mejor producto","ranking","popular","prediccion","proyeccion"],
            "GREETING": ["hola","buenos dias","quien eres","ayuda","saludos",
                        "buenas tardes","buenas noches","hey","que tal"],
            "OFFERS": ["ofertas","descuentos","rebajas","promocion","barato",
                      "mejor precio","liquidacion","ganga"],
            "SALES": ["ventas hoy","cuanto vendi","recaude","caja","facturacion",
                     "ticket","cuanto llevo","como voy"]
        }
        self.vocab = set()
        self.idf = {}
        self.weights = defaultdict(lambda: defaultdict(float))
        self.intents["RECOMMEND"] = ["recomiendame","recomendar","recomendacion","sugerir","sugerencia","que me recomiendas","aconsejar","aconsejame","propuesta","proponer"]
        self._train()
    
    @staticmethod
    def _normalize(text):
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def _tokenize(self, text):
        text = self._normalize(text.lower().strip())
        for c in '.,;:!?()[]{}"\'-':
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
        return best, confidence
