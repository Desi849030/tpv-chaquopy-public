# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status (v8.0 definitivo)."""

from flask import Blueprint, request, jsonify, session
from datetime import datetime

from anon_identity import ensure_anon_client_id, ensure_request_id, identity_payload

agent_chat_bp = Blueprint('agent_chat', __name__)

_agent = None
_agent_loaded = False
try:
    from ia.agent_master import agent as _agent
    _agent_loaded = True
except Exception as e:
    print(f"⚠️ Agente IA no disponible: {e}")


def _saludo_inteligente(rol, name):
    h = datetime.now().hour
    t = "Buenos días" if h < 12 else "Buenas tardes" if h < 19 else "Buenas noches"
    icons = {
        'vendedor': '🛒',
        'administrador': '📊',
        'desarrollador': '💻',
        'supervisor': '👁️',
        'cajero': '💵',
        'cliente': '🛍️',
    }
    icon = icons.get(rol, '👋')
    n = name or rol

    if rol == 'cliente':
        return f"{t} {icon} ¡Bienvenido a la tienda! Soy tu asistente virtual. Puedo ayudarte a buscar productos, ver precios, ofertas y disponibilidad. ¿Qué necesitas?"
    elif rol == 'vendedor':
        return f"{t} {icon} Hola {n}, soy tu copiloto de ventas. Pregúntame por tus ventas de hoy, stock, precios o productos más vendidos."
    elif rol == 'administrador':
        return f"{t} {icon} Hola Admin {n}, tengo el negocio bajo control. Pídeme balance, gastos, rendimiento del personal o inventario."
    elif rol == 'desarrollador':
        return f"{t} {icon} Root Access concedido {n}. Telemetría del sistema, integridad de BD, logs y métricas de telecomunicaciones listas."
    elif rol == 'supervisor':
        return f"{t} {icon} Hola {n}, panel de supervisión activo. Dashboard, análisis ABC, rotación y predicciones."
    else:
        return f"{t} {icon} ¡Hola! ¿En qué te ayudo?"


@agent_chat_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    d = request.get_json(silent=True) or {}
    msg = str(d.get('mensaje', '')).strip()
    name_from_req = str(d.get('nombre', '')).strip()
    request_id = ensure_request_id(request)

    usuario = session.get('usuario')
    if usuario and isinstance(usuario, dict):
        rol = usuario.get('rol', 'cliente')
        name = usuario.get('nombre') or usuario.get('username') or name_from_req
        usuario_id = usuario.get('usuario_id', '')
        anon_client_id = session.get('anon_client_id', '')
        autenticado = True
    else:
        rol = 'cliente'
        anon_client_id = ensure_anon_client_id(request, session)
        name = name_from_req or 'Cliente anónimo'
        usuario_id = anon_client_id
        autenticado = False

    saludos = ['hola', 'buenas', 'hi', 'hey', 'buenos dias', 'buenas tardes', 'buenas noches']
    if not msg or msg.lower().strip() in saludos:
        return jsonify({
            "ok": True,
            "respuesta": _saludo_inteligente(rol, name),
            "rol": rol,
            "intencion": "GREETING",
            "ui_action": None,
            "request_id": request_id,
            "anon_client_id": anon_client_id,
            "usuario_id": usuario_id,
            "autenticado": autenticado,
        })

    try:
        from ia.catalog import P, O
        if hasattr(P, 'load'):
            P.load()
        if hasattr(O, 'load'):
            O.load()
    except Exception:
        pass

    if _agent_loaded and _agent:
        try:
            result = _agent.process(text=msg, role=rol, name=name)
            tools = [f"{t.get('icon', '')} {t.get('name', '')}" for t in result.get('tools', [])]
            return jsonify({
                "ok": True,
                "respuesta": result.get('response', ''),
                "rol": rol,
                "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.85),
                "herramientas": tools,
                "ui_action": result.get('ui_action'),
                "request_id": request_id,
                "anon_client_id": anon_client_id,
                "usuario_id": usuario_id,
                "autenticado": autenticado,
            })
        except Exception as e:
            print(f"Agent error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "ok": True,
                "respuesta": _saludo_inteligente(rol, name),
                "rol": rol,
                "ui_action": None,
                "request_id": request_id,
                "anon_client_id": anon_client_id,
                "usuario_id": usuario_id,
                "autenticado": autenticado,
            })

    return jsonify({
        "ok": True,
        "respuesta": _saludo_inteligente(rol, name) + " (Motor IA no disponible, modo catálogo)",
        "rol": rol,
        "ui_action": None,
        "request_id": request_id,
        "anon_client_id": anon_client_id,
        "usuario_id": usuario_id,
        "autenticado": autenticado,
    })


@agent_chat_bp.route('/api/agent/status')
def agent_status():
    status = {"ok": True, "agent": "fallback", "version": "8.0", "request_id": ensure_request_id(request)}
    if _agent_loaded and _agent:
        try:
            status["agent"] = "active"
            status["details"] = _agent.get_status()
        except Exception:
            status["agent"] = "active"
    return jsonify(status)


@agent_chat_bp.route('/api/agent/identity')
def agent_identity():
    """El frontend llama esto al cargar la página para saber quién es el usuario."""
    return jsonify(identity_payload(request, session))


def is_agent_loaded():
    return _agent_loaded
