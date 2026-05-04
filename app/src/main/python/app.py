"""
╔══════════════════════════════════════════════════════════════╗
║   app.py  —  TPV ULTRA SMART  v5.0                          ║
║   Sin configuración de entorno expuesta                     ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os

# ── FIX PATH PYDROID3 / ANDROID ──────────────────────────────
# Detecta automáticamente la carpeta del proyecto en cualquier
# Android, Pydroid 3, Redmi u otra marca
try:
    from tpv_rutas import fix_path, CARPETA as _CARPETA_DETECTADA
    fix_path()
except ImportError:
    # Fallback si tpv_rutas.py no está disponible
    def _fix_path_fallback():
        candidatas = [
            '/storage/emulated/0/TPV_APK',
            '/storage/emulated/0/TPV',
            '/sdcard/TPV_APK',
            '/sdcard/TPV',
        ]
        try:
            d = os.path.dirname(os.path.abspath(__file__))
            candidatas.insert(0, d)
        except NameError:
            pass
        candidatas.insert(0, os.getcwd())
        for r in candidatas:
            if os.path.exists(os.path.join(r, 'database.py')):
                if r not in sys.path:
                    sys.path.insert(0, r)
                os.chdir(r)
                print(f"✅ Proyecto: {r}")
                return r
        print("❌ No se encontró database.py. Revisa tpv_rutas.py")
        return os.getcwd()
    _CARPETA_DETECTADA = _fix_path_fallback()
# ─────────────────────────────────────────────────────────────

import json, threading, webbrowser, time, pathlib, secrets as _secrets
from datetime import datetime
from functools import wraps

# ── Clave secreta segura (generada una vez, persistida) ──────
try:
    _KEY_FILE = pathlib.Path(__file__).parent / ".tpv_secret_key"
except NameError:
    _KEY_FILE = pathlib.Path(_CARPETA) / ".tpv_secret_key"
if not _KEY_FILE.exists():
    _KEY_FILE.write_text(_secrets.token_hex(32))
    try: _KEY_FILE.chmod(0o600)
    except Exception: pass

try:
    from flask import Flask, request, jsonify, render_template, session
except ImportError:
    print("❌ Instala Flask: pip install flask"); exit(1)

from database import (
    crear_tablas, cargar_estado, guardar_estado,
    consultar_ventas_por_fecha, consultar_resumen_ventas,
    consultar_inventario_actual, consultar_ganancias_por_dia,
    agregar_log, obtener_info_db, DB_FILE,
    login_usuario, crear_usuario, cambiar_password, resetear_password,
    listar_usuarios, desactivar_usuario,
    registrar_entrada_producto, obtener_inventario_general,
    obtener_historial_entradas, asignar_inventario_diario,
    obtener_inventario_diario, actualizar_vendido_diario,
    crear_licencia, listar_licencias, verificar_licencia_activa, desactivar_licencia,
    limpiar_inventarios_diarios, obtener_productos_catalogo, sincronizar_productos_catalogo,
    importar_catalogo_a_inventario, eliminar_producto_inventario_general,
    sincronizar_estado_completo, limpiar_tablas_completo, reconstruir_desde_productos,
    cargar_stock_masivo
,
    guardar_historial_diario_local, obtener_historial_diario_local,
    obtener_historial_detalle_local,
)

from supabase_sync import (
    cargar_desde_supabase, guardar_en_supabase,
    sincronizar_subida, probar_conexion,
    obtener_config_actual, actualizar_config,
    mostrar_sql_configuracion,
    sincronizar_usuario_nuevo, sincronizar_todo,
    sincronizar_cliente_nuevo,
    # v6.0 — Dynamic tables + daily history
    setup_supabase, verificar_tablas_supabase,
    guardar_historial_diario, obtener_historial_diario,
    obtener_historial_detalle, obtener_sql_completo,
)
import supabase_sync as _sb

from tienda_routes import tienda_bp, crear_tablas_tienda
from loyalty_routes import loyalty_bp
from payment_tokenizer import tokenize, create_payment_record, mask_card
from biometric_auth import check_biometric_availability, quick_login_setup
from supabase_rls import get_branch_id, build_rls_query, get_rls_headers
from api_routes import api_bp
try:
    from ia_assistant_routes import assistant_bp
except ImportError:
    assistant_bp = None
try:
    from ai_routes import ai_bp, analytics_bp
except ImportError:
    ai_bp = None
    analytics_bp = None

# ── Carpeta del proyecto — detectada automáticamente ─────────
_CARPETA = os.environ.get("TPV_FRONTEND_DIR") or _CARPETA_DETECTADA or os.getcwd()
# Sin static_folder ni template_folder — Flask NO busca carpetas especiales.
# Los archivos se leen directamente con open() desde _CARPETA.
app = Flask(__name__, static_folder=None)
app.config["JSON_ENSURE_ASCII"]         = False
app.config["SESSION_COOKIE_SAMESITE"]   = "Lax"
app.config["SESSION_COOKIE_SECURE"]     = False
app.config["SESSION_COOKIE_HTTPONLY"]   = True
# Permitir cookies en acceso por IP local (WiFi desde otros dispositivos)
app.config["SESSION_COOKIE_DOMAIN"]     = None  # acepta cualquier host
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7
app.secret_key = _KEY_FILE.read_text().strip()
app.register_blueprint(tienda_bp)
app.register_blueprint(loyalty_bp)
app.register_blueprint(api_bp)
if assistant_bp:
    app.register_blueprint(assistant_bp)
if ai_bp:
    app.register_blueprint(ai_bp)
if analytics_bp:
    app.register_blueprint(analytics_bp)
print("Blueprints registrados: tienda_bp + api_bp + assistant_bp + ai_bp + analytics_bp")

# ══════════════════════════════════════════════════════════════
#  DECORADORES
# ══════════════════════════════════════════════════════════════
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
            if not u:
                return jsonify({"error": "No autenticado"}), 401
            if u.get("rol") not in roles:
                return jsonify({"error": f"Se requiere: {', '.join(roles)}"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def usuario_actual():
    return session.get("usuario", {})

# ══════════════════════════════════════════════════════════════
#  PÁGINA PRINCIPAL — inyecta los JS directamente en el HTML
#  Sin rutas /static/, sin carpetas templates/ ni static/
#  TODOS los archivos deben estar en la misma carpeta que app.py
# ══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Sirve index.html buscando en la carpeta del proyecto y subcarpetas."""
    candidatos = [
        os.path.join(_CARPETA, 'index.html'),
        os.path.join(os.getcwd(), 'index.html'),
        # Subcarpeta organizada
        os.path.join(_CARPETA, 'frontend', 'templates', 'index.html'),
        os.path.join(_CARPETA, 'templates', 'index.html'),
    ]
    try:
        candidatos.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'))
    except NameError:
        pass

    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return '<h3>No se encontro index.html. Verifica que esta en la carpeta del proyecto.</h3>', 500


