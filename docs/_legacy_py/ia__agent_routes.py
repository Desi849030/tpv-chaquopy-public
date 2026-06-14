# -*- coding: utf-8 -*-
"""
Agente IA Proactivo - Rutas Flask
Incluye: chat, status, fuzzy-search, metrics, memory, guide, react
"""
from flask import Blueprint, request, jsonify, session

# Intentar importar agent_master primero, sino agent_core
try:
    from ia.agent_master import agent
except Exception:
    try:
        from ia.agent_core import agent
    except Exception:
        agent = None

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
        
        if agent is None:
            return jsonify({'error': 'Agente IA no disponible', 'code': 503}), 503

        # AgentMaster usa process(), AgentCore usa process_message()
        if hasattr(agent, 'process'):
            result = agent.process(
                text=user_text,
                role=role,
                user_name=user_name,
                session_id=session_id
            )
        elif hasattr(agent, 'process_message'):
            result = agent.process_message(
                text=user_text,
                role=role,
                user_name=user_name,
                session_id=session_id
            )
        else:
            return jsonify({'error': 'Agente sin metodo de procesamiento', 'code': 500}), 500
        
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
    # Intentar obtener sugerencias contextuales del skill registry
    try:
        if agent and hasattr(agent, 'skill_registry') and agent.skill_registry:
            role = session.get('role', 'cliente')
            skills_info = agent.skill_registry.get_skills_info(role)
            if skills_info:
                sugerencias = [f"{s['icon']} {s['desc']}" for s in skills_info[:7]]
    except Exception:
        pass
    return jsonify({'suggestions': sugerencias})


@agent_bp.route('/suggestions', methods=['POST'])
def personalized_suggestions():
    try:
        data = request.get_json() or {}
        history = data.get('history', [])
        role = data.get('role', session.get('role', 'cliente'))
        sugerencias = [
            "¿Qué productos tienen?",
            "¿Cuánto cuesta el café?",
            "¿Tienen bebidas?"
        ]
        # Sugerencias basadas en rol usando role_guidance
        try:
            from ia.role_guidance import ROLE_MISSIONS
            missions = ROLE_MISSIONS.get(role, {})
            ayuda = missions.get('ayuda', [])
            if ayuda:
                sugerencias = ayuda[:5]
        except Exception:
            pass
        return jsonify({'suggestions': sugerencias})
    except Exception:
        return jsonify({'suggestions': []})


# ================================================================
# NUEVOS ENDPOINTS - Modulos IA conectados
# ================================================================

@agent_bp.route('/status', methods=['GET'])
def status():
    """GET /api/ia/status - Estado de todos los modulos IA."""
    if agent and hasattr(agent, 'get_status'):
        return jsonify(agent.get_status())
    # Fallback basico
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


@agent_bp.route('/fuzzy-search', methods=['POST'])
def fuzzy_search():
    """POST /api/ia/fuzzy-search - Busqueda difusa de productos."""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        threshold = data.get('threshold', 55)
        
        if not query:
            return jsonify({'error': 'Query vacío', 'code': 400}), 400
        
        if agent and hasattr(agent, 'fuzzy_search_products'):
            result = agent.fuzzy_search_products(query, threshold)
            return jsonify(result)
        
        # Fallback directo con fuzzy_match
        try:
            from ia.fuzzy_match import best_match, build_index
            # Intentar obtener productos de BD
            product_names = []
            try:
                from db_connection import obtener_conexion
                conn = obtener_conexion()
                c = conn.cursor()
                c.execute("SELECT nombre FROM productos WHERE activo=1")
                product_names = [r[0] for r in c.fetchall()]
                conn.close()
            except Exception:
                pass
            
            if product_names:
                build_index(product_names)
                match, score = best_match(query, product_names, threshold=threshold)
                if match:
                    return jsonify({'results': [{'name': match, 'score': round(score, 1)}], 'query': query})
            return jsonify({'results': [], 'query': query})
        except Exception as e:
            return jsonify({'results': [], 'query': query, 'error': str(e)})
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@agent_bp.route('/metrics', methods=['GET'])
def metrics():
    """GET /api/ia/metrics - Metricas de uso de la IA."""
    if agent and hasattr(agent, 'get_metrics'):
        return jsonify(agent.get_metrics())
    return jsonify({'total_queries': 0, 'by_role': {}, 'by_intent': {}})


