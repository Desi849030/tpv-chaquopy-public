# -*- coding: utf-8 -*-
"""
Agente IA Proactivo - Motor Principal
"""
import random
import logging
from datetime import datetime
from ia.catalog import Catalog
from ia.memory import Memory

logger = logging.getLogger(__name__)


class AgentCore:
    def __init__(self):
        self.memory = Memory()
        self.catalog = Catalog()
        self.sessions = {}
        
        # Saludos por rol
        self.greetings = {
            'administrador': [
                "¡Hola admin! ¿En qué puedo ayudarte?",
                "¡Bienvenido de vuelta! Lista de comandos disponibles.",
                "¡Hola jefe! El sistema está funcionando correctamente."
            ],
            'vendedor': [
                "¡Hola vendedor! ¿Listo para atender clientes?",
                "¡Bienvenido! Puedo ayudarte con ventas y productos.",
                "¡Hola! ¿Necesitas ver el inventario?"
            ],
            'cliente': [
                "¡Hola! Bienvenido a nuestra cafetería ☕",
                "¡Buenos días! ¿En qué puedo ayudarte?",
                "¡Hola! ¿Qué te gustaría tomar hoy?",
                "¡Bienvenido! Tenemos café, bebidas y comida deliciosa."
            ]
        }
        
        print("🧠 Agente Proactivo v1.0 cargado")
    
    def process_message(self, text, role='cliente', user_name='', session_id=None):
        """Procesar mensaje del usuario"""
        if not session_id:
            session_id = f"sess_{random.randint(100000, 999999)}"
        
        # Guardar en memoria
        self.memory.add(session_id, {
            'role': 'user',
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Detectar intención
        intent = self._detect_intent(text)
        
        # Procesar según intención
        response = self._handle_intent(text, intent, role, user_name, session_id)
        
        # Guardar respuesta
        self.memory.add(session_id, {
            'role': 'agent',
            'text': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'response': response,
            'intent': intent,
            'role': role,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'confidence': random.uniform(0.6, 0.95)
        }
    
    def _detect_intent(self, text):
        """Detectar la intención del usuario"""
        text_lower = text.lower()
        
        # Saludos
        if any(w in text_lower for w in ['hola', 'buenos días', 'buenas', 'hey', 'hi', 'hello', 'saludos']):
            return 'GREETING'
        
        # Despedidas
        if any(w in text_lower for w in ['adiós', 'hasta luego', 'chao', 'nos vemos', 'bye']):
            return 'FAREWELL'
        
        # Productos/Catálogo
        if any(w in text_lower for w in ['producto', 'catálogo', 'catalogo', 'tienes', 'tienen', 'hay', 'venden']):
            return 'PRODUCTS'
        
        # Precios
        if any(w in text_lower for w in ['precio', 'cuánto', 'cuanto', 'cuesta', 'vale', 'coste']):
            return 'PRICE'
        
        # Stock/Inventario
        if any(w in text_lower for w in ['stock', 'inventario', 'existencias', 'disponible', 'disponibilidad']):
            return 'STOCK'
        
        # Bebidas
        if any(w in text_lower for w in ['bebida', 'bebidas', 'café', 'cafe', 'jugo', 'zumo', 'té', 'te']):
            return 'BEBIDAS'
        
        # Comida
        if any(w in text_lower for w in ['comida', 'comer', 'tostada', 'croissant', 'sandwich', 'bocadillo']):
            return 'COMIDA'
        
        # Recomendaciones
        if any(w in text_lower for w in ['recomienda', 'recomiendas', 'sugieres', 'qué me']):
            return 'RECOMMENDATION'
        
        # Horario
        if any(w in text_lower for w in ['horario', 'abren', 'cierran', 'hora', 'abierto']):
            return 'SCHEDULE'
        
        # Ubicación
        if any(w in text_lower for w in ['dónde', 'donde', 'ubicación', 'ubicacion', 'dirección', 'direccion', 'llegar']):
            return 'LOCATION'
        
        # Promociones
        if any(w in text_lower for w in ['promoción', 'promocion', 'oferta', 'descuento', 'rebajas']):
            return 'PROMOTIONS'
        
        # Ayuda
        if any(w in text_lower for w in ['ayuda', 'help', 'opciones', 'puedes', 'sabes']):
            return 'HELP'
        
        return 'UNKNOWN'
    
    def _handle_intent(self, text, intent, role, user_name, session_id):
        """Manejar la intención detectada"""
        
        name = user_name or 'amigo'
        
        if intent == 'GREETING':
            return self._greet(role, name)
        
        elif intent == 'FAREWELL':
            return f"¡Hasta luego, {name}! Fue un placer ayudarte. ¡Vuelve pronto! 👋"
        
        elif intent == 'PRODUCTS':
            return self._show_products(role, basic=True)
        
        elif intent == 'PRICE':
            return self._show_prices(text)
        
        elif intent == 'STOCK':
            return self._show_stock(role)
        
        elif intent == 'BEBIDAS':
            return self._show_products_by_category('bebidas')
        
        elif intent == 'COMIDA':
            return self._show_products_by_category('comida')
        
        elif intent == 'RECOMMENDATION':
            return self._recommend()
        
        elif intent == 'SCHEDULE':
            return "🕐 Nuestro horario es de lunes a domingo de 8:00 AM a 10:00 PM."
        
        elif intent == 'LOCATION':
            return "📍 Estamos ubicados en el centro de la ciudad. ¡Te esperamos!"
        
        elif intent == 'PROMOTIONS':
            return "🎉 ¡Tenemos promociones especiales! Pregunta por nuestro menú del día."
        
        elif intent == 'HELP':
            return self._show_help(role)
        
        else:
            return f"No estoy seguro de entender. ¿Puedes reformular tu pregunta? También puedes preguntar por: productos, precios, horarios o ubicaciones."
    
    def _greet(self, role, name):
        """Saludar según el rol"""
        greetings = self.greetings.get(role, self.greetings['cliente'])
        greeting = random.choice(greetings)
        
        if role == 'administrador':
            greeting += "\n\n📊 Comandos disponibles: stock, ventas, productos, usuarios"
        elif role == 'vendedor':
            greeting += "\n\n💼 Puedes consultar: productos, precios, stock disponible"
        else:
            greeting += "\n\n☕ Puedo informarte sobre: productos, precios, horarios y promociones"
        
        return greeting
    
    def _show_products(self, role, basic=False):
        """Mostrar productos"""
        try:
            products = self.catalog.get_all_products()
            
            if not products:
                return "📦 No hay productos disponibles en este momento."
            
            if basic or role not in ['administrador', 'vendedor']:
                return self._format_products_basic(products)
            else:
                return self._format_products_full(products)
        except Exception as e:
            logger.error(f"Error mostrando productos: {e}")
            return f"📦 **Nuestros Productos:**\n\n☕ Café Americano - $2.50\n☕ Cappuccino - $3.50\n🥤 Zumo de naranja - $2.00\n🥪 Tostada con tomate - $3.00\n🥐 Croissant - $1.80"
    
    def _format_products_basic(self, products):
        """Formato básico para clientes"""
        text = "☕ **Nuestros Productos:**\n\n"
        
        for p in products[:10]:
            nombre = p.get('nombre', 'Producto')
            precio = p.get('precio', 0)
            text += f"• {nombre} - ${precio:.2f}\n"
        
        return text
    
    def _format_products_full(self, products):
        """Formato completo para admin/vendedores"""
        text = "📋 **Catálogo Completo:**\n\n"
        
        for p in products[:20]:
            nombre = p.get('nombre', 'Producto')
            precio = p.get('precio', 0)
            precio_compra = p.get('precio_compra', 0)
            stock = p.get('stock_actual', 0)
            categoria = p.get('categoria', 'general')
            
            text += f"• **{nombre}**\n"
            text += f"  Precio: ${precio:.2f} | Costo: ${precio_compra:.2f}\n"
            text += f"  Stock: {stock} | Categoría: {categoria}\n\n"
        
        return text
    
    def _show_prices(self, text):
        """Mostrar precios de producto específico"""
        products = {
            'cafe': ('Café Americano', 2.50),
            'cappuccino': ('Cappuccino', 3.50),
            'zumo': ('Zumo de naranja', 2.00),
            'naranja': ('Zumo de naranja', 2.00),
            'tostada': ('Tostada con tomate', 3.00),
            'croissant': ('Croissant', 1.80)
        }
        
        text_lower = text.lower()
        
        for key, (nombre, precio) in products.items():
            if key in text_lower:
                return f"💰 El **{nombre}** cuesta **${precio:.2f}**"
        
        return "💰 **Lista de precios:**\n\n☕ Café Americano - $2.50\n☕ Cappuccino - $3.50\n🥤 Zumo de naranja - $2.00\n🥪 Tostada con tomate - $3.00\n🥐 Croissant - $1.80"
    
    def _show_stock(self, role):
        """Mostrar stock"""
        try:
            stats = self.catalog.get_stock_stats()
            
            if role == 'administrador':
                return (
                    f"📦 **Estado del Inventario (Admin)**\n\n"
                    f"• Total productos: {stats.get('total', 0)}\n"
                    f"• Stock bajo: {stats.get('stock_bajo', 0)}\n"
                    f"• Agotados: {stats.get('agotados', 0)}\n"
                    f"• Valor total inventario: ${stats.get('valor_total', 0):.2f}"
                )
            elif role == 'vendedor':
                return (
                    f"📦 **Stock Disponible**\n\n"
                    f"• Total productos: {stats.get('total', 0)}\n"
                    f"• Con stock: {stats.get('con_stock', 0)}\n"
                    f"• Stock bajo: {stats.get('stock_bajo', 0)}"
                )
            else:
                return f"📦 Tenemos **{stats.get('total', 0)} productos** disponibles. ¡Pregunta por cualquiera!"
        except Exception as e:
            logger.error(f"Error mostrando stock: {e}")
            return "📦 Tenemos productos disponibles. ¡Pregunta por nuestro catálogo!"
    
    def _show_products_by_category(self, category):
        """Mostrar productos por categoría"""
        names = {
            'bebidas': '☕ **Bebidas:**',
            'comida': '🥪 **Comida:**',
            'postres': '🍰 **Postres:**'
        }
        
        try:
            products = self.catalog.get_products_by_category(category)
            
            if not products:
                return f"No tenemos {category} disponibles en este momento."
            
            text = f"{names.get(category, '📦 Productos:')}\n\n"
            
            for p in products:
                nombre = p.get('nombre', 'Producto')
                precio = p.get('precio', 0)
                text += f"• {nombre} - ${precio:.2f}\n"
            
            return text
        except Exception as e:
            logger.error(f"Error mostrando categoría {category}: {e}")
            return f"Consulta nuestras {category} disponibles."
    
    def _recommend(self):
        """Dar recomendaciones"""
        recommendations = [
            "☕ **Te recomendamos:**\n\n1. Café Americano + Croissant - $4.30 (combo clásico)\n2. Cappuccino - Nuestra especialidad\n3. Zumo de naranja natural - Refrescante",
            "🌟 **Populares hoy:**\n\n1. Café Americano - El favorito\n2. Tostada con tomate - Deliciosa\n3. Cappuccino - Perfecto para la tarde",
            "🎯 **Sugerencia del día:**\n\nPrueba nuestro **Cappuccino** con un **Croissant** - ¡La combinación perfecta por solo $5.30!"
        ]
        
        return random.choice(recommendations)
    
    def _show_help(self, role):
        """Mostrar ayuda según rol"""
        if role == 'administrador':
            return (
                "📋 **Comandos disponibles (Admin):**\n\n"
                "• **stock** - Ver inventario completo\n"
                "• **productos** - Catálogo con precios y costos\n"
                "• **ventas** - Resumen de ventas\n"
                "• **usuarios** - Gestionar usuarios\n"
                "• **ayuda** - Mostrar este menú"
            )
        elif role == 'vendedor':
            return (
                "📋 **Comandos disponibles (Vendedor):**\n\n"
                "• **productos** - Ver catálogo\n"
                "• **precio [producto]** - Consultar precio\n"
                "• **stock** - Ver disponibilidad\n"
                "• **ayuda** - Mostrar este menú"
            )
        else:
            return (
                "📋 **¿En qué puedo ayudarte?**\n\n"
                "• **productos** - Ver qué tenemos\n"
                "• **precio [producto]** - Consultar precio\n"
                "• **bebidas** - Ver bebidas disponibles\n"
                "• **comida** - Ver comida disponible\n"
                "• **horario** - Horarios de atención\n"
                "• **ubicación** - Dónde estamos\n"
                "• **promociones** - Ofertas especiales\n"
                "• **recomendación** - Sugerencias"
            )


# Instancia global del agente
agent = AgentCore()
