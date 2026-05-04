"""guardrails.py - Blindaje de seguridad y RBAC"""
ROLE_PERMISSIONS = {
    "cliente": ["productos","ofertas","categorias","ayuda"],
    "vendedor": ["productos","ofertas","ventas","stock","top","ayuda"],
    "supervisor": ["productos","ventas","stock","top","dashboard","tendencias","ayuda"],
    "administrador": ["productos","ventas","stock","top","dashboard","tendencias","finanzas","abc","predicciones","ofertas","ayuda"],
    "desarrollador": ["todo"]
}
BLOCKED_WORDS = ["hack","exploit","injection","drop table","delete from","shutdown","reboot","sudo","root"]

class Guardrails:
    @staticmethod
    def check_permission(role, intent):
        if role == "desarrollador": return True
        permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["cliente"])
        intent_map = {"FINANCE":"finanzas","STOCK":"stock","TRENDS":"top","SALES":"ventas","OFFERS":"ofertas","GREETING":"ayuda","HELP":"ayuda"}
        required = intent_map.get(intent, "ayuda")
        if required not in permissions: return f"Lo siento, no tienes permisos para {required}."
        return True
    
    @staticmethod
    def filter_noise(text):
        for word in BLOCKED_WORDS:
            if word in text.lower(): return True
        return False
    
    @staticmethod
    def sanitize_input(text):
        if not text: return ""
        return text.strip()[:500]
