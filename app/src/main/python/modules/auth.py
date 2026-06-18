from flask import Blueprint, request, jsonify, session
from functools import wraps
from decorators import login_required, requiere_rol, usuario_actual
from db_config import crear_licencia, desactivar_licencia, listar_licencias, verificar_licencia_activa
from db.users import cambiar_password, crear_usuario, desactivar_usuario, listar_usuarios, login_usuario, resetear_password
import threading, hashlib, secrets, supabase_sync as _sb

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


# ══════════════════════════════════════════════════════════════
#  LOGIN BIOMÉTRICO POR TOKEN DE DISPOSITIVO
#  La huella/rostro se verifica en Android (BiometricPrompt via
#  TPVNative). Si pasa, el cliente canjea un token de dispositivo
#  emitido previamente. El servidor guarda SOLO el hash SHA-256
#  del token: nunca contraseñas hardcodeadas ni tokens en claro.
# ══════════════════════════════════════════════════════════════

_BIO_TABLE = """CREATE TABLE IF NOT EXISTS bio_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash  TEXT    NOT NULL UNIQUE,
    usuario_id  TEXT    NOT NULL,
    device      TEXT    DEFAULT '',
    activo      INTEGER DEFAULT 1,
    creado      TEXT    DEFAULT (datetime('now','localtime')),
    ultimo_uso  TEXT    DEFAULT NULL
)"""


def _bio_conn():
    from db_connection import obtener_conexion
    conn = obtener_conexion()
    conn.execute(_BIO_TABLE)
    return conn


def _bio_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@auth_bp.route("/auth/bio/registrar", methods=["POST"])
@login_required
def api_bio_registrar():
    """Emite un token de dispositivo para login biométrico.

    Requiere sesión activa (el usuario acaba de entrar con contraseña).
    El token se devuelve UNA sola vez; el servidor guarda su hash.
    Un nuevo registro del mismo usuario+dispositivo revoca el anterior.
    """
    u = usuario_actual()
    datos = request.get_json(silent=True) or {}
    device = str(datos.get("device", ""))[:120]
    token = secrets.token_urlsafe(32)  # 256 bits aleatorios
    conn = _bio_conn()
    try:
        # Revocar tokens previos de este usuario en este dispositivo
        conn.execute(
            "UPDATE bio_tokens SET activo=0 WHERE usuario_id=? AND device=?",
            (u["usuario_id"], device))
        conn.execute(
            "INSERT INTO bio_tokens (token_hash, usuario_id, device) VALUES (?,?,?)",
            (_bio_hash(token), u["usuario_id"], device))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "token": token})


@auth_bp.route("/auth/bio/login", methods=["POST"])
def api_bio_login():
    """Login canjeando un token de dispositivo (tras BiometricPrompt OK).

    Protección anti fuerza bruta: los intentos fallidos se registran en
    login_intentos bajo el pseudo-usuario 'bio-token' (mismo bloqueo
    de 5 fallos / 10 min que el login normal).
    """
    datos = request.get_json(silent=True) or {}
    token = datos.get("token", "")
    if not token or len(token) < 20:
        return jsonify({"ok": False, "error": "Token requerido"}), 400

    conn = _bio_conn()
    try:
        # Bloqueo por intentos fallidos (reutiliza login_intentos)
        from datetime import datetime, timedelta
        hace10 = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            fallos = conn.execute(
                "SELECT COUNT(*) FROM login_intentos "
                "WHERE username='bio-token' AND exito=0 AND timestamp>?",
                (hace10,)).fetchone()[0]
            if fallos >= 5:
                return jsonify({"ok": False,
                                "error": "Demasiados intentos. Espera 10 minutos."}), 429
        except Exception:
            pass

        fila = conn.execute(
            "SELECT b.usuario_id, u.username, u.nombre, u.rol "
            "FROM bio_tokens b JOIN usuarios u ON u.usuario_id = b.usuario_id "
            "WHERE b.token_hash=? AND b.activo=1 AND u.activo=1",
            (_bio_hash(token),)).fetchone()

        def _registrar(exito):
            try:
                conn.execute(
                    "INSERT INTO login_intentos(username, exito) VALUES('bio-token',?)",
                    (1 if exito else 0,))
                conn.commit()
            except Exception:
                pass

        if not fila:
            _registrar(False)
            return jsonify({"ok": False,
                            "error": "Token inválido o revocado. Entra con contraseña."}), 401

        conn.execute(
            "UPDATE bio_tokens SET ultimo_uso=datetime('now','localtime') "
            "WHERE token_hash=?", (_bio_hash(token),))
        conn.commit()
        _registrar(True)

        user = {
            "id": fila["usuario_id"], "usuario_id": fila["usuario_id"],
            "username": fila["username"],
            "nombre": fila["nombre"] or fila["username"],
            "rol": fila["rol"] or "vendedor",
        }
        session.permanent = True
        session["usuario"] = user
        return jsonify({"ok": True, "usuario": user})
    finally:
        conn.close()


@auth_bp.route("/auth/bio/revocar", methods=["POST"])
@login_required
def api_bio_revocar():
    """Revoca los tokens biométricos del usuario actual (o uno por device)."""
    u = usuario_actual()
    datos = request.get_json(silent=True) or {}
    device = datos.get("device")
    conn = _bio_conn()
    try:
        if device is not None:
            cur = conn.execute(
                "UPDATE bio_tokens SET activo=0 WHERE usuario_id=? AND device=?",
                (u["usuario_id"], str(device)[:120]))
        else:
            cur = conn.execute(
                "UPDATE bio_tokens SET activo=0 WHERE usuario_id=?",
                (u["usuario_id"],))
        conn.commit()
        return jsonify({"ok": True, "revocados": cur.rowcount})
    finally:
        conn.close()




@auth_bp.route("/auth/login", methods=["POST"])
def api_login():
    """Login atomico con session_token unico."""
    import secrets
    datos = request.get_json(silent=True) or {}
    username = datos.get("username", "").strip()
    password = datos.get("password", "").strip()
    if not username or not password:
        return jsonify({"ok": False, "error": "Usuario y contrasena requeridos"}), 400
    try:
        resultado = login_usuario(username, password)
    except Exception as e:
        resultado = None
        print("login_usuario error:", e)
    if isinstance(resultado, dict) and resultado.get("error") == "bloqueado":
        return jsonify({"ok": False, "error": resultado.get("mensaje", "Cuenta bloqueada")}), 429
    if resultado and resultado.get("usuario_id"):
        session.clear()
        session_token = secrets.token_urlsafe(32)
        user = {
            "id": resultado["usuario_id"], "usuario_id": resultado["usuario_id"],
            "username": resultado["username"],
            "nombre": resultado.get("nombre", resultado["username"]),
            "rol": resultado.get("rol", "vendedor"),
            "session_token": session_token,
        }
        session.permanent = True
        session["usuario"] = user
        session["session_token"] = session_token
        session.pop("_active_check_ts", None)
        return jsonify({"ok": True, "usuario": user, "session_token": session_token})
    return jsonify({"ok": False, "error": "Usuario o contrasena incorrectos"}), 401

@auth_bp.route("/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    response = jsonify({"ok": True})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response

@auth_bp.route("/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u:
        return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

@auth_bp.route("/auth/cambiar-password", methods=["POST"])
@login_required
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

def _get_default_password(): return 'admin123'
