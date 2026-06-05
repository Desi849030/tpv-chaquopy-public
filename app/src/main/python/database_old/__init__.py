"""
Database module - SQLite operations
"""
import sqlite3
import os
import hashlib
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'tpv.db')
DB_PATH = DB_FILE

def obtener_conexion():
    """Obtener conexión a la base de datos"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    """Crear tablas necesarias"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT,
            rol TEXT DEFAULT 'usuario',
            activo INTEGER DEFAULT 1,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave TEXT UNIQUE NOT NULL,
            tipo TEXT,
            expira TEXT,
            activa INTEGER DEFAULT 1,
            creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            clave TEXT PRIMARY KEY,
            valor TEXT,
            actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel TEXT,
            mensaje TEXT,
            modulo TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tablas creadas correctamente")

def login_usuario(username, password):
    """Verificar credenciales de usuario con scrypt"""
    import hashlib
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
        (username,)
    )
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        cols = [desc[0] for desc in cursor.description]
        usuario = dict(zip(cols, usuario))
        stored = usuario.get('password', '')
        # Verificar con scrypt (formato: salt:hash)
        if ':' in stored:
            salt, hash_hex = stored.split(':', 1)
            h = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=32)
            if h.hex() == hash_hex:
                return usuario
        else:
            # Fallback para contraseñas en texto plano (no recomendado)
            if password == stored:
                return usuario
    return None

def obtener_info_db():
    """Obtener información de la base de datos"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {
        "db_file": DB_FILE,
        "tablas": tablas,
        "estado": "conectado"
    }

def agregar_log(nivel, mensaje, modulo="general"):
    """Agregar registro de log"""
    try:
        conn = obtener_conexion()
        conn.execute(
            "INSERT INTO logs (nivel, mensaje, modulo) VALUES (?, ?, ?)",
            (nivel, mensaje, modulo)
        )
        conn.commit()
        conn.close()
    except:
        pass

def _hash_password(password):
    """Hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_password(password, hash_password):
    """Verificar contraseña"""
    return _hash_password(password) == hash_password

def crear_usuario(username, password, nombre, rol='usuario', activo=True):
    """Crear un nuevo usuario con contraseña hasheada con scrypt"""
    import hashlib
    import os
    
    # Generar hash scrypt
    salt = os.urandom(16).hex()
    h = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=32)
    password_hash = f"{salt}:{h.hex()}"
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (username, password, nombre, rol, activo)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, nombre, rol, 1 if activo else 0))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creando usuario: {e}")
        return False
    finally:
        conn.close()


def cambiar_password(username, new_password):
    """Cambiar contraseña de un usuario"""
    import hashlib
    import os
    
    salt = os.urandom(16).hex()
    h = hashlib.scrypt(new_password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=32)
    password_hash = f"{salt}:{h.hex()}"
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET password = ? WHERE username = ?", (password_hash, username))
    conn.commit()
    conn.close()
    return True

def crear_cliente(nombre, email=None, telefono=None, direccion=None):
    """Crear un nuevo cliente"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (nombre, email, telefono, direccion)
            VALUES (?, ?, ?, ?)
        """, (nombre, email, telefono, direccion))
        conn.commit()
        cliente_id = cursor.lastrowid
        return cliente_id
    except Exception as e:
        print(f"Error creando cliente: {e}")
        return None
    finally:
        conn.close()


def obtener_cliente(cliente_id):
    """Obtener un cliente por su ID"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()
    conn.close()
    if cliente:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, cliente))
    return None


def buscar_clientes(termino):
    """Buscar clientes por nombre, email o teléfono"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM clientes 
        WHERE nombre LIKE ? OR email LIKE ? OR telefono LIKE ?
        ORDER BY nombre
    """, (f'%{termino}%', f'%{termino}%', f'%{termino}%'))
    cols = [desc[0] for desc in cursor.description]
    clientes = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return clientes


def actualizar_cliente(cliente_id, **kwargs):
    """Actualizar datos de un cliente"""
    campos = []
    valores = []
    for campo, valor in kwargs.items():
        campos.append(f"{campo} = ?")
        valores.append(valor)
    valores.append(cliente_id)
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE clientes SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()
    return True


def eliminar_cliente(cliente_id):
    """Eliminar un cliente"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    return True


def listar_clientes(limite=100):
    """Listar todos los clientes"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nombre LIMIT ?", (limite,))
    cols = [desc[0] for desc in cursor.description]
    clientes = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return clientes
