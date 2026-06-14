# -*- coding: utf-8 -*-
"""humanizer.py - Lenguaje humano profesional + blindaje UTF-8 v2.0
Añade enhance() que faltaba y que agent_master llama."""

import random
from datetime import datetime


class Humanizer:

    # ── Saludos contextuales por hora del día ──
    _GREET_MORNING = ["¡Buen día!", "Buenos días,", "¡Arrancamos!"]
    _GREET_AFTERNOON = ["Buenas tardes,", "¡Hola!"]
    _GREET_EVENING = ["Buenas noches,", "¡Hola!"]

    # ── Frases de cierre para que el agente no suene robótico ──
    _CLOSERS = {
        "cliente": ["¿Algo más en lo que pueda ayudarle?",
                    "Estoy aquí para lo que necesite.",
                    "¿Le busco algo más?"],
        "vendedor": ["¿Necesitas algo más?",
                     "Aquí estoy para lo que ocupes.",
                     "¡A seguir vendiendo! 💪"],
        "supervisor": ["¿Revisamos algo más?",
                       "Cualquier cosa, aquí estoy."],
        "administrador": ["¿Requiere otro reporte?",
                          "¿Algo más que analizar?"],
        "desarrollador": ["¿Debug algo más?",
                          "Sistema listo."],
    }

    @staticmethod
    def sanitize_text(text):
        """Limpia texto: UTF-8 seguro, sin nulos, sin retornos de carro."""
        if not text:
            return ""
        text = str(text)
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        text = text.replace('\x00', '').replace('\r', '')
        # Eliminar espacios dobles
        while '  ' in text:
            text = text.replace('  ', ' ')
        return text.strip()

    def enhance(self, text, role='cliente'):
        """Mejora la respuesta con tono profesional y humano.
        - Añade saludo si la respuesta es larga
        - Sanitiza el texto
        - Elimina repeticiones de signos
        """
        if not text:
            return text
        text = self.sanitize_text(text)

        # Eliminar múltiples signos de exclamación/interrogación
        for c in '!?':
            while c * 3 in text:
                text = text.replace(c * 3, c * 2)

        # Eliminar emojis repetidos consecutivos (ej: 🔧🔧🔧 → 🔧)
        cleaned = []
        prev_char = ''
        for ch in text:
            if ord(ch) > 0x1F000 and ch == prev_char:
                continue
            cleaned.append(ch)
            prev_char = ch
        text = ''.join(cleaned)

        return text

    @staticmethod
    def human_help(role):
        helps = {
            "cliente": "Puedo mostrarle nuestro catálogo, precios y ofertas.",
            "vendedor": "Puedo informarle sobre ventas, stock y productos más vendidos.",
            "supervisor": "Tengo listo el dashboard con KPIs y tendencias.",
            "administrador": "Puedo generarle reportes financieros, ABC y proyecciones.",
            "desarrollador": "Acceso total activo. Monitoreo del sistema disponible.",
            "cajero": "Puedo ayudarte con cobros, caja y el catálogo.",
        }
        return helps.get(role, helps["cliente"])

    def get_closer(self, role='cliente'):
        """Devuelve una frase de cierre aleatoria para el rol."""
        options = self._CLOSERS.get(role, self._CLOSERS["cliente"])
        return random.choice(options)

    def time_greeting(self):
        """Saludo según la hora del día."""
        h = datetime.now().hour
        if h < 12:
            return random.choice(self._GREET_MORNING)
        elif h < 19:
            return random.choice(self._GREET_AFTERNOON)
        else:
            return random.choice(self._GREET_EVENING)
