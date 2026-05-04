"""rich_response.py - Respuestas enriquecidas"""
class RichResponse:
    @staticmethod
    def text(content): return {"type": "text", "content": content}
    @staticmethod
    def table(headers, data): return {"type": "table", "headers": headers, "data": data}
    @staticmethod
    def alert(level, title, message): return {"type": "alert", "level": level, "title": title, "content": message}
    @staticmethod
    def card(title, body, action_text=None): return {"type": "card", "title": title, "body": body, "action": action_text}
    @staticmethod
    def multi(parts): return {"type": "multi", "parts": parts}
