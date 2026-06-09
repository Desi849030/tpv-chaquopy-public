from functools import wraps
from flask import session, jsonify
import functools
import sqlite3
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'databases', 'tpv.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def crear_tablas_tienda():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes_tienda (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id  TEXT    NOT NULL UNIQUE,
            nombre      TEXT    NOT NULL,
            email       TEXT    DEFAULT '',
            telefono    TEXT    DEFAULT '',
            direccion   TEXT    DEFAULT '',
            imagen      TEXT    DEFAULT '',
            username    TEXT    DEFAULT '',
            creado      TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)
    
    # Migraciones para BD existentes con columnas faltantes
    for col, definicion in [
        ('imagen',   "TEXT DEFAULT ''"),
        ('username', "TEXT DEFAULT ''"),
    ]:
        try:
            # Sanitizar nombre de columna
            col_seguro = "".join(c for c in col if c.isalnum() or c == "_")
            if col_seguro != col:
                raise ValueError(f"Nombre de columna no válido: {col}")
            cursor.execute(f"ALTER TABLE clientes_tienda ADD COLUMN {col_seguro} {definicion}")
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
        )
    """)
    
    # Migración: añadir imagen si no existe en BD existente
    try:
        cursor.execute("ALTER TABLE tiendas ADD COLUMN imagen TEXT DEFAULT ''")
    except Exception:  # noqa: broad-except - graceful degradation
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
        )
    """)
    
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
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tablas de tienda creadas/verificadas")

def _guardar_imagen_base64(imagen_b64, cliente_id):
    """Guarda imagen base64 como archivo y retorna la ruta."""
    import base64
    import os
    
    try:
        # Extraer datos base64
        if ',' in imagen_b64:
            imagen_b64 = imagen_b64.split(',')[1]
        
        # Decodificar
        img_data = base64.b64decode(imagen_b64)
        
        # Crear directorio si no existe
        img_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'static', 'uploads', 'clientes')
        os.makedirs(img_dir, exist_ok=True)
        
        # Guardar archivo
        ruta = os.path.join(img_dir, f'{cliente_id}.jpg')
        with open(ruta, 'wb') as f:
            f.write(img_data)
        
        return ruta
    except Exception as e:
        print(f"Error guardando imagen: {e}")
        return ''

def requiere_staff(f):
    """Decorador: requiere rol staff o admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('usuario', {}).get('rol') not in ['admin', 'staff']:
            return jsonify({'error': 'No autorizado'}), 403
        return f(*args, **kwargs)
    return decorated_function

def requiere_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "No autorizado"}), 401
        if session.get("rol") != "admin":
            return jsonify({"error": "Se requiere rol admin"}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorated_function
