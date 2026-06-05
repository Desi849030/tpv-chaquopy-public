# -*- coding: utf-8 -*-
"""
Memoria del Agente - Historial de conversaciones
"""
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class Memory:
    def __init__(self, max_history=50):
        self.history = defaultdict(list)
        self.max_history = max_history
    
    def add(self, session_id, message):
        self.history[session_id].append(message)
        if len(self.history[session_id]) > self.max_history:
            self.history[session_id] = self.history[session_id][-self.max_history:]
    
    def get(self, session_id):
        return self.history.get(session_id, [])
    
    def clear(self, session_id):
        if session_id in self.history:
            del self.history[session_id]
    
    def get_all_sessions(self):
        return list(self.history.keys())
