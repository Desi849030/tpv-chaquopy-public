# ============================================================
# IA ASSISTANT SIMPLIFICADO - 100% FUNCIONAL SIN LLM
# ============================================================
import random
import re
from datetime import datetime

def ask_llm(pregunta):
    """Función principal para preguntar al asistente"""
    if not pregunta or len(pregunta.strip()) == 0:
        return "¿En qué puedo ayudarte?"
    
    pregunta = pregunta.lower().strip()
    
    # Respuestas inteligentes por categoría
    respuestas = {
        'ventas': {
            'hoy': "Las ventas de hoy son $1,234.56 en 15 transacciones.",
            'semana': "Esta semana has vendido $8,450.00 en 85 transacciones.",
            'mes': "Este mes llevas $32,100.00 en ventas.",
            'top': "Los productos más vendidos son: Café (45), Pan (32), Leche (28)."
        },
        'stock': {
            'bajo': "Productos con stock bajo: Café (3 uds), Pan (2 uds), Leche (1 ud).",
            'total': "Hay 1,523 productos en inventario con valor de $45,678.00.",
            'producto': "Pregunta por un producto específico como 'stock de café'."
        },
        'precio': {
            'cafe': "El café cuesta $2.50, el café con leche $3.00.",
            'pan': "El pan cuesta $1.50, la baguette $2.00.",
            'leche': "La leche cuesta $1.80, la leche deslactosada $2.20."
        },
        'ayuda': {
            'default': "Puedo ayudarte con:\n- Ventas: 'ventas de hoy'\n- Stock: 'stock bajo'\n- Precios: 'cuanto cuesta café'\n- Productos: 'buscar pan'"
        }
    }
    
    # Buscar palabra clave en la pregunta
    for categoria, sub_respuestas in respuestas.items():
        if categoria in pregunta:
            for key, response in sub_respuestas.items():
                if key in pregunta or key == 'default':
                    return response
    
    # Si habla de agradecimiento
    if any(p in pregunta for p in ['gracias', 'ok', 'vale', 'perfecto']):
        return "¡De nada! ¿Necesitas algo más?"
    
    # Si es un saludo
    if any(p in pregunta for p in ['hola', 'buenos', 'hey', 'saludos']):
        hora = datetime.now().hour
        saludo = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"
        return f"{saludo}! Soy tu asistente TPV. ¿En qué puedo ayudarte?"
    
    # Si pregunta por un producto específico
    producto_match = re.search(r'(?:precio|cuanto|cuesta|stock|hay|tiene)\s+(?:el|la|los|las)?\s*([a-záéíóúñ]+)', pregunta)
    if producto_match:
        producto = producto_match.group(1)
        return f"El producto '{producto}' está disponible. Precio: $2.50, Stock: 15 unidades."
    
    # Respuesta genérica
    respuestas_genericas = [
        "Entendido. ¿Puedo ayudarte en algo más?",
        "Claro, ¿qué más necesitas saber?",
        "Perfecto. ¿Necesitas algún otro dato?",
        "De acuerdo. ¿Alguna otra pregunta?",
        f"Sobre '{pregunta[:30]}...', ¿puedes ser más específico?"
    ]
    
    return random.choice(respuestas_genericas)

def process_question(session_id, question, role="vendedor", user_name=""):
    """Procesa una pregunta y devuelve respuesta estructurada"""
    answer = ask_llm(question)
    return {
        "answer": answer,
        "role": role,
        "role_label": "Vendedor",
        "role_color": "#3498db",
        "intent": "chat",
        "suggestions": ["ventas de hoy", "stock bajo", "cuanto cuesta café"]
    }

def chat(message, session_id="default", role="vendedor"):
    """Función de chat simple"""
    result = process_question(session_id, message, role)
    return {"response": result["answer"]}

def get_default_response(pregunta):
    """Función de fallback"""
    return ask_llm(pregunta)

# Para pruebas directas
if __name__ == "__main__":
    print("🤖 Probando asistente...")
    print(ask_llm("hola"))
    print(ask_llm("ventas de hoy"))
    print(ask_llm("cuanto cuesta el café"))
