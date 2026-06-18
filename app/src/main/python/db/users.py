"""db_users.py - Usuarios, autenticacion, permisos (DAO)"""
from __future__ import annotations
import sqlite3, json, uuid, hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from db_connection import obtener_conexion, _hash_password, verificar_password, agregar_log


def _get_default_password():
    return "Desarrollador2025"

def _crear_desarrollador_default(cursor, conn):
    """Crea/asegura los usuarios demo del sistema con IDs FIJOS que coinciden
    con los del login de app.py (dev-001, usr-001..004). Así todos los roles
    existen en la tabla 'usuarios' y tienen acceso real (inventario general,
    privilegios, etc.) — antes solo existía el desarrollador."""
    _PW = "123456"
    # (usuario_id, username, nombre, rol)
    DEMO = [
        ("dev-001", "desarrollador", "Desarrollador Principal", "desarrollador"),
        ("usr-001", "admin",         "Administrador",           "administrador"),
        ("usr-002", "supervisor1",   "María Supervisora",       "supervisor"),
        ("usr-003", "vendedor1",     "Juan Vendedor",           "vendedor"),
        ("usr-004", "cajero1",       "Ana Cajera",              "cajero"),
    ]
    for uid, username, nombre, rol in DEMO:
        hash_pw, salt = _hash_password(_PW)
        cursor.execute("SELECT usuario_id FROM usuarios WHERE username=? OR usuario_id=?",
                       (username, uid))
        row = cursor.fetchone()
        if row:
            # Actualizar password e id para mantener consistencia con el login
            cursor.execute(
                "UPDATE usuarios SET password_hash=?, password_salt=?, rol=?, nombre=? "
                "WHERE username=?",
                (hash_pw, salt, rol, nombre, username))
        else:
            cursor.execute("""
                INSERT INTO usuarios
                    (usuario_id, username, nombre, rol, password_hash, password_salt, creado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (uid, username, nombre, rol, hash_pw, salt, "sistema"))
    conn.commit()
    print("✅ Usuarios demo asegurados (dev, admin, supervisor, vendedor, cajero) — pass: %s" % _PW)

# ══════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════

def login_usuario(username, password):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        # ── Protección contra fuerza bruta ──────────────────
        from datetime import timedelta
        hace10 = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            fallos = cursor.execute(
                "SELECT COUNT(*) FROM login_intentos WHERE username=? AND exito=0 AND timestamp>?",
                (username, hace10)
            ).fetchone()[0]
            if fallos >= 5:
                return {"error": "bloqueado", "mensaje": "Cuenta bloqueada 10 min por intentos fallidos"}
        except Exception:
            pass  # tabla login_intentos no existe aún

        cursor.execute("""
            SELECT usuario_id, username, nombre, rol,
                   password_hash, password_salt, activo
            FROM usuarios WHERE username = ? AND activo = 1
        """, (username,))
        u = cursor.fetchone()

        def _registrar(exito):
            try:
                cursor.execute(
                    "INSERT INTO login_intentos(username, exito) VALUES(?,?)",
                    (username, 1 if exito else 0)
                )
                conn.commit()
            except Exception:  # noqa: broad-except - graceful degradation
                pass
        if not u:
            _registrar(False)
            agregar_log(f"Login fallido: '{username}' no existe", "warning")
            return None
        if verificar_password(password, u["password_hash"], u["password_salt"]):
            _registrar(True)
            conn.execute("UPDATE usuarios SET ultimo_acceso = ? WHERE username = ?",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            conn.commit()
            agregar_log(f"Login: {username} ({u['rol']})", "info")
            return {"usuario_id": u["usuario_id"], "username": u["username"],
                    "nombre": u["nombre"], "rol": u["rol"]}
        _registrar(False)
        agregar_log(f"Login fallido: contraseña incorrecta '{username}'", "warning")
        return None
    finally:
        conn.close()



def crear_usuario(datos, creado_por_rol=None, creado_por_id=None):
    # Desarrollador sin límites, puede crear cualquier rol excepto otro desarrollador
    roles_permitidos = {
        "desarrollador": ["administrador", "supervisor", "vendedor"],
        "administrador": ["supervisor", "vendedor"],
        "supervisor":    [],
        "vendedor":      []
    }
    rol_nuevo = datos.get("rol", "")
    if rol_nuevo not in roles_permitidos.get(creado_por_rol, []):
        return {"ok": False, "mensaje": f"'{creado_por_rol}' no puede crear rol '{rol_nuevo}'"}

    username = datos.get("username", "").strip()
    nombre   = datos.get("nombre", "").strip()
    password = datos.get("password", "")

    if not username or not nombre or not password:
        return {"ok": False, "mensaje": "Faltan campos: username, nombre, password"}
    if len(password) < 4:
        return {"ok": False, "mensaje": "Contraseña mínimo 4 caracteres"}

    hash_pw, salt = _hash_password(password)
    uid = f"user-{uuid.uuid4().hex[:8]}"
    conn = obtener_conexion()
    try:
        conn.execute("""
            INSERT INTO usuarios
                (usuario_id, username, nombre, rol, password_hash, password_salt, creado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, username, nombre, rol_nuevo, hash_pw, salt, creado_por_id))
        conn.commit()
        agregar_log(f"Usuario creado: {username} ({rol_nuevo}) por {creado_por_id}", "info")
        return {"ok": True, "mensaje": f"Usuario '{username}' creado", "usuario_id": uid}
    except sqlite3.IntegrityError:
        return {"ok": False, "mensaje": f"El username '{username}' ya existe"}
    except sqlite3.Error as e:
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def cambiar_password(usuario_id, password_actual, password_nueva):
    if len(password_nueva) < 4:
        return {"ok": False, "mensaje": "Mínimo 4 caracteres"}
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash, password_salt FROM usuarios WHERE usuario_id = ? AND activo = 1", (usuario_id,))
        u = cursor.fetchone()
        if not u:
            return {"ok": False, "mensaje": "Usuario no encontrado"}
        if not verificar_password(password_actual, u["password_hash"], u["password_salt"]):
            return {"ok": False, "mensaje": "Contraseña actual incorrecta"}
        nh, ns = _hash_password(password_nueva)
        conn.execute("UPDATE usuarios SET password_hash=?, password_salt=? WHERE usuario_id=?", (nh, ns, usuario_id))
        conn.commit()
        return {"ok": True, "mensaje": "Contraseña actualizada"}
    finally:
        conn.close()



