"""
╔══════════════════════════════════════════════════════════════╗
║   database.py  —  TPV ULTRA SMART  v5.0                     ║
╚══════════════════════════════════════════════════════════════╝
JERARQUÍA DE ROLES:
  DESARROLLADOR  → sin límites, genera licencias por ID/móvil
  ADMINISTRADOR  → gestiona su tienda, crea supervisores/vendedores
  SUPERVISOR     → consulta reportes
  VENDEDOR       → trabaja con su inventario diario
"""
import sqlite3, json, os, hashlib, secrets, uuid
from datetime import datetime

DB_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), "tpv_datos.db")

# ══════════════════════════════════════════════════════════════
#  SEGURIDAD
# ══════════════════════════════════════════════════════════════
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
def crear_tablas():
    conn   = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            clave       TEXT    NOT NULL UNIQUE,
            valor       TEXT    NOT NULL,
            actualizado TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id    TEXT    NOT NULL UNIQUE,
            username      TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            rol           TEXT    NOT NULL CHECK(rol IN
                          ('desarrollador','administrador','supervisor','vendedor')),
            password_hash TEXT    NOT NULL,
            password_salt TEXT    NOT NULL,
            creado_por    TEXT    DEFAULT NULL,
            activo        INTEGER DEFAULT 1,
            ultimo_acceso TEXT    DEFAULT NULL,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    # ── LICENCIAS (generadas por el desarrollador) ────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licencias (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            licencia_id   TEXT    NOT NULL UNIQUE,
            admin_id      TEXT    NOT NULL,
            admin_nombre  TEXT    NOT NULL,
            tipo          TEXT    NOT NULL DEFAULT 'anual'
                          CHECK(tipo IN ('diaria','mensual','anual','personalizada','ilimitada')),
            dias          INTEGER NOT NULL DEFAULT 365,
            fecha_inicio  TEXT    NOT NULL,
            fecha_expira  TEXT    NOT NULL,
            activa        INTEGER DEFAULT 1,
            notas         TEXT    DEFAULT '',
            creado_por    TEXT    NOT NULL,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_ventas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id        TEXT    NOT NULL UNIQUE,
            producto_id     TEXT    NOT NULL,
            nombre          TEXT    NOT NULL,
            cantidad        REAL    NOT NULL DEFAULT 1,
            precio_unit     REAL    NOT NULL DEFAULT 0,
            total           REAL    NOT NULL DEFAULT 0,
            metodo_pago     TEXT    DEFAULT 'efectivo',
            vendedor_id     TEXT    DEFAULT NULL,
            vendedor_nombre TEXT    DEFAULT NULL,
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id   TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            precio        REAL    NOT NULL DEFAULT 0,
            costo         REAL    NOT NULL DEFAULT 0,
            categoria     TEXT    DEFAULT 'General',
            unidad_medida TEXT    DEFAULT 'C/U',
            en_oferta     INTEGER DEFAULT 0,
            imagen        TEXT    DEFAULT '',
            activo        INTEGER DEFAULT 1,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_general (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id   TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            stock_actual  REAL    NOT NULL DEFAULT 0,
            stock_minimo  REAL    DEFAULT 5,
            precio_compra REAL    DEFAULT 0,
            precio_venta  REAL    DEFAULT 0,
            categoria     TEXT    DEFAULT 'General',
            unidad_medida TEXT    DEFAULT 'C/U',
            actualizado   TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entradas_productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            entrada_id    TEXT    NOT NULL UNIQUE,
            producto_id   TEXT    NOT NULL,
            nombre        TEXT    NOT NULL,
            cantidad      REAL    NOT NULL DEFAULT 0,
            precio_compra REAL    DEFAULT 0,
            proveedor     TEXT    DEFAULT '',
            nota          TEXT    DEFAULT '',
            registrado_por TEXT   NOT NULL,
            fecha         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_diario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha         TEXT    NOT NULL,
            vendedor_id   TEXT    NOT NULL,
            producto_id   TEXT    NOT NULL,
            nombre        TEXT    NOT NULL,
            cant_asignada REAL    NOT NULL DEFAULT 0,
            cant_vendida  REAL    DEFAULT 0,
            cant_devuelta REAL    DEFAULT 0,
            cant_final    REAL    DEFAULT 0,
            precio_venta  REAL    DEFAULT 0,
            precio_costo  REAL    DEFAULT 0,
            activo        INTEGER DEFAULT 1,
            UNIQUE(fecha, vendedor_id, producto_id)
        )""")
    # Migración: columnas nuevas en BD existente
    for col, tipo in [
        ('cant_final',    'REAL DEFAULT 0'),
        ('precio_costo',  'REAL DEFAULT 0'),
        ('unidad_medida', "TEXT DEFAULT 'Un'"),
    ]:
        try: cursor.execute(f'ALTER TABLE inventario_diario ADD COLUMN {col} {tipo}')
        except Exception: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cierres_diario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id   TEXT    NOT NULL,
            fecha         TEXT    NOT NULL,
            total_ventas  REAL    DEFAULT 0,
            total_costo   REAL    DEFAULT 0,
            ganancia_neta REAL    DEFAULT 0,
            items_json    TEXT    DEFAULT '[]',
            creado_en     TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(vendedor_id, fecha)
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            gasto_id     TEXT    NOT NULL UNIQUE,
            descripcion  TEXT    NOT NULL,
            monto        REAL    NOT NULL DEFAULT 0,
            categoria    TEXT    DEFAULT 'Otros',
            fecha        TEXT    NOT NULL,
            nota         TEXT    DEFAULT '',
            registrado_por TEXT  DEFAULT '',
            creado_en    TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cierres_caja (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha             TEXT    NOT NULL UNIQUE,
            total_ventas      REAL    DEFAULT 0,
            total_costos      REAL    DEFAULT 0,
            total_comisiones  REAL    DEFAULT 0,
            ganancia_total    REAL    DEFAULT 0,
            num_transacciones INTEGER DEFAULT 0,
            cerrado_por       TEXT    DEFAULT NULL,
            creado            TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha         TEXT    NOT NULL,
            producto_id   TEXT    NOT NULL,
            nombre        TEXT    NOT NULL,
            cant_inicial  REAL    DEFAULT 0,
            cant_final    REAL    DEFAULT 0,
            vendido       REAL    DEFAULT 0,
            precio_venta  REAL    DEFAULT 0,
            precio_costo  REAL    DEFAULT 0,
            importe       REAL    DEFAULT 0,
            comision      REAL    DEFAULT 0,
            ganancia_neta REAL    DEFAULT 0,
            UNIQUE(fecha, producto_id)
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_sistema (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo      TEXT    DEFAULT 'info',
            usuario   TEXT    DEFAULT NULL,
            mensaje   TEXT    NOT NULL,
            timestamp TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    # ── TABLAS v5.1: seguridad, auditoría y descuentos ────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_intentos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL,
            ip         TEXT    DEFAULT '',
            exito      INTEGER DEFAULT 0,
            timestamp  TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla       TEXT    NOT NULL,
            accion      TEXT    NOT NULL,
            registro_id TEXT    NOT NULL,
            campo       TEXT    DEFAULT '',
            valor_antes TEXT    DEFAULT '',
            valor_nuevo TEXT    DEFAULT '',
            usuario_id  TEXT    NOT NULL,
            timestamp   TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS descuentos_config (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL DEFAULT 'Descuento',
            tipo        TEXT    NOT NULL DEFAULT 'porcentaje'
                        CHECK(tipo IN ('porcentaje','fijo')),
            valor       REAL    NOT NULL DEFAULT 0,
            activo      INTEGER DEFAULT 1,
            creado      TEXT    DEFAULT (datetime('now','localtime'))
        )""")

    conn.commit()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_diario (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha             TEXT    NOT NULL UNIQUE,
            total_ventas      REAL    DEFAULT 0,
            num_transacciones INTEGER DEFAULT 0,
            productos_activos INTEGER DEFAULT 0,
            inventario_items  INTEGER DEFAULT 0,
            ventas_data       TEXT    DEFAULT '[]',
            inventario_data   TEXT    DEFAULT '[]',
            config_snapshot   TEXT    DEFAULT '{}',
            ts_guardado       TEXT    DEFAULT (datetime('now','localtime'))
        )""")
    try: cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_fecha ON historial_diario(fecha DESC)")
    except Exception: pass

    # ── ÍNDICES DE RENDIMIENTO ─────────────────────────────────
    _indices = [
        "CREATE INDEX IF NOT EXISTS idx_hv_fecha    ON historial_ventas(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_hv_vend     ON historial_ventas(vendedor_id)",
        "CREATE INDEX IF NOT EXISTS idx_hv_prod     ON historial_ventas(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_inv_dia     ON inventario_diario(fecha, vendedor_id)",
        "CREATE INDEX IF NOT EXISTS idx_prod_cat    ON productos(categoria, activo)",
        "CREATE INDEX IF NOT EXISTS idx_gastos_f    ON gastos(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_login_ts    ON login_intentos(username, timestamp)",
    ]
    for idx in _indices:
        try: cursor.execute(idx)
        except Exception: pass

    # ── AUTO-EXPIRAR LOGS > 30 días ────────────────────────────
    try:
        cursor.execute("DELETE FROM logs_sistema WHERE timestamp < datetime('now','-30 days')")
    except Exception: pass

    conn.commit()

    # Migraciones seguras: añadir columnas nuevas a DBs existentes
    _migraciones = [
        ("licencias", "cliente_id",       "TEXT DEFAULT ''"),
        ("licencias", "clave_activacion", "TEXT DEFAULT ''"),
    ]
    for tabla, col, tipo_col in _migraciones:
        try:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo_col}")
            conn.commit()
        except Exception:
            pass  # Columna ya existe, ignorar

    _crear_desarrollador_default(cursor, conn)

    # Curated documentation is copied into SQLite so the developer IA can read
    # project guidance without network access. Failure must never block startup.
    try:
        from documentation_loader import sync_documentation
        sync_documentation(conn)
    except Exception as exc:
        print(f"⚠️ No se pudo sincronizar documentación offline: {exc}")

    conn.close()
    print(f"✅ Base de datos lista: {DB_FILE}")


def _crear_desarrollador_default(cursor, conn):
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    if cursor.fetchone()["total"] == 0:
        password_default = "dev2024"
        hash_pw, salt    = _hash_password(password_default)
        uid = f"user-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
            INSERT INTO usuarios
                (usuario_id, username, nombre, rol, password_hash, password_salt, creado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, "desarrollador", "Desarrollador Principal",
              "desarrollador", hash_pw, salt, "sistema"))
        conn.commit()
        print(f"✅ Desarrollador creado — usuario: desarrollador | pass: {password_default}")

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
            except Exception:
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


def crear_usuario(datos, creado_por_rol, creado_por_id):
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
def cargar_stock_masivo(admin_id, items):
    """
    Carga stock a múltiples productos del almacén general de una vez.
    items = [{ producto_id, cantidad, precio_compra }]
    Suma la cantidad al stock_actual existente (igual que registrar_entrada).
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev"}

        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok = 0
        for item in items:
            pid  = item.get("producto_id", "")
            cant = float(item.get("cantidad", 0) or 0)
            pc   = float(item.get("precio_compra", 0) or 0)
            if not pid or cant <= 0:
                continue
            # Solo actualiza stock si el producto ya existe en inventario_general
            cursor.execute("""
                UPDATE inventario_general
                SET stock_actual  = stock_actual + ?,
                    precio_compra = CASE WHEN ? > 0 THEN ? ELSE precio_compra END,
                    actualizado   = ?
                WHERE producto_id = ?
            """, (cant, pc, pc, fecha_ahora, pid))
            if cursor.rowcount > 0:
                ok += 1
        conn.commit()
        agregar_log(f"Stock masivo: {ok} productos actualizados por {admin_id}", "info")
        return {"ok": True, "actualizados": ok,
                "mensaje": f"✅ Stock cargado en {ok} productos"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def registrar_entrada_producto(datos, admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede registrar entradas"}

        producto_id   = datos.get("producto_id", "")
        nombre        = datos.get("nombre", "")
        cantidad      = float(datos.get("cantidad", 0))
        precio_compra = float(datos.get("precio_compra", 0))
        precio_venta  = float(datos.get("precio_venta",  0))
        categoria     = datos.get("categoria", "General")
        unidad_medida = datos.get("unidad_medida", "Un")
        proveedor     = datos.get("proveedor", "")
        nota          = datos.get("nota", "")

        if not producto_id or cantidad <= 0:
            return {"ok": False, "mensaje": "producto_id y cantidad > 0 son obligatorios"}

        entrada_id  = f"ent-{uuid.uuid4().hex[:8]}"
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO entradas_productos
                (entrada_id, producto_id, nombre, cantidad, precio_compra,
                 proveedor, nota, registrado_por, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entrada_id, producto_id, nombre, cantidad, precio_compra,
              proveedor, nota, admin_id, fecha_ahora))

        # Guardar precio_venta, categoria y unidad también para uso en asignación
        cursor.execute("""
            INSERT INTO inventario_general
                (producto_id, nombre, stock_actual, precio_compra, precio_venta,
                 categoria, unidad_medida, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(producto_id) DO UPDATE SET
                stock_actual  = stock_actual + excluded.stock_actual,
                precio_compra = excluded.precio_compra,
                precio_venta  = CASE WHEN excluded.precio_venta > 0
                                     THEN excluded.precio_venta
                                     ELSE inventario_general.precio_venta END,
                categoria     = CASE WHEN excluded.categoria != ''
                                     THEN excluded.categoria
                                     ELSE inventario_general.categoria END,
                unidad_medida = CASE WHEN excluded.unidad_medida != ''
                                     THEN excluded.unidad_medida
                                     ELSE inventario_general.unidad_medida END,
                actualizado   = excluded.actualizado
        """, (producto_id, nombre, cantidad, precio_compra, precio_venta,
              categoria, unidad_medida, fecha_ahora))

        conn.commit()
        agregar_log(f"Entrada: +{cantidad} '{nombre}' por {admin_id}", "info")
        return {"ok": True, "mensaje": f"+{cantidad} '{nombre}'", "entrada_id": entrada_id}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def obtener_inventario_general(admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return []
        cursor.execute("""
            SELECT ig.producto_id, ig.nombre, ig.stock_actual, ig.stock_minimo,
                   ig.precio_compra, ig.precio_venta, ig.categoria, ig.unidad_medida,
                   ig.actualizado, COALESCE(SUM(e.cantidad),0) AS total_entradas
            FROM inventario_general ig
            LEFT JOIN entradas_productos e ON ig.producto_id = e.producto_id
            GROUP BY ig.producto_id ORDER BY ig.nombre ASC
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()


def obtener_historial_entradas(admin_id, producto_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        if producto_id:
            cursor.execute("""
                SELECT e.*, u.nombre AS admin_nombre FROM entradas_productos e
                LEFT JOIN usuarios u ON e.registrado_por = u.usuario_id
                WHERE e.producto_id = ? ORDER BY e.fecha DESC
            """, (producto_id,))
        else:
            cursor.execute("""
                SELECT e.*, u.nombre AS admin_nombre FROM entradas_productos e
                LEFT JOIN usuarios u ON e.registrado_por = u.usuario_id
                ORDER BY e.fecha DESC LIMIT 100
            """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  INVENTARIO DIARIO
# ══════════════════════════════════════════════════════════════
def asignar_inventario_diario(vendedor_id, productos, admin_id):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede asignar inventario"}

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        errores   = []
        asignados = 0
        for prod in productos:
            pid  = prod.get("producto_id", "")
            cant = float(prod.get("cant_asignada", 0))
            if not pid or cant <= 0:
                continue

            cursor.execute("SELECT stock_actual FROM inventario_general WHERE producto_id = ?", (pid,))
            row = cursor.fetchone()
            stock_disp = row["stock_actual"] if row else 0

            # Si stock insuficiente, asignar lo que haya si > 0
            cant_real = cant if (stock_disp >= cant) else stock_disp
            if cant_real <= 0:
                errores.append(f"'{prod.get('nombre','?')}': sin stock (disponible: {stock_disp})")
                continue

            comision_pct = float(prod.get("comision_pct", 0))  # % comisión del admin

            cursor.execute("""
                INSERT INTO inventario_diario
                    (fecha, vendedor_id, producto_id, nombre, cant_asignada,
                     precio_venta, precio_costo, unidad_medida)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fecha, vendedor_id, producto_id) DO UPDATE SET
                    cant_asignada = cant_asignada + excluded.cant_asignada,
                    precio_venta  = excluded.precio_venta,
                    precio_costo  = excluded.precio_costo,
                    unidad_medida = excluded.unidad_medida,
                    activo = 1
            """, (fecha_hoy, vendedor_id, pid, prod.get("nombre",""), cant_real,
                  float(prod.get("precio_venta", 0)),
                  float(prod.get("precio_costo", 0)),
                  prod.get("unidad_medida", "Un")))

            cursor.execute("""
                UPDATE inventario_general
                SET stock_actual = MAX(0, stock_actual - ?), actualizado = ?
                WHERE producto_id = ?
            """, (cant_real, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pid))
            asignados += 1

        conn.commit()
        msg = f"{asignados} productos asignados"
        if errores:
            msg += f" | Sin stock: {', '.join(errores)}"
        return {"ok": asignados > 0 or not errores, "mensaje": msg, "errores": errores, "asignados": asignados}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def obtener_inventario_diario(vendedor_id, fecha=None):
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id.producto_id, id.nombre, id.cant_asignada, id.cant_vendida,
                   id.cant_final,
                   id.cant_asignada - id.cant_vendida AS cant_disponible,
                   id.precio_venta, id.precio_costo,
                   COALESCE(NULLIF(id.unidad_medida,''), ig.unidad_medida, 'Un') AS um
            FROM inventario_diario id
            LEFT JOIN inventario_general ig ON ig.producto_id = id.producto_id
            WHERE id.vendedor_id = ? AND id.fecha = ? AND id.activo = 1
            ORDER BY id.nombre ASC
        """, (vendedor_id, fecha))
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()


def actualizar_vendido_diario(vendedor_id, producto_id, cantidad_vendida):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = obtener_conexion()
    try:
        conn.execute("""
            UPDATE inventario_diario SET cant_vendida = cant_vendida + ?
            WHERE vendedor_id = ? AND producto_id = ? AND fecha = ?
        """, (cantidad_vendida, vendedor_id, producto_id, fecha_hoy))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  LIMPIAR INVENTARIOS DIARIOS
# ══════════════════════════════════════════════════════════════
def limpiar_inventarios_diarios(admin_id, vendedor_id=None, fecha=None):
    """Elimina registros de inventario_diario. Si vendedor_id=None limpia todos."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id = ? AND activo = 1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede limpiar inventarios"}
        if vendedor_id and fecha:
            cursor.execute("DELETE FROM inventario_diario WHERE vendedor_id = ? AND fecha = ?", (vendedor_id, fecha))
        elif vendedor_id:
            cursor.execute("DELETE FROM inventario_diario WHERE vendedor_id = ?", (vendedor_id,))
        elif fecha:
            cursor.execute("DELETE FROM inventario_diario WHERE fecha = ?", (fecha,))
        else:
            cursor.execute("DELETE FROM inventario_diario")
        eliminados = cursor.rowcount
        conn.commit()
        agregar_log(f"Inventarios limpiados ({eliminados} registros) por {admin_id}", "info")
        return {"ok": True, "eliminados": eliminados, "mensaje": f"{eliminados} registros eliminados"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  CATÁLOGO DE PRODUCTOS (server-side, compartido entre roles)
# ══════════════════════════════════════════════════════════════
def obtener_productos_catalogo():
    """
    Devuelve catálogo activo desde la tabla productos.
    NO hace auto-repoblación — si está vacío, devuelve lista vacía.
    """
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT producto_id AS id, nombre, precio,
                   costo AS costoUnitario, categoria,
                   unidad_medida AS um, en_oferta AS onSale, imagen
            FROM productos WHERE activo=1 ORDER BY categoria, nombre ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def sincronizar_productos_catalogo(productos, admin_id):
    """
    Sincroniza productos del cliente → servidor.
    Actualiza tabla productos e inventario_general simultáneamente.
    El stock_actual del almacén NUNCA se modifica.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador","desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede sincronizar catálogo"}
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in productos:
            pid  = p.get("id","");
            if not pid: continue
            nom  = p.get("nombre","")
            pv   = float(p.get("precio",0))
            pc   = float(p.get("costoUnitario",0))
            cat  = p.get("categoria","General") or "General"
            um   = p.get("um","C/U") or "C/U"
            oferta = 1 if p.get("onSale") else 0
            img  = p.get("imagen","")
            # tabla productos
            cursor.execute("""
                INSERT INTO productos
                    (producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,imagen,activo)
                VALUES (?,?,?,?,?,?,?,?,1)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre=excluded.nombre, precio=excluded.precio, costo=excluded.costo,
                    categoria=excluded.categoria, unidad_medida=excluded.unidad_medida,
                    en_oferta=excluded.en_oferta, imagen=excluded.imagen, activo=1
            """, (pid,nom,pv,pc,cat,um,oferta,img))
            # inventario_general: actualiza metadatos, NUNCA stock
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id,nombre,stock_actual,stock_minimo,
                     precio_compra,precio_venta,categoria,unidad_medida,actualizado)
                VALUES (?,?,0,5,?,?,?,?,?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra>0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (pid,nom,pc,pv,cat,um,ahora))
        ids = [p.get("id","") for p in productos if p.get("id","")]
        if ids:
            ph = ",".join("?"*len(ids))
            cursor.execute(f"UPDATE productos SET activo=0 WHERE producto_id NOT IN ({ph})",ids)
        conn.commit()
        return {"ok": True, "sincronizados": len(productos)}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def importar_catalogo_a_inventario(admin_id):
    """Catálogo → inventario_general. Nuevos: stock 0. Existentes: conserva stock."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1",(admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador","desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev"}
        cursor.execute("SELECT producto_id,nombre,precio,costo,categoria,unidad_medida FROM productos WHERE activo=1")
        prods = cursor.fetchall()
        if not prods:
            return {"ok": False, "mensaje": "Catálogo vacío"}
        ahora   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevos  = existentes = 0
        for p in prods:
            cursor.execute("""
                INSERT OR IGNORE INTO inventario_general
                    (producto_id,nombre,stock_actual,stock_minimo,
                     precio_compra,precio_venta,categoria,unidad_medida,actualizado)
                VALUES (?,?,0,5,?,?,?,?,?)
            """, (p["producto_id"],p["nombre"],
                  float(p["costo"] or 0), float(p["precio"] or 0),
                  p["categoria"] or "General", p["unidad_medida"] or "C/U", ahora))
            if cursor.rowcount > 0:
                nuevos += 1
            else:
                cursor.execute("""
                    UPDATE inventario_general SET
                        nombre=?, precio_venta=?,
                        precio_compra=CASE WHEN ?> 0 THEN ? ELSE precio_compra END,
                        categoria=?, unidad_medida=?, actualizado=?
                    WHERE producto_id=?
                """, (p["nombre"], float(p["precio"] or 0),
                      float(p["costo"] or 0), float(p["costo"] or 0),
                      p["categoria"] or "General", p["unidad_medida"] or "C/U",
                      ahora, p["producto_id"]))
                existentes += 1
        conn.commit()
        agregar_log(f"Import catálogo→almacén: {nuevos} nuevos, {existentes} actualizados", "info")
        return {"ok":True,"nuevos":nuevos,"existentes":existentes,"total":len(prods),
                "mensaje":f"{nuevos} nuevos · {existentes} actualizados (stock conservado)"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def eliminar_producto_inventario_general(producto_id, admin_id):
    """Borra producto del almacén y lo desactiva en catálogo."""
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM inventario_general WHERE producto_id=?", (producto_id,))
        conn.execute("UPDATE productos SET activo=0 WHERE producto_id=?", (producto_id,))
        conn.commit()
        agregar_log(f"Producto {producto_id} eliminado del almacén", "warning")
        return {"ok": True, "mensaje": "Eliminado"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()



# ══════════════════════════════════════════════════════════════
#  SINCRONIZACIÓN COMPLETA — une productos ↔ inventario_general
# ══════════════════════════════════════════════════════════════
def sincronizar_estado_completo(admin_id):
    """
    Sincronización en cascada:
      1. productos  →  inventario_general  (metadatos, nunca stock)
      2. inventario_general  →  productos  (productos huérfanos del almacén)
    Devuelve resumen de lo sincronizado.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede sincronizar"}

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. productos → inventario_general
        cursor.execute("SELECT * FROM productos WHERE activo=1")
        prods = cursor.fetchall()
        sync_p2i = 0
        for p in prods:
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id, nombre, stock_actual, stock_minimo,
                     precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                VALUES (?, ?, 0, 5, ?, ?, ?, ?, ?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra > 0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (p["producto_id"], p["nombre"],
                  float(p["costo"] or 0), float(p["precio"] or 0),
                  p["categoria"] or "General", p["unidad_medida"] or "C/U", ahora))
            sync_p2i += 1

        # 2. inventario_general → productos (huérfanos)
        cursor.execute("""
            SELECT * FROM inventario_general
            WHERE producto_id NOT IN (SELECT producto_id FROM productos WHERE activo=1)
        """)
        huerfanos = cursor.fetchall()
        sync_i2p = 0
        for ig in huerfanos:
            cursor.execute("""
                INSERT OR IGNORE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen, activo)
                VALUES (?, ?, ?, ?, ?, ?, 0, '', 1)
            """, (ig["producto_id"], ig["nombre"],
                  float(ig["precio_venta"] or 0), float(ig["precio_compra"] or 0),
                  ig["categoria"] or "General", ig["unidad_medida"] or "C/U"))
            sync_i2p += 1

        conn.commit()
        agregar_log(
            f"Sync completo: {sync_p2i} productos→almacén, {sync_i2p} huérfanos recuperados",
            "info"
        )
        return {
            "ok": True,
            "productos_a_almacen": sync_p2i,
            "huerfanos_recuperados": sync_i2p,
            "mensaje": f"✅ {sync_p2i} productos sincronizados al almacén · {sync_i2p} huérfanos recuperados"
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def limpiar_tablas_completo(admin_id):
    """
    Borrado total y real en todos los almacenes del servidor:
      - productos
      - inventario_general
      - entradas_productos
      - inventario_diario
      - inventarios
      - app_state  (estado JSON del cliente)
    NO toca: usuarios, licencias, cierres_caja, gastos, historial_ventas, logs.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev"}

        tablas = [
            "productos",
            "inventario_general",
            "entradas_productos",
            "inventario_diario",
            "inventarios",
        ]
        conteos = {}
        for t in tablas:
            cursor.execute(f"DELETE FROM {t}")
            conteos[t] = cursor.rowcount

        # Borrar el estado JSON guardado
        cursor.execute("DELETE FROM app_state WHERE clave='estado_tpv'")
        conn.commit()

        resumen = " · ".join(f"{t}: {n}" for t, n in conteos.items())
        agregar_log(f"Limpieza completa por {admin_id}: {resumen}", "warning")
        return {
            "ok":      True,
            "conteos": conteos,
            "mensaje": f"🗑️ Limpieza completa: {resumen}"
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


def reconstruir_desde_productos(admin_id, productos_js):
    """
    Recibe la lista de productos del cliente (JS) y reconstruye
    productos + inventario_general desde cero.
    Acepta campo opcional 'stock_actual' en cada producto para
    poblar el almacén con el stock real del Excel importado.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=? AND activo=1", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador"):
            return {"ok": False, "mensaje": "Solo Admin/Dev"}

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = 0
        for p in productos_js:
            pid = p.get("id", "")
            if not pid: continue
            nom    = p.get("nombre", "")
            pv     = float(p.get("precio", 0) or 0)
            pc     = float(p.get("costoUnitario", p.get("costo", 0)) or 0)
            cat    = p.get("categoria", "General") or "General"
            um     = p.get("um", p.get("unidadMedida", "C/U")) or "C/U"
            oferta = 1 if p.get("onSale", p.get("enOferta", False)) else 0
            img    = p.get("imagen", "")
            # Stock real del XLSX si viene; si no, conservar el existente o 0
            stock  = p.get("stock_actual", None)

            cursor.execute("""
                INSERT OR REPLACE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen, activo)
                VALUES (?,?,?,?,?,?,?,?,1)
            """, (pid, nom, pv, pc, cat, um, oferta, img))

            if stock is not None:
                # Stock explícito enviado desde el cliente (viene del XLSX)
                cursor.execute("""
                    INSERT OR REPLACE INTO inventario_general
                        (producto_id, nombre, stock_actual, stock_minimo,
                         precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                    VALUES (?,?,?,5,?,?,?,?,?)
                """, (pid, nom, float(stock), pc, pv, cat, um, ahora))
            else:
                # Sin stock explícito: insertar con 0, o actualizar solo metadatos si ya existe
                cursor.execute("""
                    INSERT INTO inventario_general
                        (producto_id, nombre, stock_actual, stock_minimo,
                         precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                    VALUES (?,?,0,5,?,?,?,?,?)
                    ON CONFLICT(producto_id) DO UPDATE SET
                        nombre        = excluded.nombre,
                        precio_venta  = excluded.precio_venta,
                        precio_compra = CASE WHEN excluded.precio_compra > 0
                                        THEN excluded.precio_compra
                                        ELSE inventario_general.precio_compra END,
                        categoria     = excluded.categoria,
                        unidad_medida = excluded.unidad_medida,
                        actualizado   = excluded.actualizado
                """, (pid, nom, pc, pv, cat, um, ahora))
            total += 1

        conn.commit()
        agregar_log(f"Reconstrucción: {total} productos desde cliente", "info")
        return {"ok": True, "total": total,
                "mensaje": f"✅ {total} productos reconstruidos en servidor"}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
