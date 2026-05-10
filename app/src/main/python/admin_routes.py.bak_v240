"""Rutas de administración — usuarios, privilegios, licencias (DB)"""
import threading
from flask import Blueprint, request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    crear_usuario, listar_usuarios, desactivar_usuario, resetear_password,
    crear_licencia, listar_licencias, verificar_licencia_activa,
    desactivar_licencia, agregar_log
)
from supabase_sync import sincronizar_usuario_nuevo
import supabase_sync as _sb

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
        row = conn.execute("SELECT valor FROM app_state WHERE clave=?", (f"privilegios_{rol}",)).fetchone()
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

@admin_bp.route("/api/privilegios/<rol>", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_get_privilegios(rol):
    u = usuario_actual()
    if rol == "desarrollador" and u["rol"] != "desarrollador":
        return jsonify({"error": "Sin permisos"}), 403
    p = _obtener_privilegios_rol(rol)
    if p is None:
        p = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    return jsonify({"ok":True,"rol":rol,"privilegios":p,"modulos":_MODULOS_DISPONIBLES,"default":_PRIVILEGIOS_DEFAULT.get(rol,{})})

@admin_bp.route("/api/privilegios/<rol>", methods=["PUT"])
@requiere_rol("desarrollador","administrador")
def api_set_privilegios(rol):
    u = usuario_actual()
    d = request.get_json(force=True, silent=True) or {}
    n = d.get("privilegios", {})
    if not isinstance(n, dict): return jsonify({"error": "Formato invalido"}), 400
    if rol == "desarrollador" and u["rol"] != "desarrollador": return jsonify({"error": "Sin permisos"}), 403
    if u["rol"] == "administrador":
        for m in ("debug","privilegios","licencias"):
            if n.get(m): n[m] = False
    if rol == "desarrollador": n = {m: True for m in _MODULOS_DISPONIBLES}
    if _guardar_privilegios_rol(rol, n):
        return jsonify({"ok": True, "mensaje": f"Privilegios de '{rol}' actualizados"})
    return jsonify({"error": "No se pudieron guardar"}), 500

@admin_bp.route("/api/privilegios/<rol>/restablecer", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_reset_privilegios(rol):
    u = usuario_actual()
    if rol == "desarrollador" and u["rol"] != "desarrollador": return jsonify({"error": "Sin permisos"}), 403
    d = _PRIVILEGIOS_DEFAULT.get(rol, {m: False for m in _MODULOS_DISPONIBLES})
    if _guardar_privilegios_rol(rol, d):
        return jsonify({"ok":True,"mensaje":f"Privilegios de '{rol}' restablecidos","privilegios":d})
    return jsonify({"error": "No se pudieron guardar"}), 500

# ── Usuarios ─────────────────────────────────────────────────
@admin_bp.route("/api/usuarios/crear", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_crear_usuario():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = crear_usuario(datos, creado_por_rol=u["rol"], creado_por_id=u["usuario_id"])
    if resultado.get("ok") and resultado.get("usuario_id") and _sb.SUPABASE_OK:
        threading.Thread(target=sincronizar_usuario_nuevo, args=(resultado["usuario_id"],), daemon=True).start()
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@admin_bp.route("/api/usuarios", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_usuarios():
    try:
        u = usuario_actual()
        usuarios = listar_usuarios(u["rol"], u["usuario_id"])
        return jsonify({"usuarios": usuarios, "total": len(usuarios)})
    except Exception as e:
        return jsonify({"error": f"Error al listar usuarios: {str(e)}"}), 500

@admin_bp.route("/api/usuarios/<usuario_id>", methods=["DELETE"])
@requiere_rol("desarrollador","administrador")
def api_desactivar_usuario(usuario_id):
    u = usuario_actual()
    resultado = desactivar_usuario(usuario_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@admin_bp.route("/api/usuarios/<usuario_id>/reset-password", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_reset_password(usuario_id):
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = resetear_password(usuario_id, datos.get("password_nueva",""), u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

# ── Licencias (sistema DB original) ──────────────────────────
@admin_bp.route("/api/licencias", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_licencias():
    u = usuario_actual()
    admin_filtro = request.args.get("admin_id")
    licencias = listar_licencias(u["usuario_id"], admin_filtro)
    return jsonify({"licencias": licencias, "total": len(licencias)})

@admin_bp.route("/api/licencias/crear", methods=["POST"])
@requiere_rol("desarrollador")
def api_crear_licencia():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    tipo_dias = {"diaria":1,"mensual":30,"anual":365,"ilimitada":99999}
    tipo = datos.get("tipo", "anual")
    dias = datos.get("dias") or tipo_dias.get(tipo, 365)
    resultado = crear_licencia(
        admin_id=datos.get("admin_id",""), tipo=tipo, dias=int(dias),
        notas=datos.get("notas",""), dev_id=u["usuario_id"],
        cliente_id=datos.get("cliente_id",""),
        clave_activacion=datos.get("clave_activacion","")
    )
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@admin_bp.route("/api/licencias/<licencia_id>", methods=["DELETE"])
@requiere_rol("desarrollador")
def api_desactivar_licencia(licencia_id):
    u = usuario_actual()
    resultado = desactivar_licencia(licencia_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@admin_bp.route("/api/licencias/verificar/<admin_id>", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_verificar_licencia(admin_id):
    lic = verificar_licencia_activa(admin_id)
    return jsonify({"tiene_licencia": lic is not None, "licencia": lic})
