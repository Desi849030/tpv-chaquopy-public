# validacion_routes.py — Endpoints de validacion server-side
from flask import Blueprint, request, jsonify
from decorators import requiere_login, usuario_actual
from tpv_security import (
    calcular_venta, validar_totales, validar_stock,
    calcular_cierre_server, sanitize_data, sanitize_string,
    generar_id, cifrar_valor, descifrar_valor, check_sql_injection
)

val_bp = Blueprint('validacion', __name__)


@val_bp.route('/api/ventas/calcular', methods=['POST'])
@requiere_login
def api_calcular_venta():
    datos = sanitize_data(request.get_json(force=True, silent=True) or {})
    items = datos.get('items', [])
    if not items:
        return jsonify({'error': 'No hay items'}), 400
    desc = float(datos.get('descuento_pct', 0))
    imp = float(datos.get('impuesto_pct', 0))
    resultado = calcular_venta(items, desc, imp)
    return jsonify({'ok': True, **resultado})


@val_bp.route('/api/ventas/validar-totales', methods=['POST'])
@requiere_login
def api_validar_totales():
    datos = sanitize_data(request.get_json(force=True, silent=True) or {})
    resultado = validar_totales(datos)
    if not resultado.get('valido', False):
        return jsonify({'ok': False, **resultado}), 400
    return jsonify({'ok': True, **resultado})


@val_bp.route('/api/ventas/validar-stock', methods=['POST'])
@requiere_login
def api_validar_stock():
    datos = request.get_json(force=True, silent=True) or {}
    items = datos.get('items', [])
    if not items:
        return jsonify({'error': 'No hay items'}), 400
    u = usuario_actual()
    uid = u.get('usuario_id') if u else None
    resultado = validar_stock(items, uid)
    if not resultado.get('valido', False):
        return jsonify({'ok': False, **resultado}), 400
    return jsonify({'ok': True, 'mensaje': 'Stock disponible'})


@val_bp.route('/api/ventas/cierre-calcular', methods=['POST'])
@requiere_login
def api_cierre_calcular():
    datos = request.get_json(force=True, silent=True) or {}
    fecha = datos.get('fecha')
    if not fecha:
        from datetime import datetime
        fecha = datetime.now().strftime('%Y-%m-%d')
    u = usuario_actual()
    vid = u.get('vendedor_id') if u and u.get('rol') == 'vendedor' else datos.get('vendedor_id')
    resultado = calcular_cierre_server(fecha, vid)
    if 'error' in resultado:
        return jsonify({'ok': False, 'error': resultado['error']}), 500
    return jsonify({'ok': True, **resultado})


@val_bp.route('/api/ventas/generar-id', methods=['POST'])
@requiere_login
def api_generar_id():
    datos = request.get_json(silent=True) or {}
    prefijo = datos.get('prefijo', 'id')
    return jsonify({'ok': True, 'id': generar_id(prefijo)})


@val_bp.route('/api/util/sanitize', methods=['POST'])
def api_sanitize():
    datos = request.get_json(silent=True) or {}
    texto = datos.get('texto', '')
    if not texto:
        return jsonify({'error': 'Se requiere texto'}), 400
    resultado = sanitize_string(str(texto))
    return jsonify({'sanitized': resultado, 'original': texto})


@val_bp.route('/api/util/sqli-check', methods=['POST'])
def api_sqli_check():
    datos = request.get_json(silent=True) or {}
    texto = datos.get('texto', '')
    if not texto:
        return jsonify({'error': 'Se requiere texto'}), 400
    resultado = check_sql_injection(str(texto))
    return jsonify({'peligroso': resultado, 'texto': texto})


@val_bp.route('/api/util/cifrar', methods=['POST'])
@requiere_login
def api_cifrar():
    datos = request.get_json(silent=True) or {}
    valor = datos.get('valor', '')
    if not valor:
        return jsonify({'error': 'Se requiere valor'}), 400
    resultado = cifrar_valor(str(valor))
    return jsonify({'ok': True, 'cifrado': resultado})


@val_bp.route('/api/util/descifrar', methods=['POST'])
@requiere_login
def api_descifrar():
    datos = request.get_json(silent=True) or {}
    valor = datos.get('valor', '')
    if not valor:
        return jsonify({'error': 'Se requiere valor'}), 400
    resultado = descifrar_valor(str(valor))
    if resultado is None:
        return jsonify({'error': 'No se pudo descifrar'}), 400
    return jsonify({'ok': True, 'descifrado': resultado})
