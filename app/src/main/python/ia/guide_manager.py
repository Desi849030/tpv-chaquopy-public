"""guide_manager.py - Motor de Guia Contextual"""
from .role_guidance import ROLE_MISSIONS, SCREEN_GUIDES
import random
from datetime import datetime

class GuideManager:
    def __init__(self, user_role="cliente"):
        self.role = user_role
        self.missions = ROLE_MISSIONS.get(user_role, ROLE_MISSIONS["cliente"])
    
    def get_contextual_guide(self, screen_id=None):
        h = datetime.now().hour
        state = "inicio" if h < 9 else "operativo" if h < 18 else "cierre"
        screen_info = SCREEN_GUIDES.get(screen_id, "")
        suggestions = self.missions.get(state, self.missions.get("operativo", ["Estoy aqui para ayudarle."]))
        role_suggestion = random.choice(suggestions)
        if screen_info:
            return f"📍 {screen_info}\n\n💡 {role_suggestion}"
        return f"🤖 {role_suggestion}"
    
    def get_onboarding(self):
        return self.get_contextual_guide()
    
    def get_help(self):
        suggestions = self.missions.get("ayuda", ["¿En que puedo ayudarle?"])
        return random.choice(suggestions)