@agent_bp.route('/memory', methods=['GET'])
def memory_list():
    """GET /api/ia/memory - Ver memoria de sesion."""
    session_id = request.args.get('session_id', 'default')
    category = request.args.get('category', None)
    limit = request.args.get('limit', 20, type=int)
    
    if agent and hasattr(agent, 'get_memory'):
        memories = agent.get_memory(session_id, category=category, limit=limit)
        summary = {}
        if hasattr(agent, 'get_memory_summary'):
            summary = agent.get_memory_summary(session_id)
        return jsonify({
            'session_id': session_id,
            'memories': memories if isinstance(memories, list) else [memories],
            'summary': summary
        })
    
    # Fallback con agent_core
    if agent and hasattr(agent, 'memory'):
        history = agent.memory.get(session_id, [])
        return jsonify({
            'session_id': session_id,
            'history': history[-limit:]
        })
    
    return jsonify({'session_id': session_id, 'memories': []})


@agent_bp.route('/memory', methods=['DELETE'])
def memory_clear():
    """DELETE /api/ia/memory - Limpiar memoria de sesion."""
    data = request.get_json() or {}
    session_id = data.get('session_id', request.args.get('session_id', 'default'))
    category = data.get('category', None)
    
    if agent and hasattr(agent, 'clear_memory'):
        success = agent.clear_memory(session_id, category=category)
        return jsonify({'success': success, 'session_id': session_id})
    
    # Fallback con agent_core
    if agent and hasattr(agent, 'memory'):
        agent.memory.clear(session_id)
        return jsonify({'success': True, 'session_id': session_id})
    
    return jsonify({'success': False, 'error': 'No hay agente disponible'})


@agent_bp.route('/guide', methods=['GET'])
def guide():
    """GET /api/ia/guide - Guia contextual para el rol y pantalla."""
    role = request.args.get('role', session.get('role', 'cliente'))
    screen_id = request.args.get('screen_id', None)
    
    if agent and hasattr(agent, 'get_guide'):
        return jsonify({'guide': agent.get_guide(role, screen_id)})
    
    return jsonify({'guide': '🤖 ¿En qué puedo ayudarle?'})


@agent_bp.route('/react', methods=['POST'])
def react_query():
    """POST /api/ia/react - Consulta con motor ReAct (razonamiento multi-paso)."""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        plan_name = data.get('plan', None)
        role = data.get('role', 'vendedor')
        
        if not query and not plan_name:
            return jsonify({'error': 'Query o plan requerido', 'code': 400}), 400
        
        if agent and hasattr(agent, 'react_query'):
            result = agent.react_query(query, plan_name=plan_name, role=role)
            return jsonify(result)
        
        return jsonify({'error': 'Motor ReAct no disponible', 'code': 503}), 503
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@agent_bp.route('/alerts', methods=['GET'])
def alerts():
    """Alertas del sistema."""
    alerts_list = []
    # Detectar frustracion si fuzzy_match esta disponible
    try:
        from ia.fuzzy_match import contains_frustration
    except Exception:
        pass
    return jsonify({'alerts': alerts_list})


@agent_bp.route('/memory/<session_id>', methods=['GET'])
def memory_by_session(session_id):
    """Ver historial de una sesion especifica."""
    if agent and hasattr(agent, 'get_memory'):
        memories = agent.get_memory(session_id)
        return jsonify({
            'session_id': session_id,
            'memories': memories if isinstance(memories, list) else [memories]
        })
    
    # Fallback con agent_core
    if agent and hasattr(agent, 'memory'):
        history = agent.memory.get(session_id, [])
        return jsonify({
            'session_id': session_id,
            'history': history[-10:]
        })
    
    return jsonify({'session_id': session_id, 'memories': []})
