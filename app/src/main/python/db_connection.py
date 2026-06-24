"""db_connection.py - Conexion BD, seguridad, logging, auditoria (DAO)"""
from __future__ import annotations
import sqlite3, os, hashlib, secrets, hmac
from datetime import datetime
from typing import Optional, Dict, Any

DB_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), "tpv_datos.db")
DB_PATH = DB_FILE

def _hash_password(password: str, salt: str = None) -> tuple:
    """scrypt KDF (N=16384, r=8, p=1) — superior a SHA-256 para contrasenas."""
    if salt is None:
        salt = secrets.token_hex(16)
    if isinstance(salt, str):
        salt_bytes = bytes.fromhex(salt)
    else:
        salt_bytes = salt
    h = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt_bytes,
        n=16384, r=8, p=1,
    )
    return h.hex(), salt


def verify_password(password, hash_guardado, salt):
    h, _ = _hash_password(password, salt)
    return hmac.compare_digest(h, str(hash_guardado))

# ══════════════════════════════════════════════════════════════
#  CONEXIÓN
# ══════════════════════════════════════════════════════════════

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA encoding='UTF-8'")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -8000")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn

# ══════════════════════════════════════════════════════════════
#  CREAR TABLAS
# ══════════════════════════════════════════════════════════════

def log_event(mensaje, tipo="info", usuario=None):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO logs_sistema (tipo, usuario, mensaje) VALUES (?, ?, ?)",
                     (tipo, usuario, mensaje))
        conn.commit()
    except sqlite3.Error as e:
        import sys
        print("[AUDIT ERROR] agregar_log: %s" % e, file=sys.stderr)
    finally:
        conn.close()


TABLAS_PERMITIDAS = frozenset([
    "app_state", "usuarios", "historial_ventas", "productos",
    "inventario_general", "inventario_diario", "entradas_productos",
    "cierres_caja", "inventarios", "logs_sistema", "licencias",
])

def get_db_info():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        info = {"archivo": DB_FILE, "tablas": {}}
        for t in TABLAS_PERMITIDAS:
            try:
                # Table/column from whitelist, not user input
                cursor.execute(f'SELECT COUNT(*) AS total FROM "{t}"')
                info["tablas"][t] = cursor.fetchone()["total"]
            except Exception:
                info["tablas"][t] = 0
        if os.path.exists(DB_FILE):
            info["tamaño_bytes"] = os.path.getsize(DB_FILE)
            info["tamaño_kb"] = round(info["tamaño_bytes"] / 1024, 2)
        return info
    finally:
        conn.close()


def create_audit_table():
    conn = get_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                accion TEXT,
                tabla TEXT,
                registro_id TEXT,
                valor_anterior TEXT,
                valor_nuevo TEXT,
                fecha TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        conn.commit()
    except Exception as e:
        import sys
        print("[AUDIT ERROR] audit_log: %s" % e, file=sys.stderr)
    finally:
        conn.close()


def audit_log(usuario, accion, tabla, registro_id="", valor_anterior="", valor_nuevo=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_logs (usuario,accion,tabla,registro_id,valor_anterior,valor_nuevo) VALUES (?,?,?,?,?,?)",
            (usuario, accion, tabla, registro_id, str(valor_anterior)[:500], str(valor_nuevo)[:500])
        )
        conn.commit()
    except Exception as e:
        import sys
        print("[AUDIT ERROR] audit_log: %s" % e, file=sys.stderr)
    finally:
        conn.close()


# Backward-compatible aliases
obtener_conexion = get_connection
verificar_password = verify_password
agregar_log = log_event
obtener_info_db = get_db_info
crear_tabla_audit = create_audit_table


# Aliases
obtener_conexion = get_connection
verificar_password = verify_password
agregar_log = log_event
obtener_info_db = get_db_info
crear_tabla_audit = create_audit_table