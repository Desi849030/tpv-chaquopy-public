from flask import request, jsonify, session
from functools import wraps
from datetime import datetime
import uuid

from database import obtener_conexion, agregar_log, _hash_password, verificar_password
from auth_decorator import login_required
from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import _guardar_imagen_base64


@login_required
@tienda_bp.route('/api/clientes/registrar', methods=['POST'])
def api_registrar_cliente():
    datos    = request.get_json(force=True, silent=True) or {}
    nombre   = datos.get('nombre', '').strip()
    email    = datos.get('email', '').strip().lower()
    password = datos.get('password', '')
    telefono = datos.get('telefono', '').strip()
    imagen   = datos.get('imagen', '') or datos.get('foto', '')

    if not nombre or not email or not password:
        return jsonify({'error': 'nombre, email y password son obligatorios'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Contraseña mínimo 4 caracteres'}), 400
    if '@' not in email:
        return jsonify({'error': 'Email inválido'}), 400

    hash_pw, salt = _hash_password(password)
    cliente_id = f'cli-{uuid.uuid4().hex[:8]}'
    username = email

    if imagen and imagen.startswith('data:'):
        imagen = _guardar_imagen_base64(imagen, cliente_id)

    conn = obtener_conexion()
    try:
        conn.execute("""
            INSERT INTO clientes_tienda
                (cliente_id, username, nombre, email, telefono, imagen, password_hash, password_salt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, username, nombre, email, telefono, imagen, hash_pw, salt))
        conn.commit()
        agregar_log(f'Cliente registrado: {email}', 'info')
        return jsonify({'ok': True, 'cliente_id': cliente_id, 'mensaje': f'Bienvenido/a {nombre}'})
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Ese email ya está registrado'}), 409
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@login_required
@tienda_bp.route('/api/clientes/login', methods=['POST'])
def api_login_cliente():
    datos    = request.get_json(force=True, silent=True) or {}
    email    = datos.get('email', datos.get('username', '')).strip().lower()
    password = datos.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Faltan credenciales'}), 400

    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT cliente_id, nombre, email, telefono, imagen,
                   password_hash, password_salt, activo
            FROM clientes_tienda WHERE email = ? AND activo = 1
        """, (email,))
        c = cursor.fetchone()
        if not c:
            return jsonify({'error': 'Email no encontrado'}), 401
        if verificar_password(password, c['password_hash'], c['password_salt']):
            conn.execute("UPDATE clientes_tienda SET ultimo_acceso = ? WHERE cliente_id = ?",
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), c['cliente_id']))
            conn.commit()
            session.permanent = True
            session['usuario'] = {
                'usuario_id': c['cliente_id'],
                'rol': 'cliente',
                'nombre': c['nombre'],
                'username': c['email']
            }
            return jsonify({'ok': True, 'cliente': {
                'id': c['cliente_id'], 'nombre': c['nombre'],
                'email': c['email'], 'telefono': c['telefono'],
                'imagen': c['imagen']
            }})
        return jsonify({'error': 'Contraseña incorrecta'}), 401
    finally:
        conn.close()


@login_required
@tienda_bp.route('/api/clientes/<cliente_id>', methods=['GET'])
def api_perfil_cliente(cliente_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT cliente_id AS id, nombre, email, telefono, imagen, creado
            FROM clientes_tienda WHERE cliente_id = ? AND activo = 1
        """, (cliente_id,))
        c = cursor.fetchone()
        if not c:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        return jsonify({'cliente': dict(c)})
    finally:
        conn.close()
