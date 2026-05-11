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
