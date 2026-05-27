from auth_decorator import login_required
from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import *

@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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
