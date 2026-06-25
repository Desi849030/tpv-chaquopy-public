"""Agent Master v3 — Orquestador profesional del agente IA."""
from __future__ import annotations
import logging, json, uuid, os, sys
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from ia.nlp_engine import classifier, extractor, responder
except ImportError:
    classifier = None; extractor = None; responder = None

try:
    from ia.memory_advanced import advanced_memory
except ImportError:
    advanced_memory = None

try:
    from ia.guardrails_pro import guardrails_pro
except ImportError:
    guardrails_pro = None

try:
    from db_connection import get_connection
except ImportError:
    get_connection = None


class AgentMaster:
    """Orquestador profesional del agente IA conversacional."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.conversation_context: Dict[str, Any] = {}

    def process(self, message: str, user_id: str = "anonimo",
                role: str = "cliente") -> Dict:
        """Procesar mensaje y generar respuesta profesional."""

        if guardrails_pro:
            check = guardrails_pro.check_input(message, user_id, role)
            if not check["allowed"]:
                return {
                    "ok": True,
                    "response": "⚠️ " + check["blocks"][0],
                    "intent": "bloqueado",
                    "session_id": self.session_id,
                }
            message = check["sanitized"]

        intent = "ayuda"
        if classifier:
            intent, confidence = classifier.get_primary_intent(message)
        else:
            confidence = 0.5

        entities = {}
        if extractor:
            entities = {
                "products": extractor.extract_products(message),
                "price": extractor.extract_price(message),
                "quantity": extractor.extract_quantity(message),
            }

        if advanced_memory:
            advanced_memory.save_conversation(
                user_id=user_id, session_id=self.session_id,
                role="user", content=message, intent=intent,
                entities=json.dumps(entities),
            )

        tool_map = {
            "buscar_producto": self._tool_buscar_producto,
            "consultar_precio": self._tool_consultar_precio,
            "ver_stock": self._tool_ver_stock,
            "vender": self._tool_vender,
            "reporte_ventas": self._tool_reporte_ventas,
            "saludo": self._tool_saludo,
            "ayuda": self._tool_ayuda,
        }
        tool = tool_map.get(intent, self._tool_ayuda)
        try:
            response = tool(message, user_id, role, entities)
        except Exception as e:
            logger.error("Error en tool %s: %s", intent, e)
            response = self._tool_fallback(message)

        if guardrails_pro:
            valid, msg = guardrails_pro.check_output(response)
            if not valid:
                response = "Lo siento, no puedo proporcionar esa informacion."

        if advanced_memory:
            advanced_memory.save_conversation(
                user_id=user_id, session_id=self.session_id,
                role="assistant", content=response, intent=intent,
            )

        return {
            "ok": True,
            "response": response,
            "intent": intent,
            "confidence": round(confidence, 2),
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _tool_buscar_producto(self, msg, uid, role, entities):
        """Buscar productos en el catalogo."""
        query = msg.lower()
        if entities.get("products"):
            query = entities["products"][0]
        if get_connection:
            try:
                conn = get_connection()
                cursor = conn.execute(
                    "SELECT nombre, precio, stock_actual FROM productos p "
                    "LEFT JOIN inventario_general i ON p.producto_id = i.producto_id "
                    "WHERE p.nombre LIKE ? AND p.activo = 1 LIMIT 10",
                    ("%" + query + "%",)
                )
                products = [dict(r) for r in cursor.fetchall()]
                conn.close()
                if products:
                    lines = []
                    for p in products:
                        stock = p.get("stock_actual", "N/A")
                        precio = p.get("precio", 0)
                        lines.append("  - " + p["nombre"] + " — " + str(precio) + " MXN (stock: " + str(stock) + ")")
                    return "Encontre " + str(len(products)) + " producto(s):\n" + "\n".join(lines)
                else:
                    return "No encontre productos para '" + query + "'. Intenta con otra palabra."
            except Exception as e:
                logger.error("Error buscando: %s", e)
                return "Error al buscar. Intenta de nuevo."
        return "Buscando en el catalogo..."

    def _tool_consultar_precio(self, msg, uid, role, entities):
        """Consultar precio de un producto."""
        if entities.get("products"):
            product = entities["products"][0]
            if get_connection:
                try:
                    conn = get_connection()
                    cursor = conn.execute(
                        "SELECT nombre, precio FROM productos WHERE nombre LIKE ? AND activo=1",
                        ("%" + product + "%",)
                    )
                    p = cursor.fetchone()
                    conn.close()
                    if p:
                        return "Precio de " + p["nombre"] + ": " + str(p["precio"]) + " MXN"
                    return "No encontre '" + product + "' en el catalogo."
                except Exception as e:
                    logger.error("Error precio: %s", e)
        return "Que producto te gustaria consultar?"

    def _tool_ver_stock(self, msg, uid, role, entities):
        """Consultar stock de un producto."""
        if entities.get("products"):
            product = entities["products"][0]
            if get_connection:
                try:
                    conn = get_connection()
                    cursor = conn.execute(
                        "SELECT nombre, stock_actual, stock_minimo FROM inventario_general WHERE nombre LIKE ? LIMIT 1",
                        ("%" + product + "%",)
                    )
                    p = cursor.fetchone()
                    conn.close()
                    if p:
                        stock = p["stock_actual"]
                        minimo = p["stock_minimo"]
                        status = "stock bajo" if stock <= minimo else "stock OK"
                        return "Stock de " + p["nombre"] + ": " + str(stock) + " unidades (" + status + ")"
                    return "No encontre '" + product + "' en inventario."
                except Exception as e:
                    logger.error("Error stock: %s", e)
        return "De que producto quieres ver el stock?"

    def _tool_vender(self, msg, uid, role, entities):
        if role in ("cliente",):
            return "Para vender necesitas iniciar sesion como vendedor o cajero."
        return "Funcion de venta disponible en el modulo de caja."

    def _tool_reporte_ventas(self, msg, uid, role, entities):
        if role in ("cliente",):
            return "Los reportes son para personal autorizado."
        return "Puedes ver los reportes en el panel de ventas."

    def _tool_saludo(self, msg, uid, role, entities):
        saludos = {
            "desarrollador": "Bienvenido! Panel de desarrollo activo.",
            "administrador": "Hola! En que puedo ayudarte con la administracion?",
            "supervisor": "Buen dia! Reportes y dashboard disponibles.",
            "vendedor": "Hola! Necesitas ayuda con una venta?",
            "cajero": "Bienvenido! Caja lista para operar.",
            "cliente": "Bienvenido! Estoy aqui para ayudarte a encontrar productos.",
        }
        return saludos.get(role, "Hola! En que puedo ayudarte?")

    def _tool_ayuda(self, msg, uid, role, entities):
        return (
            "Asistente TPV Ultra Smart\n\n"
            "Puedo ayudarte con:\n"
            "  - Buscar productos: 'buscar cafe'\n"
            "  - Consultar precios: 'cuanto cuesta el arroz'\n"
            "  - Ver stock: 'hay stock de leche'\n"
            "  - Vender: 'registrar venta' (requiere sesion)\n"
            "  - Reportes: 'ventas del dia'\n\n"
            "Que deseas hacer?"
        )

    def _tool_fallback(self, msg):
        return (
            "No entendi completamente tu mensaje. "
            "Puedes preguntarme por productos, precios, stock, "
            "ventas y reportes. Escribe 'ayuda' para mas opciones."
        )


agent_master = AgentMaster()
