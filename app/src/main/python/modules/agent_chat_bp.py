# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime

agent_chat_bp = Blueprint('agent_chat', __name__)

_agent = None
_agent_loaded = False
try:
    from ia.agent_master import agent as _agent
    _agent_loaded = True
except Exception as e:
    print(f"⚠️ Agente IA no disponible: {e}")

def _saludo_inteligente(rol, name):
    hora = datetime.now().hour
    tiempo = "Buenos días" if 5 <= hora < 12 else "Buenas tardes" if 12 <= hora < 20 else "Buenas noches"
    
    if rol == 'cliente':
        return f"¡{tiempo}{', ' + name if name else ''}! 👋 Soy el Asistente Virtual de la tienda. Puedo ayudarte a buscar productos, ver precios, consultar ofertas disponibles y decirte dónde encontrarnos. ¿Qué estás buscando hoy?"
    elif rol == 'vendedor':
        return f"¡{tiempo}, {name or 'equipo'}! 🛒 Listo para vender. Pregúntame por tus ventas de hoy, busca productos rápido o verifica stock crítico."
    elif rol == 'administrador':
        return f"¡{tiempo} Admin {name}! 📈 Sistemas operativos. Pídeme resúmenes de ganancias, gastos o rendimiento del personal."
    elif rol == 'desarrollador':
        return f"¡{tiempo} {name}! 💻 Root Access concedido. Pídeme el estado del sistema, integridad de la base de datos o logs."
    else:
        return f"¡{tiempo} {name or rol}! ¿En qué te ayudo hoy?"

@agent_chat_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    d = request.get_json(silent=True) or {}
    msg = str(d.get('mensaje', '')).strip()
    name_from_req = str(d.get('nombre', '')).strip()

    usuario = session.get('usuario')
    
    # Si hay sesión, usa el rol real. Si no, es un cliente visitante.
    if usuario and isinstance(usuario, dict):
        rol = usuario.get('rol', 'cliente')
        name = usuario.get('nombre') or usuario.get('username') or name_from_req
    else:
        rol = 'cliente'
        name = name_from_req

    # Inyección de personalidad inicial si el usuario solo entra o saluda
    if not msg or msg.lower() in ['hola', 'buenas', 'hi', 'ayuda', 'menu']:
        return jsonify({
            "ok": True, 
            "respuesta": _saludo_inteligente(rol, name), 
            "rol": rol,
            "intencion": "GREETING"
        })

    
    # ⚡ Sincronización Atómica: Refrescar caché de la IA desde SQLite
    try:
        from ia.catalog import P, O
        if hasattr(P, 'load'): P.load()
        if hasattr(O, 'load'): O.load()
    except Exception as e:
        print("Aviso sync IA:", e)

    if _agent_loaded and _agent:
        try:
            # FIX CRÍTICO: Llamamos al AgentMaster exactamente como lo espera (sin sid)
            result = _agent.process(msg, rol, name)
            
            tools = [f"{t.get('icon', '')} {t.get('name', '')}" for t in result.get('tools', [])]
            
            return jsonify({
                "ok": True, 
                "respuesta": result.get('response', ''),
                "rol": rol, 
                "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.9),
                "herramientas": tools,
                "ui_action": result.get("ui_action"),
            })
        except Exception as e:
            print(f"Agent error: {e}")
            return jsonify({
                "ok": False,
                "respuesta": f"❌ Hubo un error procesando tu solicitud, pero sigo aquí para ayudarte.",
                "rol": rol
            }), 500

    # Fallback si falla el motor IA
    return jsonify({
        "ok": True, 
        "respuesta": _saludo_inteligente(rol, name) + " (Modo catálogo básico)", 
        "rol": rol
    })

@agent_chat_bp.route('/api/agent/status')
def agent_status():
    return jsonify({
        "ok": True,
        "agent": "active" if _agent_loaded else "fallback",
        "version": "8.0-smart",
    })

def is_agent_loaded():
    return _agent_loaded
