"""
╔══════════════════════════════════════════════════════════════╗
║   tienda_routes.py  —  TPV ULTRA SMART  v5.0                ║
║   Clientes con imagen, QR, stock por color en catálogo      ║
╚══════════════════════════════════════════════════════════════╝
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
import uuid, base64, os

from database import (
    obtener_conexion, agregar_log,
    _hash_password, verificar_password
)

tienda_bp = Blueprint('tienda', __name__)

# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
def _usuario_sistema():
    return session.get('usuario', {})

def _rol_sistema():
    return _usuario_sistema().get('rol', '')

def requiere_staff(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if _rol_sistema() not in ('vendedor','supervisor','administrador','desarrollador'):
            return jsonify({'error': 'Acceso restringido al personal'}), 403
        return f(*args, **kwargs)
    return wrapper

def requiere_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if _rol_sistema() not in ('administrador','desarrollador'):
            return jsonify({'error': 'Solo Admin/Dev'}), 403
        return f(*args, **kwargs)
    return wrapper

def _guardar_imagen_base64(imagen_b64, nombre_archivo):
    """Guarda imagen base64 en disco, devuelve ruta relativa o None."""
    if not imagen_b64 or not imagen_b64.startswith('data:'):
        return imagen_b64  # ya es URL o vacío
    try:
        header, data = imagen_b64.split(',', 1)
        ext  = 'jpg'
        if 'png' in header:  ext = 'png'
        elif 'gif' in header: ext = 'gif'
        elif 'webp' in header: ext = 'webp'
        carpeta = os.path.join('static', 'uploads')
        os.makedirs(carpeta, exist_ok=True)
        fname = f"{nombre_archivo}.{ext}"
        ruta  = os.path.join(carpeta, fname)
        with open(ruta, 'wb') as f:
            f.write(base64.b64decode(data))
        return f"/static/uploads/{fname}"
    except Exception as e:
        print(f"⚠️ Error guardando imagen: {e}")
        return imagen_b64  # devolver original si falla

# ══════════════════════════════════════════════════════════════
#  INIT TABLAS
# ══════════════════════════════════════════════════════════════
def crear_tablas_tienda():
    conn   = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes_tienda (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id    TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            telefono      TEXT    DEFAULT '',
            imagen        TEXT    DEFAULT '',
            password_hash TEXT    NOT NULL,
            password_salt TEXT    NOT NULL,
            activo        INTEGER DEFAULT 1,
            ultimo_acceso TEXT    DEFAULT NULL,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    # Migraciones para BD existentes con columnas faltantes
    for col, definicion in [
        ('imagen',   "TEXT DEFAULT ''"),
        ('username', "TEXT DEFAULT ''"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE clientes_tienda ADD COLUMN {col} {definicion}")
            conn.commit()
            print(f"✅ Migración: columna '{col}' añadida a clientes_tienda")
        except Exception:
            pass  # Ya existe, todo bien

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiendas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda_id     TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            descripcion   TEXT    DEFAULT '',
            emoji         TEXT    DEFAULT '🏪',
            admin_id      TEXT    NOT NULL,
            imagen        TEXT    DEFAULT '',
            activo        INTEGER DEFAULT 1,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )""")
    # Migración: añadir imagen si no existe en BD existente
    try:
        cursor.execute("ALTER TABLE tiendas ADD COLUMN imagen TEXT DEFAULT ''")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_tienda (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id       TEXT    NOT NULL UNIQUE,
            cliente_id      TEXT    NOT NULL,
            cliente_nombre  TEXT    NOT NULL,
            tienda_id       TEXT    NOT NULL,
            tienda_nombre   TEXT    NOT NULL,
            total           REAL    NOT NULL DEFAULT 0,
            estado          TEXT    NOT NULL DEFAULT 'pendiente'
                            CHECK(estado IN ('pendiente','aceptado','rechazado','entregado')),
            nota            TEXT    DEFAULT '',
            atendido_por    TEXT    DEFAULT NULL,
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            actualizado     TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_pedido (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id     TEXT    NOT NULL,
            producto_id   TEXT    NOT NULL,
            nombre        TEXT    NOT NULL,
            cantidad      REAL    NOT NULL DEFAULT 1,
            precio        REAL    NOT NULL DEFAULT 0,
            subtotal      REAL    NOT NULL DEFAULT 0,
            FOREIGN KEY (pedido_id) REFERENCES pedidos_tienda(pedido_id)
        )""")

    conn.commit()
    conn.close()
    print("✅ Tablas tienda listas")

# ══════════════════════════════════════════════════════════════
#  CLIENTES — registro libre con email + imagen opcional
# ══════════════════════════════════════════════════════════════
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
@tienda_bp.route('/api/productos', methods=['GET'])
def api_listar_productos():
    """
    Lista productos del catálogo con stock y color de existencia:
      verde  (stock >= 24)
      amarillo (stock >= 15)
      rojo   (stock <= 1)
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.producto_id AS id, p.nombre, p.precio, p.costo,
                   p.categoria, p.imagen, p.en_oferta AS enOferta,
                   p.unidad_medida AS unidadMedida,
                   COALESCE(ig.stock_actual, 0) AS stock
            FROM productos p
            LEFT JOIN inventario_general ig ON ig.producto_id = p.producto_id
            WHERE p.activo = 1
            ORDER BY p.categoria, p.nombre ASC
        """)
        productos = []
        for row in cursor.fetchall():
            p     = dict(row)
            stock = p.get('stock', 0) or 0
            if stock >= 24:
                p['stockColor'] = 'verde'
            elif stock >= 15:
                p['stockColor'] = 'amarillo'
            elif stock <= 1:
                p['stockColor'] = 'rojo'
            else:
                p['stockColor'] = 'naranja'
            productos.append(p)
        return jsonify({'productos': productos, 'total': len(productos)})
    finally:
        conn.close()


@tienda_bp.route('/api/productos/<producto_id>', methods=['GET'])
def api_producto_detalle(producto_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.producto_id AS id, p.nombre, p.precio, p.costo,
                   p.categoria, p.imagen, p.en_oferta AS enOferta,
                   p.unidad_medida AS unidadMedida,
                   COALESCE(ig.stock_actual, 0) AS stock
            FROM productos p
            LEFT JOIN inventario_general ig ON ig.producto_id = p.producto_id
            WHERE p.producto_id = ? AND p.activo = 1
        """, (producto_id,))
        p = cursor.fetchone()
        if not p:
            return jsonify({'error': 'Producto no encontrado'}), 404
        return jsonify({'producto': dict(p)})
    finally:
        conn.close()


