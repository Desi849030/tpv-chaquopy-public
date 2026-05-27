from auth_decorator import login_required
from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import *

@login_required
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


@login_required
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


@login_required
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


@login_required
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
