# -*- coding: utf-8 -*-
"""telecom_bp.py v8.2 - Endpoints /api/dev/telecom/* (solo desarrollador)."""

from flask import Blueprint, jsonify, request, session
from functools import wraps

telecom_bp = Blueprint('telecom_dev', __name__)


def _dev_required(f):
    """Decorador: solo desarrolladores acceden."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = session.get('usuario') or {}
        if u.get('rol') != 'desarrollador':
            return jsonify({"ok": False, "error": "Solo desarrollador"}), 403
        return f(*args, **kwargs)
    return wrapper


@telecom_bp.route('/api/dev/telecom/latencia', methods=['GET'])
@_dev_required
def api_latencia():
    from modules.telecom_diag import medir_latencia_supabase
    intentos = int(request.args.get('intentos', 5))
    return jsonify(medir_latencia_supabase(intentos=intentos))


@telecom_bp.route('/api/dev/telecom/throughput', methods=['GET'])
@_dev_required
def api_throughput():
    from modules.telecom_diag import medir_throughput_supabase
    return jsonify(medir_throughput_supabase())


@telecom_bp.route('/api/dev/telecom/dns', methods=['GET'])
@_dev_required
def api_dns():
    from modules.telecom_diag import medir_dns
    host = request.args.get('host')
    return jsonify(medir_dns(host=host))


@telecom_bp.route('/api/dev/telecom/tls', methods=['GET'])
@_dev_required
def api_tls():
    from modules.telecom_diag import medir_tls_handshake
    return jsonify(medir_tls_handshake())


@telecom_bp.route('/api/dev/telecom/red', methods=['GET'])
@_dev_required
def api_red():
    from modules.telecom_diag import info_red_local
    return jsonify(info_red_local())


@telecom_bp.route('/api/dev/telecom/sqlite', methods=['GET'])
@_dev_required
def api_sqlite():
    from modules.telecom_diag import velocidad_sqlite
    return jsonify(velocidad_sqlite())


@telecom_bp.route('/api/dev/telecom/full', methods=['GET'])
@_dev_required
def api_full():
    from modules.telecom_diag import diagnostico_completo
    return jsonify(diagnostico_completo())
