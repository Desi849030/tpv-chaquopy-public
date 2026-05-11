from __future__ import annotations

"""db_config_licencias.py - Extracted from db_config.py"""
"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE
from db_users import _crear_desarrollador_default

from db.schema import crear_tablas_schema
from db_connection import obtener_conexion
from db_users import _crear_desarrollador_default

"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE
from db_users import _crear_desarrollador_default

from db.schema import crear_tablas_schema
from db_connection import obtener_conexion
from db_users import _crear_desarrollador_default


__all__ = ['crear_tablas', 'crear_licencia', 'listar_licencias', 'verificar_licencia_activa', 'desactivar_licencia']
def crear_tablas():
    conn = obtener_conexion()
    crear_tablas_schema(conn)
    try: _crear_desarrollador_default(conn)
    except Exception: pass
    conn.close()

def crear_licencia(admin_id, tipo, dias, notas, dev_id, cliente_id="", clave_activacion=""):
    """Crea una licencia para un administrador. Solo el desarrollador puede hacerlo."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        # Verificar que quien crea es desarrollador
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (dev_id,))
        dev = cursor.fetchone()
        if not dev or dev["rol"] != "desarrollador":
            return {"ok": False, "mensaje": "Solo el Desarrollador puede generar licencias"}

        # Verificar que el destinatario existe y es administrador
        cursor.execute("SELECT nombre FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            return {"ok": False, "mensaje": "Administrador no encontrado"}

        from datetime import date, timedelta
        hoy          = date.today()
        fecha_inicio = hoy.isoformat()
        fecha_expira = (hoy + timedelta(days=int(dias))).isoformat()
        lic_id       = f"lic-{uuid.uuid4().hex[:10]}"

        # Asegurar columnas opcionales existen (migración segura)
        try:
            conn.execute("ALTER TABLE licencias ADD COLUMN cliente_id TEXT DEFAULT ''")
            conn.commit()
        except Exception: pass
        try:
            conn.execute("ALTER TABLE licencias ADD COLUMN clave_activacion TEXT DEFAULT ''")
            conn.commit()
        except Exception: pass

        conn.execute("""
            INSERT INTO licencias
                (licencia_id, admin_id, admin_nombre, tipo, dias,
                 fecha_inicio, fecha_expira, notas, creado_por,
                 cliente_id, clave_activacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lic_id, admin_id, admin["nombre"], tipo, int(dias),
              fecha_inicio, fecha_expira, notas or "", dev_id,
              cliente_id or "", clave_activacion or ""))
        conn.commit()
        agregar_log(f"Licencia {tipo} ({dias}d) creada para {admin['nombre']} por dev", "info")
        return {
            "ok": True,
            "licencia_id":      lic_id,
            "admin_nombre":     admin["nombre"],
            "tipo":             tipo,
            "dias":             dias,
            "fecha_inicio":     fecha_inicio,
            "fecha_expira":     fecha_expira,
            "cliente_id":       cliente_id,
            "clave_activacion": clave_activacion
        }
    except sqlite3.Error as e:
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



def listar_licencias(dev_id, admin_id_filtro=None):
    """Lista licencias. El desarrollador ve todas; admin solo las suyas."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ?", (dev_id,))
        u = cursor.fetchone()
        if not u:
            return []
        if u["rol"] == "desarrollador":
            if admin_id_filtro:
                cursor.execute("""
                    SELECT l.*, u.username
                    FROM licencias l
                    LEFT JOIN usuarios u ON l.admin_id = u.usuario_id
                    WHERE l.admin_id = ? ORDER BY l.creado DESC
                """, (admin_id_filtro,))
            else:
                cursor.execute("""
                    SELECT l.*, u.username
                    FROM licencias l
                    LEFT JOIN usuarios u ON l.admin_id = u.usuario_id
                    ORDER BY l.creado DESC
                """)
        else:
            cursor.execute("""
                SELECT l.*, u.username
                FROM licencias l
                LEFT JOIN usuarios u ON l.admin_id = u.usuario_id
                WHERE l.admin_id = ? ORDER BY l.creado DESC
            """, (dev_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()



def verificar_licencia_activa(admin_id):
    """Verifica si un administrador tiene licencia vigente."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT licencia_id, tipo, fecha_expira, dias
            FROM licencias
            WHERE admin_id = ? AND activa = 1 AND fecha_expira >= ?
            ORDER BY fecha_expira DESC LIMIT 1
        """, (admin_id, hoy))
        lic = cursor.fetchone()
        return dict(lic) if lic else None
    finally:
        conn.close()



def desactivar_licencia(licencia_id, dev_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ?", (dev_id,))
        u = cursor.fetchone()
        if not u or u["rol"] != "desarrollador":
            return {"ok": False, "mensaje": "Solo el Desarrollador puede desactivar licencias"}
        conn.execute("UPDATE licencias SET activa = 0 WHERE licencia_id = ?", (licencia_id,))
        conn.commit()
        return {"ok": True, "mensaje": "Licencia desactivada"}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  INVENTARIO GENERAL
# ══════════════════════════════════════════════════════════════
