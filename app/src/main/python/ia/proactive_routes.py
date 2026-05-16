"""Rutas API para el agente proactivo"""
from flask import Blueprint, jsonify, session
from ia.proactive_agent import get_proactive_agent, start_background_monitor

proactive_bp = Blueprint('proactive', __name__)

@proactive_bp.route('/api/ia/alerts', methods=['GET'])
def get_alerts():
    """Obtener todas las alertas proactivas"""
    agent = get_proactive_agent()
    alerts = agent.check_all()
    return jsonify({'ok': True, 'alertas': alerts, 'total': len(alerts)})

@proactive_bp.route('/api/ia/briefing', methods=['GET'])
def get_briefing():
    """Obtener briefing proactivo"""
    usuario = session.get('usuario', {})
    rol = usuario.get('rol', 'cliente')
    agent = get_proactive_agent()
    briefing = agent.get_briefing(rol)
    return jsonify({'ok': True, 'briefing': briefing})

@proactive_bp.route('/api/ia/alerts/start', methods=['POST'])
def start_monitor():
    """Iniciar monitoreo en segundo plano"""
    start_background_monitor(interval_seconds=120)
    return jsonify({'ok': True, 'mensaje': 'Monitoreo proactivo iniciado'})
