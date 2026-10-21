# -*- coding: utf-8 -*-
"""Agent Master v3 — Orquestador profesional del agente IA."""
from __future__ import annotations
import logging, json, uuid, os, sys
from typing import Optional, Dict, Any
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

_SENSITIVE_PATTERNS = (
    "drop table",
    "delete from",
    "truncate table",
    "password_hash",
    "password_salt",
    "secret_key",
    "root access",
    "variables de entorno",
    "clave secreta",
    "hashes de usuarios",
    "password de admin",
)


class AgentMaster:
    """Orquestador profesional del agente IA conversacional."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.conversation_context: Dict[str, Any] = {}

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado operativo verificable del orquestador."""
        return {
            "ok": True,
            "session_id": self.session_id,
            "nlp_active": classifier is not None,
            "guardrails_active": guardrails_pro is not None,
            "memory_active": advanced_memory is not None,
            "db_active": get_connection is not None,
        }

    def process(self, message: Optional[str] = None, user_id: str = "anonimo",
                role: str = "cliente", text: Optional[str] = None,
                name: Optional[str] = None) -> Dict[str, Any]:
        """Procesar mensaje y generar respuesta profesional segura por rol."""
        raw_msg = message if message is not None else (text if text is not None else "")
        effective_uid = user_id if user_id != "anonimo" else (name or "anonimo")

        lowered = raw_msg.lower()
        if any(pat in lowered for pat in _SENSITIVE_PATTERNS):
            return {
                "ok": True,
                "response": "Solicitud bloqueada por política de seguridad y mínimo privilegio.",
                "intent": "bloqueado",
                "confidence": 1.0,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            }

        if guardrails_pro:
            check = guardrails_pro.check_input(raw_msg, effective_uid, role)
            if not check["allowed"]:
                return {
                    "ok": True,
                    "response": "⚠️ " + check["blocks"][0],
                    "intent": "bloqueado",
                    "confidence": 1.0,
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat(),
                }
            clean_msg = check["sanitized"]
        else:
            clean_msg = raw_msg

        intent = "ayuda"
        if classifier and clean_msg.strip():
            intent, confidence = classifier.get_primary_intent(clean_msg)
        else:
            confidence = 0.5

        entities = {}
        if extractor and clean_msg.strip():
            entities = {
                "products": extractor.extract_products(clean_msg),
                "price": extractor.extract_price(clean_msg),
                "quantity": extractor.extract_quantity(clean_msg),
            }

        if advanced_memory and clean_msg.strip():
            advanced_memory.save_conversation(
                user_id=effective_uid, session_id=self.session_id,
                role="user", content=clean_msg[:1000], intent=intent,
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
            response = tool(clean_msg, effective_uid, role, entities)
        except Exception as e:
            logger.error("Error en tool %s: %s", intent, e)
            response = self._tool_fallback(clean_msg)

        if guardrails_pro:
            valid, _ = guardrails_pro.check_output(response)
            if not valid:
                response = "Lo siento, no puedo proporcionar esa información."

        if advanced_memory and clean_msg.strip():
            advanced_memory.save_conversation(
                user_id=effective_uid, session_id=self.session_id,
                role="assistant", content=response, intent=intent,
            )

        return {
            "ok": True,
            "response": response,
            "intent": intent or "ayuda",
            "confidence": round(confidence, 2),
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _tool_buscar_producto(self, msg, uid, role, entities):
        """Buscar productos en el catálogo."""
        query = (entities["products"][0] if entities.get("products") else msg.lower()).strip()[:80]
        if get_connection and query:
            conn = None
            try:
                conn = get_connection()
                cursor = conn.execute(
                    "SELECT nombre, precio, stock_actual FROM productos p "
                    "LEFT JOIN inventario_general i ON p.producto_id = i.producto_id "
                    "WHERE p.nombre LIKE ? AND p.activo = 1 LIMIT 10",
                    ("%" + query + "%",),
                )
                products = [dict(r) for r in cursor.fetchall()]
                if products:
                    lines = []
                    for p in products:
                        stock = p.get("stock_actual", "N/A")
                        precio = p.get("precio", 0)
                        lines.append(f"  - {p['nombre']} — {precio} u.m. (stock: {stock})")
                    return f"Encontré {len(products)} producto(s):\n" + "\n".join(lines)
                return "No encontré coincidencias en el catálogo para esa búsqueda."
            except Exception as e:
                logger.error("Error buscando: %s", e)
                return "Error al consultar el catálogo local."
            finally:
                if conn is not None:
                    conn.close()
        return "Indica el nombre del producto que deseas buscar."

    def _tool_consultar_precio(self, msg, uid, role, entities):
        """Consultar precio de un producto."""
        if entities.get("products") and get_connection:
            product = entities["products"][0]
            conn = None
            try:
                conn = get_connection()
                cursor = conn.execute(
                    "SELECT nombre, precio FROM productos WHERE nombre LIKE ? AND activo=1",
                    ("%" + product + "%",),
                )
                p = cursor.fetchone()
                if p:
                    return f"Precio de {p['nombre']}: {p['precio']} u.m."
                return "No encontré ese producto activo en el catálogo."
            except Exception as e:
                logger.error("Error precio: %s", e)
            finally:
                if conn is not None:
                    conn.close()
        return "¿Qué producto te gustaría consultar?"

    def _tool_ver_stock(self, msg, uid, role, entities):
        """Consultar stock de un producto."""
        if entities.get("products") and get_connection:
            product = entities["products"][0]
            conn = None
            try:
                conn = get_connection()
                cursor = conn.execute(
                    "SELECT nombre, stock_actual, stock_minimo FROM inventario_general WHERE nombre LIKE ? LIMIT 1",
                    ("%" + product + "%",),
                )
                p = cursor.fetchone()
                if p:
                    stock = p["stock_actual"]
                    minimo = p["stock_minimo"]
                    status = "stock bajo" if stock <= minimo else "stock OK"
                    return f"Stock de {p['nombre']}: {stock} unidades ({status})"
                return "No encontré ese artículo en el inventario."
            except Exception as e:
                logger.error("Error stock: %s", e)
            finally:
                if conn is not None:
                    conn.close()
        return "¿De qué producto quieres verificar el stock?"

    def _tool_vender(self, msg, uid, role, entities):
        if role in ("cliente",):
            return "Para registrar ventas necesitas iniciar sesión como vendedor o cajero."
        return "Función de venta disponible en el módulo de caja."

    def _tool_reporte_ventas(self, msg, uid, role, entities):
        if role in ("cliente",):
            return "Los reportes operativos están reservados al personal autorizado."
        return "Puedes consultar los reportes detallados en el panel de ventas."

    def _tool_saludo(self, msg, uid, role, entities):
        saludos = {
            "desarrollador": "¡Bienvenido! Panel de desarrollo y diagnóstico activo.",
            "administrador": "¡Hola! ¿En qué puedo ayudarte con la administración?",
            "supervisor": "¡Buen día! Reportes y control de inventario disponibles.",
            "vendedor": "¡Hola! ¿Necesitas apoyo con una venta o consulta de stock?",
            "cajero": "¡Bienvenido! Caja lista para operar.",
            "cliente": "¡Bienvenido! Estoy aquí para ayudarte a consultar productos y ofertas.",
        }
        return saludos.get(role, "¡Hola! ¿En qué puedo ayudarte?")

    def _tool_ayuda(self, msg, uid, role, entities):
        return (
            "Asistente TPV Ultra Smart\n\n"
            "Puedo ayudarte con:\n"
            "  - Buscar productos: 'buscar café'\n"
            "  - Consultar precios: 'cuánto cuesta el arroz'\n"
            "  - Ver stock: 'hay stock de leche'\n"
            "  - Vender: 'registrar venta' (requiere sesión)\n"
            "  - Reportes: 'ventas del día'\n\n"
            "¿Qué deseas consultar?"
        )

    def _tool_fallback(self, msg):
        return (
            "No entendí completamente tu mensaje. "
            "Puedes preguntarme por productos, precios, stock, "
            "ventas y reportes. Escribe 'ayuda' para más opciones."
        )


agent_master = AgentMaster()
agent = agent_master
