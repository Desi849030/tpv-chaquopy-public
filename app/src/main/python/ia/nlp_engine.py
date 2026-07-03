"""NLP Engine Profesional v2 — Clasificacion de intenciones."""
from __future__ import annotations
import re, logging
from typing import List, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Clasificador de intenciones con matching multi-nivel."""

    INTENTS = {
        "buscar_producto": ["buscar", "producto", "quiero", "necesito", "hay", "tienes", "busca", "encuentra", "cafe", "arroz", "leche", "pan"],
        "consultar_precio": ["precio", "cuanto", "cuesta", "vale", "cuestan", "precios", "costar", "importe"],
        "ver_stock": ["stock", "inventario", "disponible", "cantidad", "quedan", "existencia", "hay", "suficiente"],
        "vender": ["vender", "venda", "cobrar", "cobra", "registrar", "venta", "pagar", "comprar", "llevar"],
        "reporte_ventas": ["reporte", "ventas", "cuanto", "vendido", "total", "hoy", "dia", "semana", "mes", "ganancias"],
        "ayuda": ["ayuda", "help", "que puedes", "funciones", "comandos", "menu", "opciones", "como", "manual"],
        "saludo": ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "saludos", "que tal"],
        "despedida": ["adios", "chao", "gracias", "bye", "hasta luego", "nos vemos", "salir", "terminar"],
        "crear_producto": ["crear", "nuevo", "agregar", "aniadir", "registrar", "alta"],
        "modificar_producto": ["modificar", "cambiar", "actualizar", "editar", "precio", "nombre"],
    }

    def __init__(self, confidence_threshold: float = 0.3):
        self.threshold = confidence_threshold
        self._compile_patterns()

    def _compile_patterns(self):
        self.patterns = {}
        for intent, keywords in self.INTENTS.items():
            pattern = r"(?i)(" + "|".join(re.escape(kw) for kw in keywords) + r")"
            self.patterns[intent] = re.compile(pattern)

    def classify(self, text: str) -> List[Tuple[str, float]]:
        if not text or not text.strip():
            return [("ayuda", 1.0)]
        text_lower = text.lower().strip()
        results = []
        for intent, pattern in self.patterns.items():
            matches = pattern.findall(text_lower)
            if matches:
                score = len(matches) / max(len(text_lower.split()), 1)
                score = min(score * 2, 1.0)
                results.append((intent, score))
        words = set(text_lower.split())
        for intent, keywords in self.INTENTS.items():
            keyword_matches = words & set(keywords)
            if keyword_matches:
                score = len(keyword_matches) / max(len(keywords) * 0.3, 1)
                score = min(score, 1.0)
                existing = [r for r in results if r[0] == intent]
                if existing:
                    results = [(intent, max(score, existing[0][1])) if r[0] == intent else r for r in results]
                else:
                    results.append((intent, score))
        results.sort(key=lambda x: x[1], reverse=True)
        results = [r for r in results if r[1] >= self.threshold]
        if not results:
            return [("ayuda", 0.5)]
        return results[:3]

    def get_primary_intent(self, text: str) -> Tuple[str, float]:
        results = self.classify(text)
        return results[0] if results else ("ayuda", 0.5)


class EntityExtractor:
    """Extractor de entidades."""

    def __init__(self):
        self.product_pattern = re.compile(r"(?i)(?:el |la |un |una )?([a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})")
        self.price_pattern = re.compile(r"(?i)(\d+[.,]?\d*)\s*(?:pesos|\$|eur|usd|cup|mn)")
        self.quantity_pattern = re.compile(r"(?i)(\d+)\s*(?:kgs?|litros?|unidades?|paquetes?|bolsas?)")

    def extract_products(self, text: str) -> List[str]:
        matches = self.product_pattern.findall(text)
        stopwords = {"quiero", "necesito", "buscar", "comprar", "vender", "ver", "tener", "dar", "hay", "precio", "cuanto", "stock", "disponible"}
        return [m.strip() for m in matches if m.strip().lower() not in stopwords and len(m.strip()) > 2]

    def extract_price(self, text: str) -> Optional[float]:
        match = self.price_pattern.search(text)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
        return None

    def extract_quantity(self, text: str) -> Optional[int]:
        match = self.quantity_pattern.search(text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None


class ResponseGenerator:
    """Generador de respuestas profesionales."""

    def __init__(self):
        self.templates = {
            "buscar_producto": ["He encontrado {count} producto(s) para '{query}':\n{products}"],
            "consultar_precio": ["El precio de {product} es {price}"],
            "ver_stock": ["El stock actual de {product} es de {stock} unidades"],
            "saludo": ["Hola! En que puedo ayudarte hoy?"],
            "ayuda": ["Puedo ayudarte con:\n{commands}"],
        }

    def generate(self, intent: str, context: dict) -> str:
        templates = self.templates.get(intent, ["{default}"])
        template = templates[0]
        try:
            return template.format(**context)
        except KeyError:
            return context.get("default", "Procesando tu solicitud...")


classifier = IntentClassifier()
extractor = EntityExtractor()
responder = ResponseGenerator()


class NLPEngine:
    """Facade de compatibilidad para ia.agent.

    Versiones anteriores importaban NLPEngine, mientras que el módulo actual
    expone classifier/extractor/responder. Esta clase evita que el motor IA
    quede desactivado por un simple cambio de API interna.
    """

    def __init__(self):
        self.classifier = classifier
        self.extractor = extractor
        self.responder = responder

    def classify(self, text: str):
        return self.classifier.classify(text)

    def get_primary_intent(self, text: str):
        return self.classifier.get_primary_intent(text)

    def extract_entities(self, text: str):
        return {
            "products": self.extractor.extract_products(text),
            "price": self.extractor.extract_price(text),
            "quantity": self.extractor.extract_quantity(text),
        }

    def generate(self, intent: str, context: dict):
        return self.responder.generate(intent, context)
