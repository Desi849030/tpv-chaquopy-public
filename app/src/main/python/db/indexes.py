"""
db/indexes.py - Indices de rendimiento para tpv_datos.db
v3 fortalecida: 35 indices (simples + compuestos) + ANALYZE
Tablas: historial_ventas, productos, inventario_general, gastos,
        cierres_diario, auditoria, entradas_productos,
        inventario_diario, login_intentos
"""

import logging
_log = logging.getLogger("db.indexes")

# Definicion de los 35 indices
_INDEXES = [
    # ── historial_ventas (6) ──────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_hv_fecha          ON historial_ventas(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_hv_producto       ON historial_ventas(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_hv_vendedor       ON historial_ventas(vendedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_hv_metodo_pago    ON historial_ventas(metodo_pago)",
    "CREATE INDEX IF NOT EXISTS idx_hv_total          ON historial_ventas(total)",
    "CREATE INDEX IF NOT EXISTS idx_hv_vendedor_nombre ON historial_ventas(vendedor_id, nombre)",

    # ── productos (5) ─────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_prod_codigo       ON productos(codigo_barras)",
    "CREATE INDEX IF NOT EXISTS idx_prod_nombre       ON productos(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_prod_categoria    ON productos(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_prod_activo       ON productos(activo)",
    "CREATE INDEX IF NOT EXISTS idx_prod_cat_activo   ON productos(categoria, activo)",

    # ── inventario_general (6) ────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_inv_nombre        ON inventario_general(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_inv_categoria     ON inventario_general(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_inv_stock         ON inventario_general(stock_actual)",
    "CREATE INDEX IF NOT EXISTS idx_inv_precio_venta  ON inventario_general(precio_venta)",
    "CREATE INDEX IF NOT EXISTS idx_inv_precio_compra ON inventario_general(precio_compra)",
    "CREATE INDEX IF NOT EXISTS idx_inv_cat_stock     ON inventario_general(categoria, stock_actual)",

    # ── gastos (4) ────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_gasto_fecha       ON gastos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_categoria   ON gastos(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_monto       ON gastos(monto)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_fecha_cat   ON gastos(fecha, categoria)",

    # ── cierres_diario (3) ────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_cierre_fecha      ON cierres_diario(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_cierre_vendedor   ON cierres_diario(vendedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_cierre_vend_fecha ON cierres_diario(vendedor_id, fecha)",

    # ── auditoria (4) ─────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_audit_tabla       ON auditoria(tabla)",
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp   ON auditoria(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_audit_usuario     ON auditoria(usuario)",
    "CREATE INDEX IF NOT EXISTS idx_audit_tabla_ts    ON auditoria(tabla, timestamp)",

    # ── entradas_productos (2) ────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_ep_fecha          ON entradas_productos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_ep_producto       ON entradas_productos(producto_id)",

    # ── inventario_diario (2) ─────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_id_fecha          ON inventario_diario(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_id_producto       ON inventario_diario(producto_id)",

    # ── login_intentos (3) ────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_li_usuario        ON login_intentos(usuario)",
    "CREATE INDEX IF NOT EXISTS idx_li_fecha          ON login_intentos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_li_exito          ON login_intentos(exito)",
]


def crear_indices(conn):
    """Crea todos los indices de rendimiento en la BD.

    Args:
        conn: Conexion sqlite3 abierta.

    Returns:
        tuple (creados, total, errores) donde errores es lista de strings.
    """
    created = 0
    errors = []
    for sql in _INDEXES:
        try:
            conn.execute(sql)
            created += 1
        except Exception as e:
            name = sql.split("idx_")[1].split(" ")[0] if "idx_" in sql else "?"
            errors.append("{}: {}".format(name, e))
    # ANALYZE para actualizar estadisticas del query planner
    try:
        conn.execute("ANALYZE")
    except Exception as e:
        _log.debug("ANALYZE error: %s", e)
    conn.commit()
    if errors:
        _log.warning("[crear_indices] %d/%d OK, errores: %s",
                      created - len(errors), len(_INDEXES), errors)
    else:
        _log.info("[crear_indices] %d/%d indices creados OK",
                   created, len(_INDEXES))
    return created, len(_INDEXES), errors
