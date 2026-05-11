from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import *

@tienda_bp.route('/api/clientes/registrar', methods=['POST'])
def api_registrar_cliente():
    """
    Registro libre. El cliente proporciona nombre, email, contraseña.
    Opcionalmente puede subir una foto de perfil (base64).
    Body JSON:
        { "nombre":"...", "email":"...", "password":"...",
          "telefono":"...", "imagen":"data:image/jpeg;base64,..." }
    """
    datos    = request.get_json(force=True, silent=True) or {}
    nombre   = datos.get('nombre', '').strip()
    email    = datos.get('email', '').strip().lower()
    password = datos.get('password', '')
    telefono = datos.get('telefono', '').strip()
    imagen   = datos.get('imagen', '') or datos.get('foto', '')  # 'foto' es alias del frontend

    if not nombre or not email or not password:
        return jsonify({'error': 'nombre, email y password son obligatorios'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Contraseña mínimo 4 caracteres'}), 400
    if '@' not in email:
        return jsonify({'error': 'Email inválido'}), 400

    hash_pw, salt = _hash_password(password)
    cliente_id    = f'cli-{uuid.uuid4().hex[:8]}'

    # Guardar imagen si viene en base64
    if imagen and imagen.startswith('data:'):
        imagen = _guardar_imagen_base64(imagen, cliente_id)

    # username = email (único, sirve como identificador de login)
    username = email

    conn = obtener_conexion()
    try:
        conn.execute("""
            INSERT INTO clientes_tienda
                (cliente_id, username, nombre, email, telefono, imagen, password_hash, password_salt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, username, nombre, email, telefono, imagen, hash_pw, salt))
        conn.commit()
        agregar_log(f'Cliente registrado: {email}', 'info')
        return jsonify({'ok': True, 'cliente_id': cliente_id,
                        'mensaje': f'Bienvenido/a {nombre}'})
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Ese email ya está registrado'}), 409
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


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
            return jsonify({'ok': True, 'cliente': {
                'id': c['cliente_id'], 'nombre': c['nombre'],
                'email': c['email'], 'telefono': c['telefono'],
                'imagen': c['imagen']
            }})
        return jsonify({'error': 'Contraseña incorrecta'}), 401
    finally:
        conn.close()


@tienda_bp.route('/api/clientes/<cliente_id>', methods=['GET'])
def api_perfil_cliente(cliente_id):
    """Perfil público del cliente (para la tienda)."""
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


@tienda_bp.route('/api/clientes/<cliente_id>', methods=['PATCH'])
def api_actualizar_cliente(cliente_id):
    """El cliente actualiza su perfil (nombre, teléfono, imagen)."""
    datos    = request.get_json(force=True, silent=True) or {}
    nombre   = datos.get('nombre', '').strip()
    telefono = datos.get('telefono', '').strip()
    imagen   = datos.get('imagen', '')

    campos = []
    vals   = []
    if nombre:   campos.append('nombre = ?');   vals.append(nombre)
    if telefono: campos.append('telefono = ?'); vals.append(telefono)
    if imagen:
        if imagen.startswith('data:'):
            imagen = _guardar_imagen_base64(imagen, cliente_id)
        campos.append('imagen = ?'); vals.append(imagen)

    if not campos:
        return jsonify({'error': 'Nada que actualizar'}), 400

    vals.append(cliente_id)
    conn = obtener_conexion()
    try:
        conn.execute(f"UPDATE clientes_tienda SET {', '.join(campos)} WHERE cliente_id = ?", vals)
        conn.commit()
        return jsonify({'ok': True, 'mensaje': 'Perfil actualizado'})
    finally:
        conn.close()


@tienda_bp.route('/api/clientes', methods=['GET'])
@requiere_admin
def api_listar_clientes():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT cliente_id AS id, nombre, email, telefono, imagen,
                   activo, ultimo_acceso, creado
            FROM clientes_tienda ORDER BY creado DESC
        """)
        clientes = [dict(f) for f in cursor.fetchall()]
        return jsonify({'clientes': clientes, 'total': len(clientes)})
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  PRODUCTOS — con stock por colores y QR
# ══════════════════════════════════════════════════════════════
