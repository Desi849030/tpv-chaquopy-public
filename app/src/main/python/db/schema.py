from __future__ import annotations
from db.indexes import crear_indices
# -*- coding: utf-8 -*-
"""db/schema.py - Tablas TPV Smart.

Integridad referencial (#18):
- Se declaran FOREIGN KEYS en las tablas operativas (inventarios, entradas,
  cierres, licencias) hacia productos(producto_id) y usuarios(usuario_id).
- Las tablas de auditoría/historial (historial_ventas, ventas_cabecera,
  ventas_detalle, auditoria, logs_sistema, login_intentos) NO llevan FK dura
  hacia productos/usuarios: deben conservar el registro aunque el producto o
  usuario origen se elimine (y aceptan vendedores externos).
- ventas_detalle sí referencia a ventas_cabecera(venta_id) para asegurar que
  no existan detalles huérfanos.
- db_connection.obtener_conexion() ya ejecuta PRAGMA foreign_keys = ON.
- Nota: CREATE TABLE IF NOT EXISTS no altera tablas ya creadas; las FK
  aplican a bases de datos nuevas (las existentes siguen funcionando igual).
"""

APP_STATE = """CREATE TABLE IF NOT EXISTS app_state (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            clave       TEXT    NOT NULL UNIQUE,
            valor       TEXT    NOT NULL,
            actualizado TEXT    DEFAULT (datetime('now','localtime'))
        )"""

USUARIOS = """CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id    TEXT    NOT NULL UNIQUE,
            username      TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            rol           TEXT    NOT NULL CHECK(rol IN
                          ('desarrollador','administrador','supervisor','vendedor','cajero')),
            password_hash TEXT    NOT NULL,
            password_salt TEXT    NOT NULL,
            creado_por    TEXT    DEFAULT NULL,
            activo        INTEGER DEFAULT 1,
            ultimo_acceso TEXT    DEFAULT NULL,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )"""

LICENCIAS = """CREATE TABLE IF NOT EXISTS licencias (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            licencia_id   TEXT    NOT NULL UNIQUE,
            admin_id      TEXT    NOT NULL
                          REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
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
        )"""


VENTAS_CABECERA = """CREATE TABLE IF NOT EXISTS ventas_cabecera (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id        TEXT    NOT NULL UNIQUE,
            client_txn_id   TEXT    NOT NULL UNIQUE,
            vendedor_id     TEXT    DEFAULT NULL,
            vendedor_nombre TEXT    DEFAULT NULL,
            metodo_pago     TEXT    NOT NULL DEFAULT 'efectivo',
            total           REAL    NOT NULL DEFAULT 0,
            estado          TEXT    NOT NULL DEFAULT 'confirmada'
                          CHECK(estado IN ('procesando','confirmada','cancelada')),
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )"""

VENTAS_DETALLE = """CREATE TABLE IF NOT EXISTS ventas_detalle (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id      TEXT    NOT NULL
                          REFERENCES ventas_cabecera(venta_id) ON DELETE CASCADE,
            producto_id   TEXT    NOT NULL,
            nombre        TEXT    NOT NULL,
            cantidad      REAL    NOT NULL DEFAULT 1,
            precio_unit   REAL    NOT NULL DEFAULT 0,
            subtotal      REAL    NOT NULL DEFAULT 0
        )"""

HISTORIAL_VENTAS = """CREATE TABLE IF NOT EXISTS historial_ventas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id        TEXT    NOT NULL,
            producto_id     TEXT    NOT NULL,
            nombre          TEXT    NOT NULL,
            cantidad        REAL    NOT NULL DEFAULT 1,
            precio_unit     REAL    NOT NULL DEFAULT 0,
            total           REAL    NOT NULL DEFAULT 0,
            metodo_pago     TEXT    DEFAULT 'efectivo',
            -- Sin FK dura: el historial conserva ventas de vendedores
            -- eliminados o externos ('desconocido'); ver docstring (#18)
            vendedor_id     TEXT    DEFAULT NULL,
            vendedor_nombre TEXT    DEFAULT NULL,
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )"""

PRODUCTOS = """CREATE TABLE IF NOT EXISTS productos (
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
        )"""

INVENTARIO_GENERAL = """CREATE TABLE IF NOT EXISTS inventario_general (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id   TEXT    NOT NULL UNIQUE
                          REFERENCES productos(producto_id) ON DELETE CASCADE,
            nombre        TEXT    NOT NULL,
            stock_actual  REAL    NOT NULL DEFAULT 0,
            stock_minimo  REAL    DEFAULT 5,
            precio_compra REAL    DEFAULT 0,
            precio_venta  REAL    DEFAULT 0,
            categoria     TEXT    DEFAULT 'General',
            unidad_medida TEXT    DEFAULT 'C/U',
            actualizado   TEXT    DEFAULT (datetime('now','localtime'))
        )"""

ENTRADAS_PRODUCTOS = """CREATE TABLE IF NOT EXISTS entradas_productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            entrada_id    TEXT    NOT NULL UNIQUE,
            producto_id   TEXT    NOT NULL
                          REFERENCES productos(producto_id) ON DELETE CASCADE,
            nombre        TEXT    NOT NULL,
            cantidad      REAL    NOT NULL DEFAULT 0,
            precio_compra REAL    DEFAULT 0,
            proveedor     TEXT    DEFAULT '',
            nota          TEXT    DEFAULT '',
            registrado_por TEXT   NOT NULL,
            fecha         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )"""

