# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status"""
from flask import Blueprint, request, jsonify

agent_chat_bp = Blueprint('agent_chat', __name__)

# Cargar agente IA (si está disponible)
_agent = None
_agent_loaded = False
try:
    from ia.agent_master import agent as _agent
    _agent_loaded = True
except Exception as e:
    print(f"⚠️ Agente IA no disponible: {e}")


@agent_chat_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    d = request.get_json(silent=True) or {}
    msg = d.get('mensaje', '')
    rol = d.get('rol', 'vendedor')
    name = d.get('nombre', '')
    if _agent_loaded and _agent and msg:
        try:
            result = _agent.process(msg, rol, name)
            tools = [f"{t.get('icon', '')} {t.get('name', '')}"
                     for t in result.get('tools', [])]
            return jsonify({
                "ok": True, "respuesta": result.get('response', ''),
                "rol": rol, "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.9),
                "herramientas": tools,
            })
        except Exception as e:
            print(f"Agent error: {e}")
    return jsonify({
        "ok": True,
        "respuesta": f"Hola {name or rol}, soy el Agente IA del TPV. ¿En qué puedo ayudarte?",
        "rol": rol,
    })


@agent_chat_bp.route('/api/agent/status')
def agent_status():
    return jsonify({
        "ok": True,
        "agent": "active" if _agent_loaded else "fallback",
        "version": "3.0",
    })


def is_agent_loaded():
    """Helper para que otros módulos consulten el estado del agente."""
    return _agent_loaded
