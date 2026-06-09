# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status
El agente es PÚBLICO (no requiere login): antes del login trata a todos
como 'cliente' (solo info de productos, precios, ofertas).
Después del login usa el rol real de la sesión."""
from flask import Blueprint, request, jsonify, session

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
    """Chat con el agente IA.
    NO requiere login: antes de autenticarse, el usuario es tratado como
    'cliente' y solo puede preguntar por productos, precios y ofertas.
    Después del login se usa el rol real de la sesión."""
    d = request.get_json(silent=True) or {}
    msg = d.get('mensaje', '')
    name = d.get('nombre', '')

    # Determinar rol: si hay sesión activa, usar rol real; si no, 'cliente'
    usuario = session.get('usuario')
    if usuario and isinstance(usuario, dict):
        rol = usuario.get('rol', 'cliente')
        if not name:
            name = usuario.get('nombre', usuario.get('username', ''))
    else:
        # Sin sesión = pantalla de login = tratar como cliente
        rol = 'cliente'
        # Ignorar el rol que envíe el frontend sin sesión (seguridad)

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

    # Fallback: saludo genérico según rol
    if rol == 'cliente':
        resp = (f"¡Hola{', ' + name if name else ''}! Soy el asistente del TPV. "
                "Puedo ayudarte con información de productos, precios y ofertas. "
                "¿Qué te interesa?")
    else:
        resp = (f"¡Hola {name or rol}! Soy tu asistente IA. "
                "¿En qué puedo ayudarte?")

    return jsonify({"ok": True, "respuesta": resp, "rol": rol})


@agent_chat_bp.route('/api/agent/status')
def agent_status():
    """Estado del agente IA."""
    return jsonify({
        "ok": True,
        "agent": "active" if _agent_loaded else "fallback",
        "version": "3.0",
    })


def is_agent_loaded():
    """Helper para que otros módulos consulten el estado del agente."""
    return _agent_loaded
