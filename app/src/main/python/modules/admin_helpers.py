from db_connection import obtener_conexion
"""Rutas de administración — usuarios, privilegios, licencias (DB)"""
import threading
from flask import Blueprint, request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    crear_usuario, listar_usuarios, desactivar_usuario, resetear_password,
    crear_licencia, listar_licencias, verificar_licencia_activa,
    desactivar_licencia, agregar_log
)
from sync.supabase_sync import sincronizar_usuario_nuevo
import sync.supabase_sync as _sb

admin_bp = Blueprint('admin', __name__)
# ── Privilegios ──────────────────────────────────────────────
_MODULOS_DISPONIBLES = {
    "catalogo": "Gestión de catálogo de productos",
    "productos": "CRUD de productos (crear, editar, eliminar)",
    "categorias": "Gestión de categorías",
    "dashboard": "Panel de estadísticas y KPIs",
    "ventas": "Registro y consulta de ventas",
    "orden": "Gestión de órdenes y pedidos",
    "inventario": "Control de inventario y stock",
    "registros": "Historial y registros del sistema",
    "tienda": "Tienda online y pedidos web",
    "herramientas": "Herramientas del sistema",
    "configuracion": "Configuración general",
    "usuarios": "Gestión de usuarios",
    "licencias": "Gestión de licencias",
    "debug": "Panel de depuración (dev)",
    "privilegios": "Gestión de privilegios por rol",
    "blindajes": "Panel de blindajes de seguridad",
    "ia_edge": "IA Edge Analytics",
    "lealtad": "Programa de Lealtad y puntos",
    "asistente_ia": "Asistente IA conversacional",
    "caja": "Caja y cobros",
    "descuentos": "Gestión de descuentos y ofertas",
    "supabase": "Configuración de Supabase (nube)",
    "seguridad": "Panel de seguridad",
    "biometria": "Autenticación biométrica (huella/rostro)",
    "exportar": "Exportar datos (CSV, Excel)",
    "copias": "Copias de seguridad",
}

_PRIVILEGIOS_DEFAULT = {
    "desarrollador": {m: True for m in _MODULOS_DISPONIBLES},
    "administrador": {m: True for m in _MODULOS_DISPONIBLES
                      if m not in ("debug", "privilegios")},
    "supervisor": {
        "catalogo": True, "productos": True, "categorias": True,
        "dashboard": True, "ventas": True, "orden": True,
        "inventario": True, "registros": True, "tienda": True,
        "ia_edge": True, "lealtad": True, "asistente_ia": True,
        "caja": True, "biometria": True,
    },
    "vendedor": {
        "catalogo": True, "ventas": True, "orden": True,
        "dashboard": True, "ia_edge": True, "lealtad": True,
        "asistente_ia": True, "caja": True, "biometria": True,
    },
    "cajero": {
        "catalogo": True, "ventas": True, "caja": True,
        "dashboard": True, "biometria": True,
    },
}

def _obtener_privilegios_rol(rol):
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        rol_seguro = "".join(c for c in rol if c.isalnum() or c == "_")
        row = conn.execute("SELECT valor FROM app_state WHERE clave=?", (f"privilegios_{rol_seguro}",)).fetchone()
        if row:
            import json as _j
            v = row[0]
            p = _j.loads(v) if isinstance(v, str) else v
            if isinstance(p, dict):
                return p
    except Exception:
        pass
    finally:
        conn.close()
    return None

def _guardar_privilegios_rol(rol, priv):
    from database import obtener_conexion
    import json as _j
    conn = obtener_conexion()
    try:
        conn.execute("INSERT OR REPLACE INTO app_state(clave,valor,actualizado) VALUES(?,?,datetime('now','localtime'))",
                     (f"privilegios_{rol}", _j.dumps(priv, ensure_ascii=False)))
        conn.commit()
        agregar_log(f"Privilegios de '{rol}' actualizados", "info")
        return True
    except Exception as e:
        agregar_log(f"Error privilegios: {e}", "error")
        return False
    finally: conn.close()

