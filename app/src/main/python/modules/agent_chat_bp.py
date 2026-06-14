# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status
El agente es PÚBLICO (no requiere login): antes del login trata a todos
como 'cliente'. Después del login usa el rol real de la sesión."""

from flask import Blueprint, request, jsonify, session
from datetime import datetime

agent_chat_bp = Blueprint('agent_chat', __name__)

# Cargar agente IA (si está disponible)
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
        return f"¡{tiempo}{', ' + name if name else ''}! Soy tu Asistente Inteligente. ¿Buscas algún producto o precio?"
    elif rol == 'vendedor':
        return f"¡{tiempo}, {name or 'equipo'}! Listo para vender. Puedo consultar stock, precios o registrar atajos."
    elif rol == 'administrador':
        return f"¡{tiempo} Admin {name}! Sistemas operativos. Pídeme resúmenes de ganancias o inventario crítico."
    else:
        return f"¡{tiempo} {name or rol}! ¿En qué te ayudo hoy?"


@agent_chat_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    d = request.get_json(silent=True) or {}
    msg = str(d.get('mensaje', '')).strip()
    name_from_req = str(d.get('nombre', '')).strip()

    usuario = session.get('usuario')
    
    # Resolver identidad
    if usuario and isinstance(usuario, dict):
        rol = usuario.get('rol', 'cliente')
        name = usuario.get('nombre') or usuario.get('username') or name_from_req
        sid = usuario.get('usuario_id', 'anon')
    else:
        rol = 'cliente'
        name = name_from_req
        sid = request.remote_addr or 'anon_client'

    # Inyección de personalidad inicial (si manda mensaje vacío o dice "hola")
    if not msg or msg.lower() in ['hola', 'buenas', 'hi']:
        return jsonify({
            "ok": True, 
            "respuesta": _saludo_inteligente(rol, name), 
            "rol": rol,
            "intencion": "GREETING"
        })

    if _agent_loaded and _agent:
        try:
            # FIX CRÍTICO: Pasamos los argumentos por nombre para no cruzar SID con ROLE
            result = _agent.process(text=msg, sid=sid, role=rol, name=name)
            
            tools = [f"{t.get('icon', '')} {t.get('name', '')}" for t in result.get('tools', [])]
            
            return jsonify({
                "ok": True, 
                "respuesta": result.get('response', ''),
                "rol": rol, 
                "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.9),
                "herramientas": tools,
            })
        except Exception as e:
            print(f"Agent error: {e}")
            return jsonify({
                "ok": False,
                "respuesta": f"❌ Error procesando tu solicitud: {str(e)}",
                "rol": rol
            }), 500

    # Fallback si el motor IA está apagado
    return jsonify({
        "ok": True, 
        "respuesta": _saludo_inteligente(rol, name) + " (Modo simplificado)", 
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
