"""Rutas API para el agente proactivo — decoradores corregidos"""
from flask import Blueprint, jsonify, session
from decorators import login_required

proactive_bp = Blueprint('proactive', __name__)

try:
    from ia.proactive_agent import get_proactive_agent, start_background_monitor
    _HAS_PROACTIVE = True
except Exception:
    _HAS_PROACTIVE = False


@proactive_bp.route('/api/ia/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Obtener todas las alertas proactivas."""
    if not _HAS_PROACTIVE:
        return jsonify({'ok': True, 'alertas': [], 'total': 0})
    agent = get_proactive_agent()
    alerts = agent.check_all()
    return jsonify({'ok': True, 'alertas': alerts, 'total': len(alerts)})


@proactive_bp.route('/api/ia/briefing', methods=['GET'])
@login_required
def get_briefing():
    """Obtener briefing proactivo."""
    usuario = session.get('usuario', {})
    rol = usuario.get('rol', 'cliente')
    if not _HAS_PROACTIVE:
        return jsonify({'ok': True, 'briefing': 'Sistema operativo.'})
    agent = get_proactive_agent()
    briefing = agent.get_briefing(rol)
    return jsonify({'ok': True, 'briefing': briefing})


@proactive_bp.route('/api/ia/alerts/start', methods=['POST'])
@login_required
def start_monitor():
    """Iniciar monitoreo en segundo plano."""
    if not _HAS_PROACTIVE:
        return jsonify({'ok': False, 'error': 'Proactive agent no disponible'})
    start_background_monitor(interval_seconds=120)
    return jsonify({'ok': True, 'mensaje': 'Monitoreo proactivo iniciado'})