def resetear_password(usuario_id, password_nueva, admin_id):
    if len(password_nueva) < 4:
        return {"ok": False, "mensaje": "Mínimo 4 caracteres"}
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        admin = cursor.fetchone()
        if not admin or admin["rol"] not in ("desarrollador", "administrador"):
            return {"ok": False, "mensaje": "Sin permisos"}
        nh, ns = _hash_password(password_nueva)
        cursor.execute("UPDATE usuarios SET password_hash=?, password_salt=? WHERE usuario_id=?", (nh, ns, usuario_id))
        conn.commit()
        return {"ok": True, "mensaje": "Contraseña reseteada"}
    finally:
        conn.close()



def listar_usuarios(rol_solicitante, id_solicitante):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        if rol_solicitante == "desarrollador":
            cursor.execute("""
                SELECT usuario_id, username, nombre, rol, activo, ultimo_acceso, creado
                FROM usuarios WHERE rol != 'desarrollador' ORDER BY rol, creado DESC
            """)
        elif rol_solicitante == "administrador":
            cursor.execute("""
                SELECT usuario_id, username, nombre, rol, activo, ultimo_acceso, creado
                FROM usuarios WHERE creado_por = ? AND rol IN ('supervisor','vendedor')
                ORDER BY rol, creado DESC
            """, (id_solicitante,))
        else:
            return []
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



def desactivar_usuario(usuario_id, admin_id):
    conn = obtener_conexion()
    try:
        conn.execute("UPDATE usuarios SET activo = 0 WHERE usuario_id = ?", (usuario_id,))
        conn.commit()
        agregar_log(f"Usuario {usuario_id} desactivado por {admin_id}", "warning")
        return {"ok": True, "mensaje": "Usuario desactivado"}
    except sqlite3.Error as e:
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  LICENCIAS (solo Desarrollador)
# ══════════════════════════════════════════════════════════════
# === LICENCIAS ===



def _get_default_password():
    return "123456"
