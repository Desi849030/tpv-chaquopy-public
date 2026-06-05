"""session_context.py - Memoria conversacional de corto plazo"""
from datetime import datetime

class SessionContext:
    def __init__(self, max_history=10):
        self.history = []
        self.slots = {}  # Variables de contexto
        self.max_history = max_history
    
    def add(self, user_text, intent, response_summary):
        """Agrega un turno a la conversación"""
        turn = {
            'ts': datetime.now().isoformat(),
            'user': user_text[:200],
            'intent': intent,
            'response': response_summary[:200]
        }
        self.history.append(turn)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Actualizar slots de contexto
        self.slots['last_intent'] = intent
        self.slots['last_query'] = user_text
    
    def get_context(self):
        """Obtiene el contexto actual"""
        if not self.history:
            return None
        return {
            'last_intent': self.slots.get('last_intent'),
            'last_query': self.slots.get('last_query'),
            'recent_turns': len(self.history)
        }
    
    def fill_missing_slots(self, intent, required_slots, user_text):
        """Detecta si faltan datos y pregunta por ellos"""
        missing = []
        if 'date' in required_slots and 'fecha' not in user_text.lower():
            missing.append('fecha')
        if 'product' in required_slots and len(user_text.split()) < 3:
            missing.append('producto')
        
        if missing:
            return f"Claro, necesito más información: {', '.join(missing)}. ¿Podría indicármelos?"
        return None
    
    def should_ask_clarification(self, confidence):
        """Sugiere pedir clarificación si la confianza es baja"""
        return confidence < 0.4
