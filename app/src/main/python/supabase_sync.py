from sync.config import *

def guardar_en_supabase(estado: dict) -> bool:
    if not SUPABASE_OK:
        return False
    tabla = SUPABASE_CONFIG["tabla_estado"]
    rid   = SUPABASE_CONFIG["registro_id"]
    datos = {"estado": estado, "actualizado": datetime.now().isoformat()}

    res = _peticion(f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}?id=eq.{rid}",
                    metodo="PATCH", datos=datos)
    if res is None or res == []:
        datos_post = {"id": rid, "dispositivo": "principal",
                      "estado": estado, "actualizado": datetime.now().isoformat()}
        res = _peticion(f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}",
                        metodo="POST", datos=datos_post)

    if res is not None:
        print(f"☁️  Estado guardado en Supabase ({datetime.now().strftime('%H:%M:%S')})")
        return True
    return False


def sincronizar_subida(estado: dict):
    guardar_en_supabase(estado)

# ══════════════════════════════════════════════════════════════
#  USUARIOS Y CLIENTES
# ══════════════════════════════════════════════════════════════
def sincronizar_usuario_nuevo(usuario_id: str):
    if not SUPABASE_OK:
        return
    try:
        import sqlite3
        from database import DB_FILE
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT usuario_id, username, nombre, rol,
                   password_hash, password_salt, activo
            FROM usuarios WHERE usuario_id = ?
        """, (usuario_id,))
        u = cursor.fetchone()
        conn.close()
        if not u: return
        datos = dict(u)
        datos["activo"] = bool(datos["activo"])
        tabla = SUPABASE_CONFIG["tabla_usuarios"]
        url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"
        res   = _peticion(f"{url}?usuario_id=eq.{usuario_id}", metodo="PATCH", datos=datos)
        if res == [] or res is None:
            _peticion(url, metodo="POST", datos=datos)
        print(f"☁️  Usuario '{u['username']}' sincronizado en Supabase")
    except Exception as e:
        print(f"⚠️  Error sincronizando usuario: {e}")


def sincronizar_usuarios_a_supabase() -> dict:
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}
    try:
        import sqlite3
        from database import DB_FILE
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        usuarios = [dict(u) for u in conn.execute(
            "SELECT usuario_id,username,nombre,rol,password_hash,password_salt,activo,ultimo_acceso FROM usuarios WHERE activo=1"
        ).fetchall()]
        conn.close()
    except Exception as e:
        return {"ok": False, "mensaje": f"Error leyendo SQLite: {e}"}

    tabla = SUPABASE_CONFIG["tabla_usuarios"]
    url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"
    ok_count = 0
    for u in usuarios:
        u["activo"] = bool(u["activo"])
        res = _peticion(f"{url}?usuario_id=eq.{u['usuario_id']}", metodo="PATCH", datos=u)
        if res == [] or res is None:
            res = _peticion(url, metodo="POST", datos=u)
        if res is not None:
            ok_count += 1
    return {"ok": True, "mensaje": f"Usuarios sincronizados: {ok_count}/{len(usuarios)}", "sincronizados": ok_count}


def sincronizar_cliente_nuevo(cliente_id: str):
    if not SUPABASE_OK:
        return
    try:
        import sqlite3
        from database import DB_FILE
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes_tienda WHERE cliente_id=?", (cliente_id,))
        c = cursor.fetchone()
        conn.close()
        if not c: return
        datos = dict(c)
        datos["activo"] = bool(datos.get("activo", True))
        datos.pop("creado", None)
        tabla = SUPABASE_CONFIG["tabla_clientes"]
        url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"
        res   = _peticion(f"{url}?cliente_id=eq.{cliente_id}", metodo="PATCH", datos=datos)
        if res == [] or res is None:
            _peticion(url, metodo="POST", datos=datos)
        print(f"☁️  Cliente '{c['email']}' sincronizado en Supabase")
    except Exception as e:
        print(f"⚠️  Error sincronizando cliente: {e}")


def sincronizar_todos_clientes() -> dict:
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}
    try:
        import sqlite3
        from database import DB_FILE
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        clientes = [dict(c) for c in conn.execute(
            "SELECT cliente_id,nombre,email,telefono,password_hash,password_salt,activo FROM clientes_tienda WHERE activo=1"
        ).fetchall()]
        conn.close()
    except Exception as e:
        return {"ok": False, "mensaje": f"Error: {e}"}

    tabla = SUPABASE_CONFIG["tabla_clientes"]
    url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"
    ok_count = 0
    for c in clientes:
        c["activo"] = bool(c["activo"])
        res = _peticion(f"{url}?cliente_id=eq.{c['cliente_id']}", metodo="PATCH", datos=c)
        if res == [] or res is None:
            res = _peticion(url, metodo="POST", datos=c)
        if res is not None:
            ok_count += 1
    return {"ok": True, "mensaje": f"{ok_count}/{len(clientes)} clientes sincronizados", "total": ok_count}


def sincronizar_todo() -> dict:
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}
    from database import cargar_estado
    resultados = {}
    estado = cargar_estado()
    if estado:
        resultados["estado"] = guardar_en_supabase(estado)
    resultados["usuarios"] = sincronizar_usuarios_a_supabase()
    resultados["clientes"] = sincronizar_todos_clientes()

    # Sync ventas
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 100")
        ventas = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if ventas:
            from supabase_sync import guardar_en_supabase
            resultados["ventas"] = guardar_en_supabase({"ventas": ventas})
            print("  Ventas sincronizadas")
    except Exception as e:
        print(f"  Error sync ventas: {e}")

    # Sync inventario/stock
    try:
        from database import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventario_general ORDER BY producto_id")
        stock = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if stock:
            from supabase_sync import guardar_en_supabase
            resultados["inventario"] = guardar_en_supabase({"inventario": stock})
            print("  Inventario sincronizado")
    except Exception as e:
        print(f"  Error sync inventario: {e}")

    return {
        "ok":         True,
        "estado":     resultados.get("estado", False),
        "usuarios":   resultados.get("usuarios", {}),
        "clientes":   resultados.get("clientes", {}),
        "ventas":     resultados.get("ventas", False),
        "inventario": resultados.get("inventario", False),
    }

# ══════════════════════════════════════════════════════════════
#  UTILIDADES
# ══════════════════════════════════════════════════════════════
def probar_conexion() -> dict:
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}
    tabla = SUPABASE_CONFIG["tabla_estado"]
    url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}?limit=1"
    res   = _peticion(url, timeout=5)
    if res is not None:
        return {"ok": True, "mensaje": f"Conexión exitosa a {SUPABASE_CONFIG['url']}"}
    return {"ok": False, "mensaje": "No se pudo conectar. Verifica URL y anon_key."}


def obtener_config_actual() -> dict:
    url = SUPABASE_CONFIG.get("url", "")
    key = SUPABASE_CONFIG.get("anon_key", "")
    k   = key[:8] + "..." + key[-4:] if len(key) > 12 else "no configurada"
    return {
        "url":              url,
        "anon_key_preview": k,
        "tabla_estado":     SUPABASE_CONFIG["tabla_estado"],
        "tabla_usuarios":   SUPABASE_CONFIG["tabla_usuarios"],
        "tabla_clientes":   SUPABASE_CONFIG["tabla_clientes"],
        "configurado":      SUPABASE_OK,
    }


def actualizar_config(nueva_url: str, nueva_key: str):
    global SUPABASE_CONFIG
    SUPABASE_CONFIG["url"]      = nueva_url.rstrip("/")
    SUPABASE_CONFIG["anon_key"] = nueva_key
    # Persistir a disco para no tener que reescribir
    _guardar_config_a_archivo()
    return verificar_supabase()


def obtener_config_completa() -> dict:
    """Retorna la config completa (incluyendo key completa) para UI."""
    return {
        "url":      SUPABASE_CONFIG.get("url", ""),
        "anon_key": SUPABASE_CONFIG.get("anon_key", ""),
        "guardado": os.path.exists(_CONFIG_FILE),
    }


# Inicializar al importar
verificar_supabase()