@tienda_bp.route('/api/productos/<producto_id>/imagen', methods=['POST'])
@requiere_staff
def api_subir_imagen_producto(producto_id):
    """
    Sube o actualiza la imagen de un producto (base64).
    Admite caracteres especiales en nombre de archivo.
    Body JSON: { "imagen": "data:image/jpeg;base64,..." }
    """
    datos  = request.get_json(force=True, silent=True) or {}
    imagen = datos.get('imagen', '')
    if not imagen:
        return jsonify({'error': 'Sin imagen'}), 400

    ruta = _guardar_imagen_base64(imagen, f"prod_{producto_id}")
    conn = obtener_conexion()
    try:
        conn.execute("UPDATE productos SET imagen = ? WHERE producto_id = ?", (ruta, producto_id))
        conn.commit()
        return jsonify({'ok': True, 'imagen': ruta})
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  QR — generación para productos del catálogo (máx 40)
# ══════════════════════════════════════════════════════════════
@tienda_bp.route('/api/productos/qr', methods=['POST'])
@requiere_staff
def api_generar_qr_productos():
    """
    Genera QR para hasta 40 productos.
    Body JSON: { "producto_ids": ["id1","id2",...], "base_url": "http://..." }
    El QR apunta a la URL del producto en la tienda.
    Devuelve lista con { id, nombre, qr_svg } usando qrcode puro Python.
    """
    datos       = request.get_json(force=True, silent=True) or {}
    ids         = datos.get('producto_ids', [])[:40]   # máx 40
    base_url    = datos.get('base_url', 'http://localhost:5000/tienda/producto')

    try:
        import qrcode
        from qrcode.image.svg import SvgImage
        import io
    except ImportError:
        # Fallback: generar URL de Google Charts API (sin dependencias)
        conn   = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT producto_id AS id, nombre FROM productos WHERE producto_id IN ({','.join('?'*len(ids))}) AND activo=1",
            ids
        )
        productos = [dict(r) for r in cursor.fetchall()]
        conn.close()
        resultado = []
        for p in productos:
            # Encoding correcto para ñ y caracteres especiales
            import urllib.parse
            url     = f"{base_url}/{p['id']}"
            url_enc = urllib.parse.quote(url, safe=':/.')
            qr_url  = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_enc}&ecc=M"
            resultado.append({'id': p['id'], 'nombre': p['nombre'], 'qr_url': qr_url})
        return jsonify({'ok': True, 'qrs': resultado, 'total': len(resultado), 'metodo': 'api_externa'})

    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT producto_id AS id, nombre FROM productos WHERE producto_id IN ({','.join('?'*len(ids))}) AND activo=1",
        ids
    )
    productos = [dict(r) for r in cursor.fetchall()]
    conn.close()

    resultado = []
    for p in productos:
        url = f"{base_url}/{p['id']}"
        # qrcode maneja Unicode/ñ correctamente con encoding='utf-8'
        qr  = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2
        )
        qr.add_data(url, optimize=0)
        qr.make(fit=True)
        img    = qr.make_image(image_factory=SvgImage)
        buffer = io.BytesIO()
        img.save(buffer)
        svg_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        resultado.append({
            'id':     p['id'],
            'nombre': p['nombre'],
            'url':    url,
            'qr_svg_b64': svg_b64
        })

    return jsonify({'ok': True, 'qrs': resultado, 'total': len(resultado), 'metodo': 'local'})


