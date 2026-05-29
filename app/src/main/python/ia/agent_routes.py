# -*- coding: utf-8 -*-
"""
Agente IA Proactivo - Rutas Flask
"""
from flask import Blueprint, request, jsonify, session
from ia.agent_core import agent

agent_bp = Blueprint('agent', __name__)


@agent_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json() or {}
        
        user_text = data.get('message', '').strip()
        role = data.get('role', session.get('role', 'cliente'))
        user_name = data.get('nombre', session.get('nombre', ''))
        session_id = data.get('session_id', session.get('session_id', ''))
        
        if not user_text:
            return jsonify({'error': 'Mensaje vacío', 'code': 400}), 400
        
        result = agent.process_message(
            text=user_text,
            role=role,
            user_name=user_name,
            session_id=session_id
        )
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'code': 500}), 500


@agent_bp.route('/chat-direct', methods=['POST'])
def chat_direct():
    return chat()


@agent_bp.route('/query', methods=['POST'])
def query():
    return chat()


@agent_bp.route('/suggestions', methods=['GET'])
def suggestions():
    sugerencias = [
        "¿Qué productos tienen?",
        "¿Cuánto cuesta el café?",
        "¿Tienen bebidas?",
        "¿Cuál es su horario?",
        "¿Dónde están ubicados?",
        "¿Tienen promociones hoy?",
        "¿Qué me recomiendas?"
    ]
    return jsonify({'suggestions': sugerencias})


@agent_bp.route('/suggestions', methods=['POST'])
def personalized_suggestions():
    try:
        data = request.get_json() or {}
        history = data.get('history', [])
        sugerencias = [
            "¿Qué productos tienen?",
            "¿Cuánto cuesta el café?",
            "¿Tienen bebidas?"
        ]
        return jsonify({'suggestions': sugerencias})
    except:
        return jsonify({'suggestions': []})


@agent_bp.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'modules': {
            'nlp': True,
            'memory': True,
            'proactive': True,
            'guardrails': True
        }
    })


@agent_bp.route('/alerts', methods=['GET'])
def alerts():
    return jsonify({'alerts': []})


@agent_bp.route('/memory/<session_id>', methods=['GET'])
def memory(session_id):
    history = agent.memory.get(session_id, [])
    return jsonify({
        'session_id': session_id,
        'history': history[-10:]
    })
