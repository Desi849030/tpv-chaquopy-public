"""context_memory.py - Memoria conversacional agentic: resolucion de referencias y seguimiento de contexto"""
import time

_sessions = {}

class ConversationContext:
    def __init__(self, sid):
        self.sid = sid
        self.history = []
        self.last_product = None
        self.last_intent = None
        self.last_category = None
        self.entity_cache = {}
        self.turn_count = 0
        self._created = time.time()

    def add_turn(self, user_text, bot_response, intent=None):
        self.turn_count += 1
        self.history.append({"user": user_text, "bot": bot_response, "intent": intent, "turn": self.turn_count})
        if len(self.history) > 15:
            self.history = self.history[-15:]
        if intent:
            self.last_intent = intent

    def resolve_reference(self, text):
        pronouns = ["este","esta","eso","ese","esa","aquel","aquella","lo","la","el"]
        words = text.lower().split()
        has_pronoun = any(w in pronouns for w in words)
        price_words = ["cuanto cuesta","precio","valor","cuanto es","a cuanto"]
        stock_words = ["cuanto hay","stock","disponible","quedan","hay de","hay","tiene"]
        result = {}
        if has_pronoun:
            if self.last_product:
                result["implied_product"] = self.last_product
            if self.last_category:
                result["implied_category"] = self.last_category
        is_price_q = any(w in text.lower() for w in price_words)
        is_stock_q = any(w in text.lower() for w in stock_words)
        if (is_price_q or is_stock_q) and self.last_product:
            result["query"] = self.last_product
        # Si solo preguntan sobre stock/precio sin producto, usar el ultimo producto
        if (is_price_q or is_stock_q) and not any(w in text.lower() for w in ["cafe","leche","pan","agua","arroz","azucar","carne","pollo"]):
            if self.last_product and len(text.split()) <= 5:
                result["query"] = self.last_product
        return result

    def get_last_topics(self):
        """Retorna los ultimos temas discutidos."""
        return [h.get("intent") for h in self.history[-5:] if h.get("intent")]

def get_context(sid):
    if sid not in _sessions:
        _sessions[sid] = ConversationContext(sid)
    return _sessions[sid]

def cleanup_old(max_age=7200):
    now = time.time()
    to_remove = [s for s, c in _sessions.items() if now - c._created > max_age]
    for s in to_remove:
        del _sessions[s]