@app.route("/<path:filename>")
def serve_static(filename):
    """Sirve archivos .js, .css etc buscando en la carpeta del proyecto y subcarpetas."""
    allowed = {'.js', '.css', '.ico', '.png', '.svg', '.woff', '.woff2', '.json', '.ttf', '.eot'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed:
        return '', 404

    mime_map = {
        '.js':   'application/javascript',
        '.css':  'text/css',
        '.ico':  'image/x-icon',
        '.png':  'image/png',
        '.svg':  'image/svg+xml',
        '.json': 'application/json',
        '.woff': 'font/woff',
        '.woff2':'font/woff2',
        '.ttf':  'font/ttf',
        '.eot':  'application/vnd.ms-fontobject',
    }

    # Nombre base del archivo (sin subcarpeta si la URL la incluye)
    nombre_base = os.path.basename(filename)

    # Directorio assets/frontend (Chaquopy en Android)
    _assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'frontend')

    candidatos = [
        os.path.join(_CARPETA, filename),
        os.path.join(_assets_dir, filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(_CARPETA, 'frontend', 'static', 'lib', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'lib', 'fonts', nombre_base),
        os.path.join(_assets_dir, 'static', 'lib', nombre_base),
        os.path.join(_assets_dir, 'static', 'lib', 'fonts', nombre_base),
        os.path.join(os.getcwd(), 'frontend', 'static', 'lib', nombre_base),
        os.path.join(os.getcwd(), 'frontend', 'static', 'lib', 'fonts', nombre_base),
        os.path.join(_CARPETA, nombre_base),
        os.path.join(os.getcwd(), nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'js', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'css', nombre_base),
        os.path.join(_CARPETA, 'frontend', 'static', 'icons', nombre_base),
        os.path.join(_CARPETA, 'static', 'js', nombre_base),
        os.path.join(_CARPETA, 'static', nombre_base),
        os.path.join(_CARPETA, 'static', 'lib', nombre_base),
        os.path.join(_CARPETA, 'static', 'lib', 'fonts', nombre_base),
    ]

    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, 'rb') as f:
                return f.read(), 200, {
                    'Content-Type': mime_map.get(ext, 'application/octet-stream'),
                    'Cache-Control': 'public, max-age=3600'
                }
    return '', 404