#  ESTADO JSON
# ══════════════════════════════════════════════════════════════
def cargar_estado():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM app_state WHERE clave = ?", ("estado_tpv",))
        fila = cursor.fetchone()
        return json.loads(fila["valor"]) if fila else None
    except Exception as e:
        print(f"❌ Error cargar estado: {e}")
        return None
    finally:
        conn.close()


def guardar_estado(estado):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        valor_json = json.dumps(estado, ensure_ascii=False)
        ahora      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT OR REPLACE INTO app_state (clave, valor, actualizado) VALUES (?, ?, ?)
        """, ("estado_tpv", valor_json, ahora))
        conn.commit()
        _sincronizar_tablas_relacionales(cursor, conn, estado)
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error guardar estado: {e}")
        return False
    finally:
        conn.close()


def _sincronizar_tablas_relacionales(cursor, conn, estado):
    for venta in estado.get("historialVentas", []):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO historial_ventas
                    (venta_id, producto_id, nombre, cantidad, precio_unit,
                     total, metodo_pago, vendedor_id, vendedor_nombre, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (venta.get("id",""), venta.get("productoId",""), venta.get("nombre",""),
                  venta.get("cantidad",1), venta.get("precio",0), venta.get("total",0),
                  venta.get("metodoPago","efectivo"), venta.get("vendedorId",None),
                  venta.get("vendedorNombre",None),
                  venta.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
        except sqlite3.Error:
            pass

    for p in estado.get("productos", []):
        try:
            pid  = p.get("id","")
            nom  = p.get("nombre","")
            pv   = float(p.get("precio", 0) or 0)
            pc   = float(p.get("costoUnitario", p.get("costo", 0)) or 0)
            cat  = p.get("categoria","General") or "General"
            um   = p.get("um", p.get("unidadMedida","C/U")) or "C/U"
            oferta = 1 if p.get("onSale", p.get("enOferta", False)) else 0
            img  = p.get("imagen","")
            if not pid: continue
            cursor.execute("""
                INSERT OR REPLACE INTO productos
                    (producto_id, nombre, precio, costo, categoria,
                     unidad_medida, en_oferta, imagen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, nom, pv, pc, cat, um, oferta, img))
            # Mantener inventario_general sincronizado (solo metadatos, nunca stock)
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO inventario_general
                    (producto_id, nombre, stock_actual, stock_minimo,
                     precio_compra, precio_venta, categoria, unidad_medida, actualizado)
                VALUES (?, ?, 0, 5, ?, ?, ?, ?, ?)
                ON CONFLICT(producto_id) DO UPDATE SET
                    nombre        = excluded.nombre,
                    precio_venta  = excluded.precio_venta,
                    precio_compra = CASE WHEN excluded.precio_compra > 0
                                    THEN excluded.precio_compra
                                    ELSE inventario_general.precio_compra END,
                    categoria     = excluded.categoria,
                    unidad_medida = excluded.unidad_medida,
                    actualizado   = excluded.actualizado
            """, (pid, nom, pc, pv, cat, um, ahora))
        except sqlite3.Error:
            pass

    for c in estado.get("cierresCaja", []):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO cierres_caja
                    (fecha, total_ventas, total_costos, total_comisiones, ganancia_total)
                VALUES (?, ?, ?, ?, ?)
            """, (c.get("fecha","")[:10], c.get("totalVentas",0), c.get("totalCostos",0),
                  c.get("totalComisiones",0), c.get("gananciaTotal",0)))
        except sqlite3.Error:
            pass
    conn.commit()

