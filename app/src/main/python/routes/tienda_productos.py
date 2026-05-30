from db_connection import obtener_conexion
from flask import request
from auth_decorator import login_required
from routes.tienda_bp import tienda_bp
from routes.tienda_helpers import *

@login_required
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


@login_required
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


@login_required
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
@login_required
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