INVENTARIO_DIARIO = """CREATE TABLE IF NOT EXISTS inventario_diario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha         TEXT    NOT NULL,
            vendedor_id   TEXT    NOT NULL
                          REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
            producto_id   TEXT    NOT NULL
                          REFERENCES productos(producto_id) ON DELETE CASCADE,
            nombre        TEXT    NOT NULL,
            cant_asignada REAL    NOT NULL DEFAULT 0,
            cant_vendida  REAL    DEFAULT 0,
            cant_devuelta REAL    DEFAULT 0,
            cant_final    REAL    DEFAULT 0,
            precio_venta  REAL    DEFAULT 0,
            precio_costo  REAL    DEFAULT 0,
            activo        INTEGER DEFAULT 1,
            UNIQUE(fecha, vendedor_id, producto_id)
        )"""

CIERRES_DIARIO = """CREATE TABLE IF NOT EXISTS cierres_diario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id   TEXT    NOT NULL
                          REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
            fecha         TEXT    NOT NULL,
            total_ventas  REAL    DEFAULT 0,
            total_costo   REAL    DEFAULT 0,
            ganancia_neta REAL    DEFAULT 0,
            items_json    TEXT    DEFAULT '[]',
            creado_en     TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(vendedor_id, fecha)
        )"""

GASTOS = """CREATE TABLE IF NOT EXISTS gastos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            gasto_id     TEXT    NOT NULL UNIQUE,
            descripcion  TEXT    NOT NULL,
            monto        REAL    NOT NULL DEFAULT 0,
            categoria    TEXT    DEFAULT 'Otros',
            fecha        TEXT    NOT NULL,
            nota         TEXT    DEFAULT '',
            registrado_por TEXT  DEFAULT '',
            creado_en    TEXT    DEFAULT (datetime('now','localtime'))
        )"""

CIERRES_CAJA = """CREATE TABLE IF NOT EXISTS cierres_caja (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha             TEXT    NOT NULL UNIQUE,
            total_ventas      REAL    DEFAULT 0,
            total_costos      REAL    DEFAULT 0,
            total_comisiones  REAL    DEFAULT 0,
            ganancia_total    REAL    DEFAULT 0,
            num_transacciones INTEGER DEFAULT 0,
            efectivo          REAL    DEFAULT 0,
            tarjeta           REAL    DEFAULT 0,
            transferencia     REAL    DEFAULT 0,
            cerrado_por       TEXT    DEFAULT NULL,
            creado            TEXT    DEFAULT (datetime('now','localtime'))
        )"""

INVENTARIOS = """CREATE TABLE IF NOT EXISTS inventarios (
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
        )"""

LOGS_SISTEMA = """CREATE TABLE IF NOT EXISTS logs_sistema (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo      TEXT    DEFAULT 'info',
            usuario   TEXT    DEFAULT NULL,
            mensaje   TEXT    NOT NULL,
            timestamp TEXT    DEFAULT (datetime('now','localtime'))
        )"""

LOGIN_INTENTOS = """CREATE TABLE IF NOT EXISTS login_intentos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL,
            ip         TEXT    DEFAULT '',
            exito      INTEGER DEFAULT 0,
            timestamp  TEXT    DEFAULT (datetime('now','localtime'))
        )"""

AUDITORIA = """CREATE TABLE IF NOT EXISTS auditoria (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla       TEXT    NOT NULL,
            accion      TEXT    NOT NULL,
            registro_id TEXT    NOT NULL,
            campo       TEXT    DEFAULT '',
            valor_antes TEXT    DEFAULT '',
            valor_nuevo TEXT    DEFAULT '',
            usuario_id  TEXT    NOT NULL,
            timestamp   TEXT    DEFAULT (datetime('now','localtime'))
        )"""

DESCUENTOS_CONFIG = """CREATE TABLE IF NOT EXISTS descuentos_config (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL DEFAULT 'Descuento',
            tipo        TEXT    NOT NULL DEFAULT 'porcentaje'
                        CHECK(tipo IN ('porcentaje','fijo')),
            valor       REAL    NOT NULL DEFAULT 0,
            activo      INTEGER DEFAULT 1,
            creado      TEXT    DEFAULT (datetime('now','localtime'))
        )"""

HISTORIAL_DIARIO = """CREATE TABLE IF NOT EXISTS historial_diario (
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
        )"""
















CLIENTES = """CREATE TABLE IF NOT EXISTS clientes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id    TEXT    NOT NULL UNIQUE,
            nombre        TEXT    NOT NULL,
            telefono      TEXT    DEFAULT '',
            email         TEXT    DEFAULT '',
            puntos        INTEGER DEFAULT 0,
            nivel         TEXT    DEFAULT 'bronce',
            notas         TEXT    DEFAULT '',
            activo        INTEGER DEFAULT 1,
            creado        TEXT    DEFAULT (datetime('now','localtime'))
        )"""

ALL_TABLES = [
    APP_STATE,
    USUARIOS,
    LICENCIAS,
    VENTAS_CABECERA,
    VENTAS_DETALLE,
    HISTORIAL_VENTAS,
    PRODUCTOS,
    INVENTARIO_GENERAL,
    ENTRADAS_PRODUCTOS,
    INVENTARIO_DIARIO,
    CIERRES_DIARIO,
    GASTOS,
    CIERRES_CAJA,
    INVENTARIOS,
    LOGS_SISTEMA,
    LOGIN_INTENTOS,
    AUDITORIA,
    DESCUENTOS_CONFIG,
    HISTORIAL_DIARIO,
    CLIENTES,
]

def crear_tablas_schema(conn):
    """Ejecuta todas las CREATE TABLE IF NOT EXISTS."""
    cur = conn.cursor()
    for sql in ALL_TABLES:
        try:
            cur.execute(sql)
        except Exception:  # noqa: broad-except - graceful degradation
            pass
    crear_indices(conn)
