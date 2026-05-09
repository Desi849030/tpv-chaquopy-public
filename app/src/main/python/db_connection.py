"""db_connection.py - Conexion BD, seguridad, logging, auditoria (DAO)"""
from __future__ import annotations
import sqlite3, os, hashlib, secrets
from datetime import datetime
from typing import Optional, Dict, Any

DB_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), "tpv_datos.db")
DB_PATH = DB_FILE

def _hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    combined = f"{salt}{password}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest(), salt


def verificar_password(password, hash_guardado, salt):
    h, _ = _hash_password(password, salt)
    return h == hash_guardado

# ══════════════════════════════════════════════════════════════
#  CONEXIÓN
# ══════════════════════════════════════════════════════════════

def obtener_conexion():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -8000")
    return conn

# ══════════════════════════════════════════════════════════════
#  CREAR TABLAS
# ══════════════════════════════════════════════════════════════

def agregar_log(mensaje, tipo="info", usuario=None):
    conn = obtener_conexion()
    try:
        conn.execute("INSERT INTO logs_sistema (tipo, usuario, mensaje) VALUES (?, ?, ?)",
                     (tipo, usuario, mensaje))
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()



def obtener_info_db():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        info   = {"archivo": DB_FILE, "tablas": {}}
        tablas = ["app_state","usuarios","historial_ventas","productos",
                  "inventario_general","inventario_diario","entradas_productos",
                  "cierres_caja","inventarios","logs_sistema","licencias"]
        for t in tablas:
            try:
                cursor.execute(f"SELECT COUNT(*) AS total FROM {t}")
                info["tablas"][t] = cursor.fetchone()["total"]
            except Exception:
                info["tablas"][t] = 0
        if os.path.exists(DB_FILE):
            info["tamaño_bytes"] = os.path.getsize(DB_FILE)
            info["tamaño_kb"]    = round(info["tamaño_bytes"] / 1024, 2)
        return info
    finally:
        conn.close()


def crear_tabla_audit():
    conn = obtener_conexion()
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
    except: pass
    finally: conn.close()


def audit_log(usuario, accion, tabla, registro_id="", valor_anterior="", valor_nuevo=""):
    conn = obtener_conexion()
    try:
        conn.execute(
            "INSERT INTO audit_logs (usuario,accion,tabla,registro_id,valor_anterior,valor_nuevo) VALUES (?,?,?,?,?,?)",
            (usuario, accion, tabla, registro_id, str(valor_anterior)[:500], str(valor_nuevo)[:500])
        )
        conn.commit()
    except: pass
    finally: conn.close()

