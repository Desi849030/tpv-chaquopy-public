from flask import Blueprint, request, jsonify, session
from functools import wraps
from database import (login_usuario, crear_usuario, cambiar_password, resetear_password,
                      listar_usuarios, desactivar_usuario, crear_licencia, listar_licencias,
                      verificar_licencia_activa, desactivar_licencia)
import threading, supabase_sync as _sb

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            u = session.get("usuario")
            if not u or u.get("rol") not in roles:
                return jsonify({"error": f"Se requiere: {', '.join(roles)}"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def usuario_actual():
    return session.get("usuario", {})

@auth_bp.route("/auth/login", methods=["POST"])
def api_login():
    datos = request.get_json(force=True, silent=True) or {}
    username = datos.get("username", "").strip()
    password = datos.get("password", "")
    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400
    resultado = login_usuario(username, password)
    if resultado:
        session.permanent = True
        session["usuario"] = resultado
        return jsonify({"ok": True, "usuario": resultado})
    return jsonify({"error": "Credenciales incorrectas"}), 401

@auth_bp.route("/auth/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@auth_bp.route("/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u:
        return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

@auth_bp.route("/auth/cambiar-password", methods=["POST"])
@requiere_login
def api_cambiar_password():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = cambiar_password(u["usuario_id"], datos.get("password_actual",""), datos.get("password_nueva",""))
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/usuarios/crear", methods=["POST"])
@requiere_rol("desarrollador", "administrador")
def api_crear_usuario():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = crear_usuario(datos, creado_por_rol=u["rol"], creado_por_id=u["usuario_id"])
    if resultado.get("ok") and resultado.get("usuario_id") and _sb.SUPABASE_OK:
        threading.Thread(target=_sb.sincronizar_usuario_nuevo, args=(resultado["usuario_id"],), daemon=True).start()
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/usuarios", methods=["GET"])
@requiere_rol("desarrollador", "administrador")
def api_listar_usuarios():
    try:
        u = usuario_actual()
        usuarios = listar_usuarios(u["rol"], u["usuario_id"])
        return jsonify({"usuarios": usuarios, "total": len(usuarios)})
    except Exception as e:
        return jsonify({"error": f"Error al listar usuarios: {str(e)}"}), 500

@auth_bp.route("/usuarios/<usuario_id>", methods=["DELETE"])
@requiere_rol("desarrollador","administrador")
def api_desactivar_usuario(usuario_id):
    u = usuario_actual()
    resultado = desactivar_usuario(usuario_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/usuarios/<usuario_id>/reset-password", methods=["POST"])
@requiere_rol("desarrollador", "administrador")
def api_reset_password(usuario_id):
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    resultado = resetear_password(usuario_id, datos.get("password_nueva",""), u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/licencias", methods=["GET"])
@requiere_rol("desarrollador", "administrador")
def api_listar_licencias():
    u = usuario_actual()
    admin_filtro = request.args.get("admin_id")
    licencias = listar_licencias(u["usuario_id"], admin_filtro)
    return jsonify({"licencias": licencias, "total": len(licencias)})

@auth_bp.route("/licencias/crear", methods=["POST"])
@requiere_rol("desarrollador")
def api_crear_licencia():
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    tipo_dias = {"diaria":1, "mensual":30, "anual":365, "ilimitada":99999}
    tipo = datos.get("tipo", "anual")
    dias = datos.get("dias") or tipo_dias.get(tipo, 365)
    resultado = crear_licencia(
        admin_id=datos.get("admin_id",""), tipo=tipo, dias=int(dias),
        notas=datos.get("notas",""), dev_id=u["usuario_id"],
        cliente_id=datos.get("cliente_id",""), clave_activacion=datos.get("clave_activacion","")
    )
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/licencias/<licencia_id>", methods=["DELETE"])
@requiere_rol("desarrollador")
def api_desactivar_licencia(licencia_id):
    u = usuario_actual()
    resultado = desactivar_licencia(licencia_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@auth_bp.route("/licencias/verificar/<admin_id>", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_verificar_licencia(admin_id):
    lic = verificar_licencia_activa(admin_id)
    return jsonify({"tiene_licencia": lic is not None, "licencia": lic})
