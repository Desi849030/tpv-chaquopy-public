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
    "catalogo":"Gestion de catalogo","productos":"CRUD productos",
    "categorias":"Gestion categorias","dashboard":"Panel estadisticas",
    "ventas":"Registro ventas","orden":"Gestion ordenes",
    "inventario":"Control inventario","registros":"Historial",
    "tienda":"Tienda online","herramientas":"Herramientas",
    "configuracion":"Configuracion","usuarios":"Gestion usuarios",
    "licencias":"Gestion licencias","debug":"Panel depuracion",
    "privilegios":"Gestion privilegios","blindajes":"Panel blindajes",
    "ia_edge":"IA Edge Analytics","lealtad":"Programa Lealtad",
    "asistente_ia":"Asistente IA","caja":"Caja y cobros","descuentos":"Descuentos","supabase":"Configuracion Supabase","seguridad":"Seguridad","exportar":"Exportar datos","copias":"Copias de seguridad"
}

_PRIVILEGIOS_DEFAULT = {
    "desarrollador": {m: True for m in _MODULOS_DISPONIBLES},
    "administrador": {m: True for m in _MODULOS_DISPONIBLES if m not in ("debug","privilegios")},
    "supervisor": {"catalogo":True,"productos":True,"categorias":True,"dashboard":True,
                   "ventas":True,"orden":True,"inventario":True,"registros":True,
                   "tienda":True,"ia_edge":True,"lealtad":True,"asistente_ia":True},
    "vendedor": {"catalogo":True,"ventas":True,"orden":True,"dashboard":True,
                 "ia_edge":True,"lealtad":True,"asistente_ia":True}
}

def _obtener_privilegios_rol(rol):
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        # Sanitizar rol para evitar inyección en nombre de clave
    rol_seguro = "".join(c for c in rol if c.isalnum() or c == "_")
    rol_seguro = "".join(c for c in rol if c.isalnum() or c == "_")
    row = conn.execute("SELECT valor FROM app_state WHERE clave=?", (f"privilegios_{rol_seguro}",)).fetchone()
        if row:
            import json as _j
            v = row[0]; p = _j.loads(v) if isinstance(v, str) else v
            if isinstance(p, dict): return p
    except Exception: pass
    finally: conn.close()
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

