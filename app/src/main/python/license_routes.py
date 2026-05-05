# -*- coding: utf-8 -*-
"""license_routes.py v2.0 - TPV Ultra Smart - Rutas API de licencias server-side"""
from flask import Blueprint, request, jsonify, session

lic_bp = Blueprint('license', __name__, url_prefix='/api/license')

from license_manager import (
    validar_licencia, generar_licencia, activar_licencia,
    desactivar_licencia, listar_licencias, generar_device_id
)


@lic_bp.route('/validate', methods=['GET', 'POST'])
def validate():
    """Verifica el estado de la licencia del dispositivo actual."""
    device_id = request.headers.get('X-Device-ID', '') or request.json.get('device_id', '') if request.is_json else request.args.get('device_id', '')
    
    if not device_id:
        # Generar uno para este dispositivo
        device_id = generar_device_id()
    
    resultado = validar_licencia(device_id)
    resultado['device_id'] = device_id
    return jsonify(resultado)


@lic_bp.route('/activate', methods=['POST'])
def activate():
    """Activa una licencia con una clave proporcionada."""
    data = request.get_json(silent=True) or {}
    licencia_id = data.get('licencia_id', '').strip().upper()
    device_id = data.get('device_id', '') or request.headers.get('X-Device-ID', '')
    
    if not licencia_id:
        return jsonify({'ok': False, 'error': 'Clave de licencia requerida'})
    if not device_id:
        device_id = generar_device_id()
    
    resultado = activar_licencia(licencia_id, device_id)
    if resultado['ok']:
        resultado['device_id'] = device_id
        # Devolver también el estado actualizado
        estado = validar_licencia(device_id)
        resultado['licencia'] = estado
    return jsonify(resultado)


@lic_bp.route('/generate', methods=['POST'])
def generate():
    """Genera una nueva licencia (solo desarrollador)."""
    # Verificar que sea desarrollador
    u = session.get('usuario', {})
    if u.get('rol') != 'desarrollador':
        return jsonify({'error': 'Solo el desarrollador puede generar licencias'}), 403
    
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id', generar_device_id())
    tipo = data.get('tipo', 'trial')
    valor = data.get('valor', 7)
    unidad = data.get('unidad', 'dias')
    nota = data.get('nota', '')
    
    resultado = generar_licencia(device_id, tipo, valor, unidad, nota)
    return jsonify({'ok': True, 'licencia': resultado})


@lic_bp.route('/deactivate', methods=['POST'])
def deactivate():
    """Desactiva una licencia (solo desarrollador)."""
    u = session.get('usuario', {})
    if u.get('rol') != 'desarrollador':
        return jsonify({'error': 'Solo el desarrollador puede desactivar licencias'}), 403
    
    data = request.get_json(silent=True) or {}
    licencia_id = data.get('licencia_id', '')
    
    if not licencia_id:
        return jsonify({'ok': False, 'error': 'ID de licencia requerido'})
    
    resultado = desactivar_licencia(licencia_id)
    return jsonify(resultado)


@lic_bp.route('/list', methods=['GET'])
def list_all():
    """Lista todas las licencias (solo desarrollador)."""
    u = session.get('usuario', {})
    if u.get('rol') != 'desarrollador':
        return jsonify({'error': 'Solo el desarrollador puede ver licencias'}), 403
    
    licencias = listar_licencias()
    # Ocultar firma HMAC por seguridad
    for l in licencias:
        l.pop('firma_hmac', None)
    return jsonify({'ok': True, 'licencias': licencias, 'total': len(licencias)})


@lic_bp.route('/device-id', methods=['GET'])
def get_device_id():
    """Devuelve el device_id generado para este dispositivo."""
    return jsonify({'device_id': generar_device_id()})


print("[license_routes.py v2.0] Rutas de licencia registradas en /api/license")