# ══════════════════════════════════════════════════════════════
#  CONSULTAS REPORTES
# ══════════════════════════════════════════════════════════════
def consultar_ventas_por_fecha(fecha_inicio, fecha_fin, vendedor_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        if vendedor_id:
            cursor.execute("""
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? AND vendedor_id = ?
                ORDER BY fecha DESC
            """, (fecha_inicio, fecha_fin + " 23:59:59", vendedor_id))
        else:
            cursor.execute("""
                SELECT venta_id, nombre AS producto, cantidad,
                       precio_unit AS precio_unitario, total,
                       metodo_pago, vendedor_nombre, fecha
                FROM historial_ventas
                WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC
            """, (fecha_inicio, fecha_fin + " 23:59:59"))
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()


def consultar_resumen_ventas(vendedor_id=None):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        filtro = "WHERE vendedor_id = ?" if vendedor_id else ""
        params = (vendedor_id,) if vendedor_id else ()
        cursor.execute(f"""
            SELECT COUNT(*) AS num_ventas, SUM(total) AS total_ingresos,
                   AVG(total) AS promedio_venta, MAX(total) AS venta_maxima,
                   MIN(total) AS venta_minima, SUM(cantidad) AS unidades_vendidas
            FROM historial_ventas {filtro}
        """, params)
        totales = dict(cursor.fetchone())
        cursor.execute(f"""
            SELECT nombre AS producto, SUM(cantidad) AS total_unidades,
                   SUM(total) AS total_ingresos, COUNT(*) AS num_transacciones
            FROM historial_ventas {filtro}
            GROUP BY nombre ORDER BY total_unidades DESC LIMIT 5
        """, params)
        top = [dict(f) for f in cursor.fetchall()]
        cursor.execute(f"""
            SELECT metodo_pago, COUNT(*) AS num_ventas, SUM(total) AS total
            FROM historial_ventas {filtro}
            GROUP BY metodo_pago ORDER BY total DESC
        """, params)
        por_metodo = [dict(f) for f in cursor.fetchall()]
        return {"totales": totales, "top_productos": top, "por_metodo_pago": por_metodo}
    finally:
        conn.close()


def consultar_inventario_actual():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT producto_id AS id, nombre, precio, costo, categoria,
                   unidad_medida, CASE WHEN en_oferta=1 THEN 'Sí' ELSE 'No' END AS en_oferta
            FROM productos WHERE activo = 1 ORDER BY categoria, nombre ASC
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()


def consultar_ganancias_por_dia():
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DATE(fecha) AS dia, COUNT(*) AS num_ventas,
                   SUM(cantidad) AS unidades_vendidas, SUM(total) AS total_ingresos
            FROM historial_ventas GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 30
        """)
        return [dict(f) for f in cursor.fetchall()]
    finally:
        conn.close()



# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO LOCAL
# ══════════════════════════════════════════════════════════════
def guardar_historial_diario_local(snapshot: dict) -> bool:
    """Guarda un snapshot diario en SQLite historial_diario."""
    conn = obtener_conexion()
    try:
        fecha = snapshot.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        conn.execute("""
            INSERT INTO historial_diario
                (fecha, total_ventas, num_transacciones, productos_activos,
                 inventario_items, ventas_data, inventario_data, config_snapshot, ts_guardado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                total_ventas      = excluded.total_ventas,
                num_transacciones = excluded.num_transacciones,
                productos_activos = excluded.productos_activos,
                inventario_items  = excluded.inventario_items,
                ventas_data       = excluded.ventas_data,
                inventario_data   = excluded.inventario_data,
                config_snapshot   = excluded.config_snapshot,
                ts_guardado       = excluded.ts_guardado
        """, (
            fecha,
            float(snapshot.get("total_ventas", 0)),
            int(snapshot.get("num_transacciones", 0)),
            int(snapshot.get("productos_activos", 0)),
            int(snapshot.get("inventario_items", 0)),
            json.dumps(snapshot.get("ventas_data", []), ensure_ascii=False),
            json.dumps(snapshot.get("inventario_data", []), ensure_ascii=False),
            json.dumps(snapshot.get("config_snapshot", {}), ensure_ascii=False),
            snapshot.get("ts_guardado", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error guardando historial local: {e}")
        return False
    finally:
        conn.close()


def obtener_historial_diario_local(limite=30) -> list:
    """Devuelve los últimos N días del historial local."""
    conn = obtener_conexion()
    try:
        rows = conn.execute("""
            SELECT fecha, total_ventas, num_transacciones,
                   productos_activos, inventario_items, ts_guardado
            FROM historial_diario
            ORDER BY fecha DESC LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def obtener_historial_detalle_local(fecha: str) -> dict:
    """Devuelve el detalle completo de un día."""
    conn = obtener_conexion()
    try:
        row = conn.execute("SELECT * FROM historial_diario WHERE fecha=?", (fecha,)).fetchone()
        if not row: return {}
        d = dict(row)
        d["ventas_data"]    = json.loads(d.get("ventas_data",    "[]"))
        d["inventario_data"]= json.loads(d.get("inventario_data","[]"))
        d["config_snapshot"]= json.loads(d.get("config_snapshot","{}"))
        return d
    finally:
        conn.close()


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