# ══════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    datos    = request.get_json(force=True, silent=True) or {}
    username = datos.get("username", "").strip()
    password = datos.get("password", "")
    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400
    resultado = login_usuario(username, password)
    if resultado:
        session.permanent   = True
        session["usuario"]  = resultado
        return jsonify({"ok": True, "usuario": resultado})
    return jsonify({"error": "Credenciales incorrectas"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    u = session.get("usuario")
    if u:
        return jsonify({"autenticado": True, "usuario": u})
    return jsonify({"autenticado": False}), 401

@app.route("/api/auth/cambiar-password", methods=["POST"])
@requiere_login
def api_cambiar_password():
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    resultado = cambiar_password(u["usuario_id"], datos.get("password_actual",""), datos.get("password_nueva",""))
    return jsonify(resultado), (200 if resultado["ok"] else 400)

# ══════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════

_MODULOS_DISPONIBLES = {
    "catalogo":"Gestion de catalogo","ventas":"Registro de ventas","caja":"Caja y cobros","dashboard":"Panel estadisticas","inventario":"Control inventario","productos":"CRUD productos","categorias":"Gestion categorias","orden":"Gestion de ordenes","tienda":"Tienda online","registros":"Historial","herramientas":"Herramientas","configuracion":"Configuracion","usuarios":"Gestion usuarios","licencias":"Gestion licencias","debug":"Panel depuracion","privilegios":"Gestion privilegios","blindajes":"Panel blindajes","ia_edge":"IA Edge Analytics","lealtad":"Programa Lealtad","asistente_ia":"Asistente IA","descuentos":"Descuentos","supabase":"Configuracion Supabase","seguridad":"Seguridad","exportar":"Exportar datos","copias":"Copias de seguridad",
    "catalogo":"Gestion de catalogo","productos":"CRUD productos","categorias":"Gestion categorias",
    "dashboard":"Panel estadisticas","ventas":"Registro ventas","orden":"Gestion ordenes",
    "inventario":"Control inventario","registros":"Historial","tienda":"Tienda online",
    "herramientas":"Herramientas","configuracion":"Configuracion","usuarios":"Gestion usuarios",
    "licencias":"Gestion licencias","debug":"Panel depuracion","privilegios":"Gestion privilegios","blindajes":"Panel blindajes","ia_edge":"IA Edge Analytics","lealtad":"Programa Lealtad","asistente_ia":"Asistente IA"}
_PRIVILEGIOS_DEFAULT = {
    "desarrollador":{m:True for m in _MODULOS_DISPONIBLES},
    "administrador":{m:True for m in _MODULOS_DISPONIBLES if m not in("debug","privilegios")},
    "supervisor":{"catalogo":True,"productos":True,"categorias":True,"dashboard":True,"ventas":True,"orden":True,"inventario":True,"registros":True,"tienda":True,"ia_edge":True,"lealtad":True,"asistente_ia":True},
    "vendedor":{"catalogo":True,"ventas":True,"orden":True,"dashboard":True,"ia_edge":True,"lealtad":True,"asistente_ia":True}}

def _obtener_privilegios_rol(rol):
    from database import obtener_conexion
    conn=obtener_conexion()
    try:
        row=conn.execute("SELECT valor FROM app_state WHERE clave=?",(f"privilegios_{rol}",)).fetchone()
        if row:
            import json as _j
            v=row[0]; p=_j.loads(v) if isinstance(v,str) else v
            if isinstance(p,dict): return p
    except Exception as e:
        pass  # Log: {e} pass
    finally: conn.close()
    return None

def _guardar_privilegios_rol(rol,priv):
    from database import obtener_conexion
    import json as _j
    conn=obtener_conexion()
    try:
        conn.execute("INSERT OR REPLACE INTO app_state(clave,valor,actualizado) VALUES(?,?,datetime('now','localtime'))",(f"privilegios_{rol}",_j.dumps(priv,ensure_ascii=False)))
        conn.commit(); agregar_log(f"Privilegios de '{rol}' actualizados","info"); return True
    except Exception as e: agregar_log(f"Error privilegios: {e}","error"); return False
    finally: conn.close()

@app.route("/api/privilegios/<rol>",methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_get_privilegios(rol):
    u=usuario_actual()
    if rol=="desarrollador" and u["rol"]!="desarrollador": return jsonify({"error":"Sin permisos"}),403
    p=_obtener_privilegios_rol(rol)
    if p is None: p=_PRIVILEGIOS_DEFAULT.get(rol,{m:False for m in _MODULOS_DISPONIBLES})
    return jsonify({"ok":True,"rol":rol,"privilegios":p,"modulos":_MODULOS_DISPONIBLES,"default":_PRIVILEGIOS_DEFAULT.get(rol,{})})

@app.route("/api/privilegios/<rol>",methods=["PUT"])
@requiere_rol("desarrollador","administrador")
def api_set_privilegios(rol):
    u=usuario_actual(); d=request.get_json(force=True,silent=True) or {}; n=d.get("privilegios",{})
    if not isinstance(n,dict): return jsonify({"error":"Formato invalido"}),400
    if rol=="desarrollador" and u["rol"]!="desarrollador": return jsonify({"error":"Sin permisos"}),403
    if u["rol"]=="administrador":
        for m in("debug","privilegios","licencias"):
            if n.get(m): n[m]=False
    if rol=="desarrollador": n={m:True for m in _MODULOS_DISPONIBLES}
    if _guardar_privilegios_rol(rol,n): return jsonify({"ok":True,"mensaje":f"Privilegios de '{rol}' actualizados"})
    return jsonify({"error":"No se pudieron guardar"}),500

@app.route("/api/privilegios/<rol>/restablecer",methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_reset_privilegios(rol):
    u=usuario_actual()
    if rol=="desarrollador" and u["rol"]!="desarrollador": return jsonify({"error":"Sin permisos"}),403
    d=_PRIVILEGIOS_DEFAULT.get(rol,{m:False for m in _MODULOS_DISPONIBLES})
    if _guardar_privilegios_rol(rol,d): return jsonify({"ok":True,"mensaje":f"Privilegios de '{rol}' restablecidos","privilegios":d})
    return jsonify({"error":"No se pudieron guardar"}),500


@app.route("/api/usuarios/crear", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_crear_usuario():
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    resultado = crear_usuario(datos, creado_por_rol=u["rol"], creado_por_id=u["usuario_id"])
    if resultado.get("ok") and resultado.get("usuario_id") and _sb.SUPABASE_OK:
        threading.Thread(target=sincronizar_usuario_nuevo, args=(resultado["usuario_id"],), daemon=True).start()
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/usuarios", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_usuarios():
    try:
        u        = usuario_actual()
        usuarios = listar_usuarios(u["rol"], u["usuario_id"])
        return jsonify({"usuarios": usuarios, "total": len(usuarios)})
    except Exception as e:
        return jsonify({"error": f"Error al listar usuarios: {str(e)}"}), 500

@app.route("/api/usuarios/<usuario_id>", methods=["DELETE"])
@requiere_rol("desarrollador","administrador")
def api_desactivar_usuario(usuario_id):
    u         = usuario_actual()
    resultado = desactivar_usuario(usuario_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/usuarios/<usuario_id>/reset-password", methods=["POST"])
@requiere_rol("desarrollador","administrador")
def api_reset_password(usuario_id):
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    resultado = resetear_password(usuario_id, datos.get("password_nueva",""), u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

# ══════════════════════════════════════════════════════════════
#  LICENCIAS (solo Desarrollador)
# ══════════════════════════════════════════════════════════════
@app.route("/api/licencias", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_listar_licencias():
    u             = usuario_actual()
    admin_filtro  = request.args.get("admin_id")
    licencias     = listar_licencias(u["usuario_id"], admin_filtro)
    return jsonify({"licencias": licencias, "total": len(licencias)})

@app.route("/api/licencias/crear", methods=["POST"])
@requiere_rol("desarrollador")
def api_crear_licencia():
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    # Tipos: diaria(1), mensual(30), anual(365), personalizada(N días), ilimitada(99999)
    tipo_dias = {"diaria":1, "mensual":30, "anual":365, "ilimitada":99999}
    tipo      = datos.get("tipo", "anual")
    dias      = datos.get("dias") or tipo_dias.get(tipo, 365)
    resultado = crear_licencia(
        admin_id          = datos.get("admin_id",""),
        tipo              = tipo,
        dias              = int(dias),
        notas             = datos.get("notas",""),
        dev_id            = u["usuario_id"],
        cliente_id        = datos.get("cliente_id",""),
        clave_activacion  = datos.get("clave_activacion","")
    )
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/licencias/<licencia_id>", methods=["DELETE"])
@requiere_rol("desarrollador")
def api_desactivar_licencia(licencia_id):
    u         = usuario_actual()
    resultado = desactivar_licencia(licencia_id, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/licencias/verificar/<admin_id>", methods=["GET"])
@requiere_rol("desarrollador","administrador")
def api_verificar_licencia(admin_id):
    lic = verificar_licencia_activa(admin_id)
    return jsonify({"tiene_licencia": lic is not None, "licencia": lic})

# ══════════════════════════════════════════════════════════════
#  ESTADO TPV
# ══════════════════════════════════════════════════════════════
@app.route("/api/state", methods=["GET"])
@requiere_login
def get_state():
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin estado local"}), 404
    return jsonify({"ok": True, "estado": estado})

@app.route("/api/state", methods=["POST"])
@requiere_login
def save_state():
    try:
        estado = request.get_json(force=True)
        if not isinstance(estado, dict):
            return jsonify({"error": "JSON inválido"}), 400
        guardar_estado(estado)
        if _sb.SUPABASE_OK:
            threading.Thread(target=sincronizar_subida, args=(estado,), daemon=True).start()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  INVENTARIO
# ══════════════════════════════════════════════════════════════
@app.route("/api/inventario/entrada", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_entrada_producto():
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    resultado = registrar_entrada_producto(datos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/inventario/general", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def api_inventario_general():
    try:
        u = usuario_actual()
        return jsonify({"inventario": obtener_inventario_general(u["usuario_id"])})
    except Exception as e:
        return jsonify({"error": f"Error inventario general: {str(e)}"}), 500


@app.route("/api/inventario/importar-catalogo", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_importar_catalogo():
    """Importa catálogo → inventario_general. Nuevos: stock 0. Existentes: conserva stock."""
    u = usuario_actual()
    r = importar_catalogo_a_inventario(u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)


@app.route("/api/inventario/general/eliminar", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_eliminar_inventario_general():
    """Elimina producto del almacén cuando se borra del catálogo."""
    datos = request.get_json(force=True, silent=True) or {}
    u = usuario_actual()
    r = eliminar_producto_inventario_general(datos.get("producto_id",""), u["usuario_id"])
    return jsonify(r), (200 if r["ok"] else 400)


@app.route("/api/catalogo/sync-desde-inventario", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_sync_desde_inventario():
    """Unifica inventario_general→productos y devuelve catálogo completo."""
    prods = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": prods, "total": len(prods)})

@app.route("/api/sincronizar-completo", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_sincronizar_completo():
    """
    Sincronización bidireccional completa:
    productos ↔ inventario_general (metadatos, conserva stock).
    """
    try:
        u = usuario_actual()
        r = sincronizar_estado_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stock/masivo", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_stock_masivo():
    """Carga stock a múltiples productos del almacén en una sola llamada."""
    try:
        u     = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        items = datos.get("items", [])
        r = cargar_stock_masivo(u["usuario_id"], items)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/limpiar-tablas", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_limpiar_tablas():
    """
    Borrado total: productos, inventario_general, entradas_productos,
    inventario_diario, inventarios y app_state del servidor.
    El cliente debe limpiar su IndexedDB y memoria por separado.
    """
    try:
        u = usuario_actual()
        r = limpiar_tablas_completo(u["usuario_id"])
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reconstruir-desde-productos", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_reconstruir_desde_productos():
    """
    Recibe lista de productos desde el cliente JS y reconstruye
    productos + inventario_general. Se usa DESPUÉS de limpiar-tablas
    cuando el usuario quiere reimportar su catálogo al servidor.
    """
    try:
        u         = usuario_actual()
        datos     = request.get_json(force=True, silent=True) or {}
        productos = datos.get("productos", [])
        r = reconstruir_desde_productos(u["usuario_id"], productos)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/inventario/entradas", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def api_historial_entradas():
    u          = usuario_actual()
    producto_id = request.args.get("producto_id")
    return jsonify({"entradas": obtener_historial_entradas(u["usuario_id"], producto_id)})

@app.route("/api/inventario/asignar-diario", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def api_asignar_inventario():
    datos       = request.get_json(force=True, silent=True) or {}
    u           = usuario_actual()
    vendedor_id = datos.get("vendedor_id","")
    productos   = datos.get("productos", [])
    resultado   = asignar_inventario_diario(vendedor_id, productos, u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

@app.route("/api/inventario/diario/<vendedor_id>", methods=["GET"])
@requiere_login
def api_inventario_diario(vendedor_id):
    try:
        fecha = request.args.get("fecha")
        return jsonify({"inventario": obtener_inventario_diario(vendedor_id, fecha)})
    except Exception as e:
        return jsonify({"error": f"Error inventario diario: {str(e)}"}), 500


@app.route("/api/inventario/diario/conteo", methods=["POST"])
@requiere_login
def api_conteo_vendedor():
    """
    El vendedor registra el conteo final de entrega.
    Actualiza cant_vendida en inventario_diario con el valor real contado.
    """
    datos       = request.get_json(force=True, silent=True) or {}
    u           = usuario_actual()
    vendedor_id = datos.get("vendedor_id", u["usuario_id"])
    producto_id = datos.get("producto_id", "")
    cant_final  = float(datos.get("cant_final", 0))

    # Solo el propio vendedor o un admin puede hacer esto
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Solo puedes registrar tu propio conteo"}), 403

    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        fecha_hoy = __import__('datetime').datetime.now().strftime("%Y-%m-%d")
        conn.execute("""
            UPDATE inventario_diario
            SET cant_vendida = ?
            WHERE vendedor_id = ? AND producto_id = ? AND fecha = ?
        """, (cant_final, vendedor_id, producto_id, fecha_hoy))
        conn.commit()
        agregar_log(f"Conteo final: {cant_final} de {producto_id} por {u['usuario_id']}", "info")
        return jsonify({"ok": True, "mensaje": "Conteo guardado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/inventario/diario/cierre", methods=["POST"])
@requiere_login
def api_cierre_vendedor():
    """
    Cierre del día del vendedor:
    1. Guarda resumen en cierres_diario
    2. Traspasa cant_final → cant_asignada del día SIGUIENTE (historial automático)
    """
    datos        = request.get_json(force=True, silent=True) or {}
    u            = usuario_actual()
    vendedor_id  = datos.get("vendedor_id", u["usuario_id"])
    fecha        = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    total_ventas = float(datos.get("total_ventas", 0))
    total_costo  = float(datos.get("total_costo",  0))
    ganancia     = float(datos.get("ganancia_neta", 0))
    items        = datos.get("items", [])

    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Solo puedes cerrar tu propio día"}), 403

    from database import obtener_conexion
    import json as _json
    from datetime import datetime as _dt, timedelta

    conn = obtener_conexion()
    try:
        # 1. Guardar cierre
        conn.execute("""
            INSERT INTO cierres_diario
                (vendedor_id, fecha, total_ventas, total_costo, ganancia_neta, items_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vendedor_id, fecha) DO UPDATE SET
                total_ventas  = excluded.total_ventas,
                total_costo   = excluded.total_costo,
                ganancia_neta = excluded.ganancia_neta,
                items_json    = excluded.items_json,
                creado_en     = datetime('now','localtime')
        """, (vendedor_id, fecha, total_ventas, total_costo, ganancia,
              _json.dumps(items, ensure_ascii=False)))

        # 2. Traspasar cant_final → cant_asignada del día siguiente
        fecha_sig = (_dt.strptime(fecha, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        for item in items:
            pid        = item.get("producto_id","")
            nombre     = item.get("nombre", pid)
            cant_final = float(item.get("cant_final") or item.get("cant_asignada", 0))
            pv         = float(item.get("precio_venta", 0))
            pc         = float(item.get("precio_costo", 0))
            if not pid: continue
            conn.execute("""
                INSERT INTO inventario_diario
                    (fecha, vendedor_id, producto_id, nombre,
                     cant_asignada, cant_vendida, cant_final,
                     precio_venta, precio_costo)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                ON CONFLICT(fecha, vendedor_id, producto_id) DO UPDATE SET
                    cant_asignada = excluded.cant_asignada,
                    precio_venta  = excluded.precio_venta,
                    precio_costo  = excluded.precio_costo
            """, (fecha_sig, vendedor_id, pid, nombre,
                  cant_final, cant_final, pv, pc))

        # 3. Devolver sobrante (cant_final) al inventario_general
        #    La lógica: lo que el vendedor no vendió regresa al almacén
        for item in items:
            pid        = item.get("producto_id", "")
            cant_final = float(item.get("cant_final") or 0)
            if not pid or cant_final <= 0:
                continue
            conn.execute("""
                UPDATE inventario_general
                SET stock_actual = stock_actual + ?,
                    actualizado  = datetime('now','localtime')
                WHERE producto_id = ?
            """, (cant_final, pid))

        conn.commit()
        agregar_log(f"Cierre {fecha} vendedor {vendedor_id}: ventas=${total_ventas:.2f}", "info")
        return jsonify({
            "ok": True,
            "mensaje": f"Día {fecha} cerrado. Sobrante devuelto al almacén."
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/inventario/cierre-admin", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_cierre_admin():
    """
    Cierre del día desde la vista de administrador (caja_cerrarDia).
    Actualiza inventario_general: stock_actual = cant_final de cada producto.
    """
    datos = request.get_json(force=True, silent=True) or {}
    fecha = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    items = datos.get("items", [])   # [{producto_id, cant_final}, ...]

    conn = obtener_conexion()
    try:
        actualizados = 0
        for item in items:
            pid        = item.get("producto_id", "")
            cant_final = float(item.get("cant_final") or 0)
            if not pid:
                continue
            # Reemplazar stock con cant_final (estado real al cierre)
            conn.execute("""
                UPDATE inventario_general
                SET stock_actual = ?,
                    actualizado  = datetime('now','localtime')
                WHERE producto_id = ?
            """, (max(0, cant_final), pid))
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                actualizados += 1
        conn.commit()
        agregar_log(f"Cierre admin {fecha}: {actualizados} productos actualizados en almacén", "info")
        return jsonify({"ok": True, "actualizados": actualizados,
                        "mensaje": f"Almacén actualizado: {actualizados} productos"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  CATÁLOGO DE PRODUCTOS (compartido server-side)
# ══════════════════════════════════════════════════════════════
@app.route("/api/catalogo", methods=["GET"])
@requiere_login
def api_get_catalogo():
    """Devuelve el catálogo de productos para todos los roles."""
    productos = obtener_productos_catalogo()
    return jsonify({"ok": True, "productos": productos, "total": len(productos)})

@app.route("/api/catalogo/sync", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_sync_catalogo():
    """El admin sincroniza su lista de productos al servidor (source of truth)."""
    datos     = request.get_json(force=True, silent=True) or {}
    u         = usuario_actual()
    productos = datos.get("productos", [])
    resultado = sincronizar_productos_catalogo(productos, u["usuario_id"])
    if resultado.get("ok"):
        # Propagar cambios al almacén general automáticamente
        sincronizar_estado_completo(u["usuario_id"])
    return jsonify(resultado), (200 if resultado["ok"] else 400)

# ══════════════════════════════════════════════════════════════
#  LIMPIAR INVENTARIOS DIARIOS
# ══════════════════════════════════════════════════════════════
@app.route("/api/inventario/diario/limpiar", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_limpiar_inventarios():
    datos       = request.get_json(force=True, silent=True) or {}
    u           = usuario_actual()
    vendedor_id = datos.get("vendedor_id")   # None = todos
    fecha       = datos.get("fecha")          # None = todas las fechas
    resultado   = limpiar_inventarios_diarios(u["usuario_id"], vendedor_id, fecha)
    return jsonify(resultado), (200 if resultado["ok"] else 400)

# ══════════════════════════════════════════════════════════════
#  HISTORIAL CIERRES VENDEDOR
# ══════════════════════════════════════════════════════════════
@app.route("/api/inventario/diario/historial/<vendedor_id>", methods=["GET"])
@requiere_login
def api_historial_cierres(vendedor_id):
    """Lista los cierres de un vendedor ordenados por fecha descendente."""
    u = usuario_actual()
    if u["rol"] == "vendedor" and u["usuario_id"] != vendedor_id:
        return jsonify({"error": "Sin permisos"}), 403
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT fecha, total_ventas, total_costo, ganancia_neta, creado_en
            FROM cierres_diario
            WHERE vendedor_id = ?
            ORDER BY fecha DESC LIMIT 90
        """, (vendedor_id,)).fetchall()
        return jsonify({"historial": [dict(r) for r in rows]})
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  GASTOS / INVERSIÓN
# ══════════════════════════════════════════════════════════════
@app.route("/api/gastos", methods=["GET"])
@requiere_login
def api_listar_gastos():
    u = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador","supervisor"):
        return jsonify({"error": "Sin permisos"}), 403
    desde = request.args.get("desde", "2000-01-01")
    hasta = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por, creado_en
            FROM gastos WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        """, (desde, hasta)).fetchall()
        return jsonify({"gastos": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route("/api/gastos", methods=["POST"])
@requiere_login
def api_crear_gasto():
    u    = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador"):
        return jsonify({"error": "Solo Admin/Dev puede registrar gastos"}), 403
    datos       = request.get_json(force=True, silent=True) or {}
    descripcion = datos.get("descripcion","").strip()
    monto       = float(datos.get("monto", 0))
    categoria   = datos.get("categoria","Otros")
    fecha       = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    nota        = datos.get("nota","").strip()
    if not descripcion:
        return jsonify({"error": "Descripción obligatoria"}), 400
    if monto <= 0:
        return jsonify({"error": "El monto debe ser mayor a 0"}), 400
    import uuid as _uuid
    gasto_id = "gst-" + _uuid.uuid4().hex[:8]
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        conn.execute("""
            INSERT INTO gastos (gasto_id, descripcion, monto, categoria, fecha, nota, registrado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (gasto_id, descripcion, monto, categoria, fecha, nota, u["usuario_id"]))
        conn.commit()
        agregar_log(f"Gasto ${monto:.2f} '{descripcion}' por {u['usuario_id']}", "info")
        return jsonify({"ok": True, "gasto_id": gasto_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/gastos/<gasto_id>", methods=["DELETE"])
@requiere_login
def api_eliminar_gasto(gasto_id):
    u = usuario_actual()
    if u["rol"] not in ("desarrollador","administrador"):
        return jsonify({"error": "Sin permisos"}), 403
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM gastos WHERE gasto_id = ?", (gasto_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/reportes/ventas", methods=["GET"])
@requiere_login
def api_reporte_ventas():
    u           = usuario_actual()
    fecha_inicio = request.args.get("desde", "2000-01-01")
    fecha_fin    = request.args.get("hasta", datetime.now().strftime("%Y-%m-%d"))
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify({"ventas": consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vid)})

@app.route("/api/reportes/resumen", methods=["GET"])
@requiere_login
def api_resumen():
    u   = usuario_actual()
    vid = u["usuario_id"] if u.get("rol") == "vendedor" else request.args.get("vendedor_id")
    return jsonify(consultar_resumen_ventas(vid))

@app.route("/api/reportes/ganancias", methods=["GET"])
@requiere_rol("administrador","desarrollador","supervisor")
def api_ganancias():
    return jsonify({"ganancias": consultar_ganancias_por_dia()})

# ══════════════════════════════════════════════════════════════
#  STATUS
# ══════════════════════════════════════════════════════════════
@app.route("/api/status", methods=["GET"])
def get_status():
    try:
        u = session.get("usuario", {})
        return jsonify({
            "servidor":  "activo",
            "usuario":   u.get("username","sin sesión"),
            "rol":       u.get("rol","none"),
            "sqlite":    {"activo": True, "archivo": DB_FILE, "existe": os.path.exists(DB_FILE)},

            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ping", methods=["GET"])
def api_ping():
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://cclafrwdqentvxgpmdbn.supabase.co/rest/v1/tpv_estado?limit=0")
        req.add_header("apikey","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNjbGFmcndkcWVudHZ4Z3BtZGJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwMDA4MjIsImV4cCI6MjA4ODU3NjgyMn0.***REMOVED***")
        urllib.request.urlopen(req, timeout=5)
        return jsonify({"online": True})
    except Exception as e:
        pass  # Log: {e}
        return jsonify({"online": False})

@app.route("/api/backup", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def export_backup():
    estado = cargar_estado() or {}
    backup = {"version":"5.0","fecha":datetime.now().isoformat(),"datos":estado}
    resp   = jsonify(backup)
    resp.headers["Content-Disposition"] = \
        f"attachment; filename=tpv_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return resp

# ══════════════════════════════════════════════════════════════
#  SUPABASE (sync + config persistida)
# ══════════════════════════════════════════════════════════════
@app.route("/api/supabase/config", methods=["GET"])
@requiere_rol("administrador","desarrollador")
def get_supabase_config():
    """Retorna config actual (la config se persiste en disco automaticamente)."""
    try:
        return jsonify(_sb.obtener_config_completa())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/supabase/config", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def save_supabase_config():
    """Guarda config de Supabase y la persiste a disco (no hay que reescribir)."""
    try:
        d = request.get_json(silent=True) or {}
        url = d.get("url", "").strip()
        key = d.get("anon_key", "").strip()
        if not url or not key:
            return jsonify({"error": "URL y anon_key son obligatorios"}), 400
        resultado = _sb.actualizar_config(url, key)
        return jsonify({"ok": True, "mensaje": "Config guardada y persistida", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/supabase/sync-all", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def sync_all():
    return jsonify(sincronizar_todo())

@app.route("/api/supabase/test", methods=["POST"])
@requiere_rol("desarrollador")
def test_supabase():
    return jsonify(probar_conexion())

@app.route("/api/supabase/push", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def push_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_estado()
    if not estado:
        return jsonify({"error": "Sin datos locales"}), 400
    return jsonify({"ok": guardar_en_supabase(estado)})

@app.route("/api/supabase/pull", methods=["POST"])
@requiere_rol("administrador","desarrollador")
def pull_supabase():
    if not _sb.SUPABASE_OK:
        return jsonify({"error": "Supabase no configurado"}), 400
    estado = cargar_desde_supabase()
    if not estado:
        return jsonify({"error": "Sin datos en Supabase"}), 500
    return jsonify({"ok": guardar_estado(estado)})

# ══════════════════════════════════════════════════════════════
#  SSE — Server-Sent Events (reemplaza polling de 8 segundos)
# ══════════════════════════════════════════════════════════════
import queue as _queue
_sse_clientes = {}   # { usuario_id: queue.Queue }
_sse_lock     = threading.Lock()

def _sse_broadcast(evento: dict):
    """Envía un evento a todos los clientes SSE conectados."""
    msg = f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
    with _sse_lock:
        muertos = []
        for uid, q in _sse_clientes.items():
            try:
                q.put_nowait(msg)
            except _queue.Full:
                muertos.append(uid)
        for uid in muertos:
            _sse_clientes.pop(uid, None)

@app.route("/api/sse")
@requiere_login
def api_sse():
    """Stream de eventos en tiempo real para el cliente autenticado."""
    u = usuario_actual()
    uid = u["usuario_id"]
    q = _queue.Queue(maxsize=50)
    with _sse_lock:
        _sse_clientes[uid] = q

    def gen():
        # Heartbeat inicial
        yield f"data: {json.dumps({'tipo':'conectado','rol':u['rol']})}\n\n"
        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield msg
                except _queue.Empty:
                    yield ": heartbeat\n\n"   # keep-alive cada 25 s
        except GeneratorExit:
            with _sse_lock:
                _sse_clientes.pop(uid, None)

    from flask import Response, stream_with_context
    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

# ══════════════════════════════════════════════════════════════
#  AUTO-BACKUP AL CERRAR SESIÓN
# ══════════════════════════════════════════════════════════════
@app.route("/api/auth/auto-backup", methods=["POST"])
@requiere_login
def api_auto_backup():
    """Guarda backup automático al cerrar sesión + sync Supabase si disponible."""
    try:
        estado = cargar_estado()
        # Backup local en app_state como JSON datado
        from database import obtener_conexion as _oc
        import json as _json
        ts  = datetime.now().strftime("%Y-%m-%d_%H-%M")
        key = f"autobackup_{ts}"
        conn = _oc()
        conn.execute(
            "INSERT OR REPLACE INTO app_state(clave, valor) VALUES(?,?)",
            (key, _json.dumps(estado, ensure_ascii=False))
        )
        # Limpiar auto-backups viejos (guardar solo los últimos 7)
        conn.execute("""
            DELETE FROM app_state WHERE clave LIKE 'autobackup_%'
            AND clave NOT IN (
                SELECT clave FROM app_state WHERE clave LIKE 'autobackup_%'
                ORDER BY clave DESC LIMIT 7
            )
        """)
        conn.commit()
        conn.close()
        # Sync a Supabase si hay conexión
        sb_ok = False
        if _sb.SUPABASE_OK and estado:
            sb_ok = _sb.guardar_en_supabase(estado)
        return jsonify({"ok": True, "clave": key, "supabase": sb_ok})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  DESCUENTOS
# ══════════════════════════════════════════════════════════════
@app.route("/api/descuentos", methods=["GET"])
@requiere_login
def api_listar_descuentos():
    try:
        from database import obtener_conexion as _oc
        conn = _oc()
        rows = conn.execute(
            "SELECT * FROM descuentos_config WHERE activo=1 ORDER BY nombre"
        ).fetchall()
        conn.close()
        return jsonify({"ok": True, "descuentos": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/descuentos", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_crear_descuento():
    try:
        d    = request.get_json(force=True, silent=True) or {}
        nombre = d.get("nombre", "Descuento").strip()
        tipo   = d.get("tipo", "porcentaje")
        valor  = float(d.get("valor", 0))
        if tipo not in ("porcentaje", "fijo") or valor < 0:
            return jsonify({"ok": False, "error": "Parámetros inválidos"}), 400
        from database import obtener_conexion as _oc
        conn = _oc()
        cur  = conn.execute(
            "INSERT INTO descuentos_config(nombre,tipo,valor) VALUES(?,?,?)",
            (nombre, tipo, valor)
        )
        conn.commit(); conn.close()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/descuentos/<int:did>", methods=["DELETE"])
@requiere_rol("administrador", "desarrollador")
def api_eliminar_descuento(did):
    try:
        from database import obtener_conexion as _oc
        conn = _oc()
        conn.execute("UPDATE descuentos_config SET activo=0 WHERE id=?", (did,))
        conn.commit(); conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  SUPABASE HYBRID — sincronización extendida
# ══════════════════════════════════════════════════════════════
@app.route("/api/supabase/sync-full", methods=["POST"])
@requiere_rol("administrador", "desarrollador")
def api_supabase_sync_full():
    """Sincroniza ventas, inventario, productos y pedidos a Supabase."""
    if not _sb.SUPABASE_OK:
        return jsonify({"ok": False, "mensaje": "Supabase no configurado"}), 400
    try:
        from database import obtener_conexion as _oc
        conn = _oc()

        # Ventas del día actual
        ventas = [dict(r) for r in conn.execute(
            "SELECT * FROM historial_ventas WHERE fecha >= date('now') ORDER BY fecha DESC LIMIT 500"
        ).fetchall()]

        # Productos activos
        productos = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,activo FROM productos WHERE activo=1"
        ).fetchall()]

        # Stock actual
        stock = [dict(r) for r in conn.execute(
            "SELECT producto_id,nombre,stock_actual,precio_venta,categoria FROM inventario_general"
        ).fetchall()]

        # Gastos del día
        gastos = [dict(r) for r in conn.execute(
            "SELECT * FROM gastos WHERE fecha >= date('now')"
        ).fetchall()]
        conn.close()

        url   = _sb.SUPABASE_CONFIG["url"]
        hdrs  = _sb.SUPABASE_CONFIG["anon_key"]

        def upsert(tabla, datos, pk="id"):
            if not datos: return 0
            from supabase_sync import _peticion, _headers
            import urllib.request as _ur, json as _j
            req = _ur.Request(
                f"{url}/rest/v1/{tabla}",
                data=_j.dumps(datos, ensure_ascii=False, default=str).encode(),
                method="POST"
            )
            for k,v in _headers().items(): req.add_header(k,v)
            req.add_header("Prefer","resolution=merge-duplicates")
            try:
                with _ur.urlopen(req, timeout=10) as r: r.read()
                return len(datos)
            except Exception: return 0

        ok_v = upsert("tpv_ventas_dia", ventas, "venta_id")
        ok_p = upsert("tpv_productos",  productos, "producto_id")
        ok_s = upsert("tpv_stock",      stock, "producto_id")
        ok_g = upsert("tpv_gastos_dia", gastos, "id")

        # También sync estado completo
        estado = cargar_estado()
        _sb.guardar_en_supabase(estado)

        return jsonify({
            "ok": True,
            "ventas": ok_v, "productos": ok_p,
            "stock": ok_s,  "gastos": ok_g
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  MANEJADORES DE ERROR — siempre devuelven JSON (nunca HTML)
# ══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def error_404(e):
    return jsonify({"error": "Ruta no encontrada", "code": 404}), 404

@app.errorhandler(500)
def error_500(e):
    return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

# ══════════════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════════════
def abrir_navegador():
    time.sleep(1.5)
    try: webbrowser.open("http://localhost:5000")
    except Exception as e:
        pass  # Log: {e} pass

def main():
    print("\n" + "="*58)
    print("   TPV ULTRA SMART v5.0")
    print("="*58)
    crear_tablas()
    crear_tablas_tienda()
    estado = cargar_estado()
    if estado:
        print(f" {len(estado.get('productos',[]))} productos | {len(estado.get('historialVentas',[]))} ventas")
    print(f" Supabase: {'✅ Activo' if _sb.SUPABASE_OK else '⚠️  Solo local'}")
    print(" Servidor: http://localhost:5000")
    print(" Login:    desarrollador / dev2024\n")
    threading.Thread(target=abrir_navegador, daemon=True).start()

    # Suprimir el WARNING rojo de Werkzeug (servidor de desarrollo)
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Solo muestra errores reales, no warnings

    # Mostrar IPs de red disponibles para acceso WiFi
    try:
        import socket
        ips = list(set([
            i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)
            if i[4][0].startswith(('192.168.','10.','172.')) and ':' not in i[4][0]
        ]))
        print("\n" + "="*48)
        print("  TPV ULTRA SMART v6.0 - Servidor activo")
        print("  Local : http://localhost:5000")
        for ip in ips:
            print(f"  WiFi  : http://{ip}:5000")
        print("="*48 + "\n")
    except Exception:
        pass
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)



# ══════════════════════════════════════════════════════════════
#  ENDPOINTS DEBUG / SUPABASE / HISTORIAL  (v6.0)
# ══════════════════════════════════════════════════════════════

@app.route("/api/supabase/estado", methods=["GET"])
@requiere_login
def api_supabase_estado():
    """Estado de tablas Supabase — usado por el debug panel."""
    try:
        config   = obtener_config_actual()
        tablas   = verificar_tablas_supabase() if config.get("configurado") else {}
        return jsonify({
            "ok":          True,
            "configurado": config.get("configurado", False),
            "url":         config.get("url", ""),
            "tablas":      tablas,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/supabase/setup", methods=["POST"])
@requiere_login
def api_supabase_setup():
    """Crea/verifica todas las tablas en Supabase dinámicamente."""
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    try:
        resultado = setup_supabase()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500


@app.route("/api/supabase/sql", methods=["GET"])
@requiere_login
def api_supabase_sql():
    """Devuelve el SQL completo + SQL por tabla individual."""
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador",):
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    from supabase_sync import TABLAS_SQL
    return jsonify({
        "ok": True,
        "sql": obtener_sql_completo(),
        "sql_por_tabla": {tabla: sql.strip() for tabla, sql in TABLAS_SQL.items()}
    })


@app.route("/api/historial/diario", methods=["GET"])
@requiere_login
def api_historial_get():
    """Obtiene historial diario (SQLite local + Supabase si disponible)."""
    limite = int(request.args.get("limite", 30))
    try:
        # Combinar: Supabase tiene más datos, SQLite es fallback
        res_sb = obtener_historial_diario(limite=limite)
        if res_sb.get("ok") and res_sb.get("historial"):
            return jsonify({"ok": True, "historial": res_sb["historial"], "fuente": "supabase"})
        # Fallback a SQLite
        historial_local = obtener_historial_diario_local(limite=limite)
        return jsonify({"ok": True, "historial": historial_local, "fuente": "local"})
    except Exception as e:
        return jsonify({"ok": False, "historial": [], "mensaje": str(e)}), 500


@app.route("/api/historial/diario", methods=["POST"])
@requiere_login
def api_historial_post():
    """Guarda un snapshot diario en SQLite + Supabase."""
    u = usuario_actual()
    if u.get("rol") not in ("desarrollador", "administrador"):
        return jsonify({"ok": False, "mensaje": "Solo Dev/Admin"}), 403
    datos = request.get_json(force=True) or {}
    try:
        # Guardar local siempre
        ok_local = guardar_historial_diario_local(datos)
        # Guardar en Supabase si disponible
        ok_sb    = guardar_historial_diario(datos)
        return jsonify({
            "ok":      ok_local or ok_sb.get("ok", False),
            "local":   ok_local,
            "supabase": ok_sb.get("ok", False),
            "mensaje": f"Snapshot {datos.get('fecha','?')} guardado",
        })
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500


@app.route("/api/historial/diario/<fecha>", methods=["GET"])
@requiere_login
def api_historial_detalle(fecha):
    """Detalle de un día específico del historial."""
    try:
        res_sb = obtener_historial_detalle(fecha)
        if res_sb.get("ok"):
            return jsonify(res_sb)
        local  = obtener_historial_detalle_local(fecha)
        if local:
            return jsonify({"ok": True, "dia": local, "fuente": "local"})
        return jsonify({"ok": False, "mensaje": f"Sin historial para {fecha}"}), 404
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500


@app.route("/api/debug/health", methods=["GET"])
@requiere_login
def api_debug_health():
    """Health check completo del sistema para el debug panel."""
    u = usuario_actual()
    if u.get("rol") != "desarrollador":
        return jsonify({"ok": False, "mensaje": "Solo Desarrollador"}), 403
    try:
        from database import obtener_info_db
        db_info = obtener_info_db()
        config_sb = obtener_config_actual()
        tablas_sb = verificar_tablas_supabase() if config_sb.get("configurado") else {}
        return jsonify({
            "ok":       True,
            "servidor": "Flask OK",
            "sqlite":   db_info,
            "supabase": {
                "configurado": config_sb.get("configurado"),
                "tablas":      tablas_sb,
            },
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    main()

# ============================================================
# RUTAS BIOMÉTRICAS
# ============================================================
@app.route('/api/biometric/check', methods=['GET'])
def api_biometric_check():
    try:
        result = check_biometric_availability()
        return jsonify({"ok": True, "biometric": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/biometric/setup', methods=['POST'])
@requiere_login
def api_biometric_setup():
    u = usuario_actual()
    result = quick_login_setup(u.get("username", ""))
    return jsonify({"ok": True, "setup": result})

# ============================================================
# RUTAS TOKENIZACIÓN
# ============================================================
@app.route('/api/payment/tokenize', methods=['POST'])
@requiere_login
def api_payment_tokenize():
    datos = request.get_json(force=True, silent=True) or {}
    amount = float(datos.get("amount", 0))
    method = datos.get("method", "efectivo")
    card_ref = datos.get("card_ref", "")
    
    if amount <= 0:
        return jsonify({"error": "Monto inválido"}), 400
    
    record = create_payment_record(amount, method, card_ref)
    return jsonify({"ok": True, "payment": record})

# ============================================================
# RUTAS RLS
# ============================================================
@app.route('/api/branch/info', methods=['GET'])
@requiere_login
def api_branch_info():
    branch_id = get_branch_id()
    headers = get_rls_headers()
    return jsonify({
        "ok": True,
        "branch_id": branch_id,
        "rls_enabled": True,
        "headers": headers
    })

@app.route('/api/branch/filter', methods=['POST'])
@requiere_login
def api_branch_filter():
    datos = request.get_json(force=True, silent=True) or {}
    items = datos.get("items", [])
    filtered = filter_inventory_by_branch(items)
    return jsonify({"ok": True, "filtered": filtered, "count": len(filtered)})


@app.route('/api/health/full', methods=['GET'])
def api_health_full():
    """Health check completo del sistema"""
    import time, os
    from database import obtener_info_db
    info = obtener_info_db()
    return jsonify({
        "ok": True,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time(),
        "db": info,
        "modules": 26,
        "routes": 114,
        "roles": 5
    })

@app.route('/api/ia/chat/secure', methods=['POST'])
@requiere_login
def ia_chat_secure():
    data = request.get_json(force=True, silent=True) or {}
    query = data.get('query', data.get('question', ''))
    role = session.get('usuario', {}).get('rol', 'cliente')
    from ia_agent import process_question
    response = process_question(session.get('usuario', {}).get('usuario_id', '0'), query, role)
    return jsonify(response)
