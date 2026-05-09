"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""
from __future__ import annotations
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE
from db_users import _crear_desarrollador_default

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
    conn.close()
    print(f"✅ Base de datos lista: {DB_FILE}")



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
# === INVENTARIO GENERAL ===

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
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Solo Admin/Dev puede sincronizar"}

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. productos → inventario_general
        cursor.execute("SELECT * FROM productos")
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
            WHERE producto_id NOT IN (SELECT producto_id FROM productos)
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
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}

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
    agregar_log(f"[v25] reconstruir: admin={admin_id}, n={len(productos_js)}", "info")
    """
    Recibe la lista de productos del cliente (JS) y reconstruye
    productos + inventario_general desde cero.
    Acepta campo opcional 'stock_actual' en cada producto para
    poblar el almacén con el stock real del Excel importado.
    """
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos. Rol: " + str(u["rol"])}

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
# === ESTADO Y SINCRONIZACION ===

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
# === CONSULTAS DE VENTAS ===