# ══════════════════════════════════════════════════════════════
#  TIENDAS
# ══════════════════════════════════════════════════════════════
@tienda_bp.route('/api/tiendas', methods=['GET'])
def api_listar_tiendas():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT tienda_id AS id, tienda_id, nombre, descripcion, emoji, admin_id, imagen, activo, creado
            FROM tiendas WHERE activo = 1 ORDER BY nombre ASC
        """)
        return jsonify({'tiendas': [dict(f) for f in cursor.fetchall()]})
    finally:
        conn.close()


@tienda_bp.route('/api/tiendas', methods=['POST'])
@requiere_admin
def api_crear_tienda():
    datos      = request.get_json(force=True, silent=True) or {}
    nombre     = datos.get('nombre', '').strip()
    descripcion = datos.get('descripcion', '')
    emoji      = datos.get('emoji', '🏪')
    tienda_id  = datos.get('id') or f'tnd-{uuid.uuid4().hex[:8]}'
    admin_id   = _usuario_sistema().get('usuario_id', 'sistema')
    if not nombre:
        return jsonify({'error': 'Nombre obligatorio'}), 400
    conn = obtener_conexion()
    try:
        conn.execute("INSERT INTO tiendas (tienda_id, nombre, descripcion, emoji, admin_id) VALUES (?, ?, ?, ?, ?)",
                     (tienda_id, nombre, descripcion, emoji, admin_id))
        conn.commit()
        return jsonify({'ok': True, 'tienda_id': tienda_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@tienda_bp.route('/api/tiendas/<tienda_id>', methods=['DELETE'])
@requiere_admin
def api_eliminar_tienda(tienda_id):
    conn = obtener_conexion()
    try:
        conn.execute("UPDATE tiendas SET activo = 0 WHERE tienda_id = ?", (tienda_id,))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@tienda_bp.route('/api/tiendas/<tienda_id>', methods=['PATCH'])
@requiere_admin
def api_actualizar_tienda(tienda_id):
    """Admin actualiza nombre e imagen de su tienda."""
    datos  = request.get_json(force=True, silent=True) or {}
    u      = session.get('usuario', {})

    nombre = datos.get('nombre', '').strip()
    imagen = datos.get('imagen')

    if not nombre:
        return jsonify({'error': 'Nombre requerido'}), 400

    conn = obtener_conexion()
    try:
        if imagen:
            conn.execute(
                "UPDATE tiendas SET nombre = ?, imagen = ? WHERE tienda_id = ?",
                (nombre, imagen, tienda_id)
            )
        else:
            conn.execute(
                "UPDATE tiendas SET nombre = ? WHERE tienda_id = ?",
                (nombre, tienda_id)
            )
        conn.commit()
        return jsonify({'ok': True, 'tienda_id': tienda_id, 'nombre': nombre})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def api_productos_tienda(tienda_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        hoy = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT DISTINCT id.producto_id AS id, id.nombre,
                   id.precio_venta AS precio, p.categoria, p.imagen,
                   p.en_oferta AS enOferta, p.unidad_medida AS unidadMedida,
                   id.cant_asignada - id.cant_vendida AS stock
            FROM inventario_diario id
            JOIN tiendas t ON t.tienda_id = ?
            LEFT JOIN productos p ON p.producto_id = id.producto_id
            WHERE id.fecha = ? AND id.activo = 1
              AND id.cant_asignada - id.cant_vendida > 0
        """, (tienda_id, hoy))
        productos = [dict(f) for f in cursor.fetchall()]
        if not productos:
            cursor.execute("""
                SELECT p.producto_id AS id, p.nombre, p.precio,
                       p.categoria, p.imagen, p.en_oferta AS enOferta,
                       p.unidad_medida AS unidadMedida,
                       COALESCE(ig.stock_actual, 0) AS stock
                FROM productos p
                LEFT JOIN inventario_general ig ON ig.producto_id = p.producto_id
                WHERE p.activo = 1 ORDER BY p.categoria, p.nombre
            """)
            productos = [dict(f) for f in cursor.fetchall()]

        # Añadir color de stock
        for p in productos:
            s = p.get('stock', 0) or 0
            p['stockColor'] = 'verde' if s >= 24 else ('amarillo' if s >= 15 else ('rojo' if s <= 1 else 'naranja'))

        return jsonify({'productos': productos, 'total': len(productos)})
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  PEDIDOS
# ══════════════════════════════════════════════════════════════
@tienda_bp.route('/api/pedidos', methods=['POST'])
def api_crear_pedido():
    datos          = request.get_json(force=True, silent=True) or {}
    pedido_id      = datos.get('id') or f'ped-{uuid.uuid4().hex[:8]}'
    cliente_id     = datos.get('cliente_id', '')
    cliente_nombre = datos.get('cliente_nombre', 'Cliente')
    tienda_id      = datos.get('tienda_id', '')
    tienda_nombre  = datos.get('tienda_nombre', '')
    items          = datos.get('items', [])
    total          = float(datos.get('total', 0))
    nota           = datos.get('nota', '')

    if not cliente_id or not tienda_id or not items:
        return jsonify({'error': 'cliente_id, tienda_id e items son obligatorios'}), 400

    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT OR IGNORE INTO pedidos_tienda
                (pedido_id, cliente_id, cliente_nombre, tienda_id,
                 tienda_nombre, total, estado, nota, fecha, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, 'pendiente', ?, ?, ?)
        """, (pedido_id, cliente_id, cliente_nombre, tienda_id,
              tienda_nombre, total, nota, ahora, ahora))
        for item in items:
            subtotal = float(item.get('precio',0)) * float(item.get('cantidad',1))
            cursor.execute("""
                INSERT INTO items_pedido (pedido_id, producto_id, nombre, cantidad, precio, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pedido_id, item.get('id',''), item.get('nombre',''),
                  float(item.get('cantidad',1)), float(item.get('precio',0)), subtotal))
        conn.commit()
        agregar_log(f'Pedido {pedido_id} de {cliente_nombre}', 'info')
        return jsonify({'ok': True, 'pedido_id': pedido_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@tienda_bp.route('/api/pedidos', methods=['GET'])
def api_listar_pedidos():
    estado     = request.args.get('estado')
    cliente_id = request.args.get('cliente_id')
    tienda_id  = request.args.get('tienda_id')
    desde      = request.args.get('desde')
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        condiciones, params = [], []
        if estado:     condiciones.append('p.estado = ?');     params.append(estado)
        if cliente_id: condiciones.append('p.cliente_id = ?'); params.append(cliente_id)
        if tienda_id:  condiciones.append('p.tienda_id = ?');  params.append(tienda_id)
        if desde:      condiciones.append('p.fecha >= ?');     params.append(desde)
        where = 'WHERE ' + ' AND '.join(condiciones) if condiciones else ''
        cursor.execute(f"""
            SELECT p.pedido_id AS id, p.cliente_id, p.cliente_nombre,
                   p.tienda_id, p.tienda_nombre, p.total, p.estado,
                   p.nota, p.atendido_por, p.fecha, p.actualizado
            FROM pedidos_tienda p {where}
            ORDER BY p.fecha DESC LIMIT 200
        """, params)
        pedidos = []
        for row in cursor.fetchall():
            p = dict(row)
            cursor.execute("""
                SELECT producto_id AS id, nombre, cantidad, precio, subtotal
                FROM items_pedido WHERE pedido_id = ?
            """, (p['id'],))
            p['items'] = [dict(r) for r in cursor.fetchall()]
            pedidos.append(p)
        return jsonify({'pedidos': pedidos, 'total': len(pedidos)})
    finally:
        conn.close()


@tienda_bp.route('/api/pedidos/<pedido_id>', methods=['GET'])
def api_obtener_pedido(pedido_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT pedido_id AS id, cliente_id, cliente_nombre,
                   tienda_id, tienda_nombre, total, estado,
                   nota, atendido_por, fecha, actualizado
            FROM pedidos_tienda WHERE pedido_id = ?
        """, (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido:
            return jsonify({'error': 'No encontrado'}), 404
        p = dict(pedido)
        cursor.execute("SELECT producto_id AS id, nombre, cantidad, precio, subtotal FROM items_pedido WHERE pedido_id = ?", (pedido_id,))
        p['items'] = [dict(r) for r in cursor.fetchall()]
        return jsonify({'pedido': p})
    finally:
        conn.close()


@tienda_bp.route('/api/pedidos/<pedido_id>/estado', methods=['PATCH'])
@requiere_staff
def api_actualizar_estado_pedido(pedido_id):
    datos        = request.get_json(force=True, silent=True) or {}
    nuevo_estado = datos.get('estado', '')
    estados_ok   = ('pendiente','aceptado','rechazado','entregado')
    if nuevo_estado not in estados_ok:
        return jsonify({'error': f'Estado inválido. Usa: {", ".join(estados_ok)}'}), 400
    usuario = _usuario_sistema()
    ahora   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = obtener_conexion()
    try:
        conn.execute("""
            UPDATE pedidos_tienda SET estado = ?, atendido_por = ?, actualizado = ?
            WHERE pedido_id = ?
        """, (nuevo_estado, usuario.get('usuario_id'), ahora, pedido_id))
        conn.commit()
        return jsonify({'ok': True, 'estado': nuevo_estado})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@tienda_bp.route('/api/pedidos/resumen', methods=['GET'])
@requiere_admin
def api_resumen_pedidos():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado, COUNT(*) AS num, SUM(total) AS total_ingresos FROM pedidos_tienda GROUP BY estado")
        por_estado = [dict(f) for f in cursor.fetchall()]
        cursor.execute("""
            SELECT cliente_nombre, COUNT(*) AS num_pedidos, SUM(total) AS total_gastado
            FROM pedidos_tienda GROUP BY cliente_id ORDER BY total_gastado DESC LIMIT 5
        """)
        top_clientes = [dict(f) for f in cursor.fetchall()]
        cursor.execute("""
            SELECT DATE(fecha) AS dia, COUNT(*) AS num_pedidos, SUM(total) AS total
            FROM pedidos_tienda GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 30
        """)
        por_dia = [dict(f) for f in cursor.fetchall()]
        return jsonify({'por_estado': por_estado, 'top_clientes': top_clientes, 'por_dia': por_dia})
    finally:
        conn.close()
