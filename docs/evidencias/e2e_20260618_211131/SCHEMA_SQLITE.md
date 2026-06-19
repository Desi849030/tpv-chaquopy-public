# Esquema SQLite detectado

## Base: `/data/data/com.termux/files/home/tpv-trabajo/tpv_datos.db`

### `app_state`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `clave` | `TEXT` | 1 | `None` | 0 |
| 2 | `valor` | `TEXT` | 1 | `None` | 0 |
| 3 | `actualizado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `audit_logs`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `timestamp` | `DATETIME` | 0 | `CURRENT_TIMESTAMP` | 0 |
| 2 | `usuario_id` | `TEXT` | 0 | `None` | 0 |
| 3 | `accion` | `TEXT` | 0 | `None` | 0 |
| 4 | `detalles` | `TEXT` | 0 | `None` | 0 |
| 5 | `ip` | `TEXT` | 0 | `None` | 0 |

> Observación: `audit_logs` no contiene columna `usuario`.

### `auditoria`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `tabla` | `TEXT` | 1 | `None` | 0 |
| 2 | `accion` | `TEXT` | 1 | `None` | 0 |
| 3 | `registro_id` | `TEXT` | 1 | `None` | 0 |
| 4 | `campo` | `TEXT` | 0 | `''` | 0 |
| 5 | `valor_antes` | `TEXT` | 0 | `''` | 0 |
| 6 | `valor_nuevo` | `TEXT` | 0 | `''` | 0 |
| 7 | `usuario_id` | `TEXT` | 1 | `None` | 0 |
| 8 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `bio_tokens`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `token_hash` | `TEXT` | 1 | `None` | 0 |
| 2 | `usuario_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `device` | `TEXT` | 0 | `''` | 0 |
| 4 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 5 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 6 | `ultimo_uso` | `TEXT` | 0 | `NULL` | 0 |

### `cierres_caja`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 3 | `total_costos` | `REAL` | 0 | `0` | 0 |
| 4 | `total_comisiones` | `REAL` | 0 | `0` | 0 |
| 5 | `ganancia_total` | `REAL` | 0 | `0` | 0 |
| 6 | `num_transacciones` | `INTEGER` | 0 | `0` | 0 |
| 7 | `efectivo` | `REAL` | 0 | `0` | 0 |
| 8 | `tarjeta` | `REAL` | 0 | `0` | 0 |
| 9 | `transferencia` | `REAL` | 0 | `0` | 0 |
| 10 | `cerrado_por` | `TEXT` | 0 | `NULL` | 0 |
| 11 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `cierres_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `vendedor_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 3 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 4 | `total_costo` | `REAL` | 0 | `0` | 0 |
| 5 | `ganancia_neta` | `REAL` | 0 | `0` | 0 |
| 6 | `items_json` | `TEXT` | 0 | `'[]'` | 0 |
| 7 | `creado_en` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `clientes`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `cliente_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `telefono` | `TEXT` | 0 | `''` | 0 |
| 4 | `email` | `TEXT` | 0 | `''` | 0 |
| 5 | `puntos` | `INTEGER` | 0 | `0` | 0 |
| 6 | `nivel` | `TEXT` | 0 | `'bronce'` | 0 |
| 7 | `notas` | `TEXT` | 0 | `''` | 0 |
| 8 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 9 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `descuentos_config`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `nombre` | `TEXT` | 1 | `'Descuento'` | 0 |
| 2 | `tipo` | `TEXT` | 1 | `'porcentaje'` | 0 |
| 3 | `valor` | `REAL` | 1 | `0` | 0 |
| 4 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 5 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `entradas_productos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `entrada_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `0` | 0 |
| 5 | `precio_compra` | `REAL` | 0 | `0` | 0 |
| 6 | `proveedor` | `TEXT` | 0 | `''` | 0 |
| 7 | `nota` | `TEXT` | 0 | `''` | 0 |
| 8 | `registrado_por` | `TEXT` | 1 | `None` | 0 |
| 9 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `gastos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `gasto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `descripcion` | `TEXT` | 1 | `None` | 0 |
| 3 | `monto` | `REAL` | 1 | `0` | 0 |
| 4 | `categoria` | `TEXT` | 0 | `'Otros'` | 0 |
| 5 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 6 | `nota` | `TEXT` | 0 | `''` | 0 |
| 7 | `registrado_por` | `TEXT` | 0 | `''` | 0 |
| 8 | `creado_en` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `historial_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 3 | `num_transacciones` | `INTEGER` | 0 | `0` | 0 |
| 4 | `productos_activos` | `INTEGER` | 0 | `0` | 0 |
| 5 | `inventario_items` | `INTEGER` | 0 | `0` | 0 |
| 6 | `ventas_data` | `TEXT` | 0 | `'[]'` | 0 |
| 7 | `inventario_data` | `TEXT` | 0 | `'[]'` | 0 |
| 8 | `config_snapshot` | `TEXT` | 0 | `'{}'` | 0 |
| 9 | `ts_guardado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `historial_ventas`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `1` | 0 |
| 5 | `precio_unit` | `REAL` | 1 | `0` | 0 |
| 6 | `total` | `REAL` | 1 | `0` | 0 |
| 7 | `metodo_pago` | `TEXT` | 0 | `'efectivo'` | 0 |
| 8 | `vendedor_id` | `TEXT` | 0 | `NULL` | 0 |
| 9 | `vendedor_nombre` | `TEXT` | 0 | `NULL` | 0 |
| 10 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `ia_memory`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `session_id` | `TEXT` | 1 | `'default'` | 0 |
| 2 | `category` | `TEXT` | 1 | `'general'` | 0 |
| 3 | `key` | `TEXT` | 1 | `None` | 0 |
| 4 | `value` | `TEXT` | 1 | `None` | 0 |
| 5 | `metadata` | `TEXT` | 0 | `'{}'` | 0 |
| 6 | `confidence` | `REAL` | 0 | `1.0` | 0 |
| 7 | `access_count` | `INTEGER` | 0 | `0` | 0 |
| 8 | `created_at` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 9 | `updated_at` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 10 | `expires_at` | `TEXT` | 0 | `None` | 0 |

### `inventario_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `vendedor_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 4 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 5 | `cant_asignada` | `REAL` | 1 | `0` | 0 |
| 6 | `cant_vendida` | `REAL` | 0 | `0` | 0 |
| 7 | `cant_devuelta` | `REAL` | 0 | `0` | 0 |
| 8 | `cant_final` | `REAL` | 0 | `0` | 0 |
| 9 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 10 | `precio_costo` | `REAL` | 0 | `0` | 0 |
| 11 | `activo` | `INTEGER` | 0 | `1` | 0 |

### `inventario_general`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `stock_actual` | `REAL` | 1 | `0` | 0 |
| 4 | `stock_minimo` | `REAL` | 0 | `5` | 0 |
| 5 | `precio_compra` | `REAL` | 0 | `0` | 0 |
| 6 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 7 | `categoria` | `TEXT` | 0 | `'General'` | 0 |
| 8 | `unidad_medida` | `TEXT` | 0 | `'C/U'` | 0 |
| 9 | `actualizado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `inventarios`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cant_inicial` | `REAL` | 0 | `0` | 0 |
| 5 | `cant_final` | `REAL` | 0 | `0` | 0 |
| 6 | `vendido` | `REAL` | 0 | `0` | 0 |
| 7 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 8 | `precio_costo` | `REAL` | 0 | `0` | 0 |
| 9 | `importe` | `REAL` | 0 | `0` | 0 |
| 10 | `comision` | `REAL` | 0 | `0` | 0 |
| 11 | `ganancia_neta` | `REAL` | 0 | `0` | 0 |

### `licencias`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `licencia_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `admin_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `admin_nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `tipo` | `TEXT` | 1 | `'anual'` | 0 |
| 5 | `dias` | `INTEGER` | 1 | `365` | 0 |
| 6 | `fecha_inicio` | `TEXT` | 1 | `None` | 0 |
| 7 | `fecha_expira` | `TEXT` | 1 | `None` | 0 |
| 8 | `activa` | `INTEGER` | 0 | `1` | 0 |
| 9 | `notas` | `TEXT` | 0 | `''` | 0 |
| 10 | `creado_por` | `TEXT` | 1 | `None` | 0 |
| 11 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 12 | `cliente_id` | `TEXT` | 0 | `''` | 0 |
| 13 | `clave_activacion` | `TEXT` | 0 | `''` | 0 |

### `login_intentos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `username` | `TEXT` | 1 | `None` | 0 |
| 2 | `ip` | `TEXT` | 0 | `''` | 0 |
| 3 | `exito` | `INTEGER` | 0 | `0` | 0 |
| 4 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `logs_sistema`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `tipo` | `TEXT` | 0 | `'info'` | 0 |
| 2 | `usuario` | `TEXT` | 0 | `NULL` | 0 |
| 3 | `mensaje` | `TEXT` | 1 | `None` | 0 |
| 4 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `productos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `precio` | `REAL` | 1 | `0` | 0 |
| 4 | `costo` | `REAL` | 1 | `0` | 0 |
| 5 | `categoria` | `TEXT` | 0 | `'General'` | 0 |
| 6 | `unidad_medida` | `TEXT` | 0 | `'C/U'` | 0 |
| 7 | `en_oferta` | `INTEGER` | 0 | `0` | 0 |
| 8 | `imagen` | `TEXT` | 0 | `''` | 0 |
| 9 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 10 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `sqlite_sequence`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `name` | `` | 0 | `None` | 0 |
| 1 | `seq` | `` | 0 | `None` | 0 |

### `sqlite_stat1`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `tbl` | `` | 0 | `None` | 0 |
| 1 | `idx` | `` | 0 | `None` | 0 |
| 2 | `stat` | `` | 0 | `None` | 0 |

### `tiendas`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `nombre` | `TEXT` | 0 | `None` | 0 |
| 2 | `direccion` | `TEXT` | 0 | `None` | 0 |
| 3 | `telefono` | `TEXT` | 0 | `None` | 0 |
| 4 | `ruc` | `TEXT` | 0 | `None` | 0 |

### `usuarios`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `usuario_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `username` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `rol` | `TEXT` | 1 | `None` | 0 |
| 5 | `password_hash` | `TEXT` | 1 | `None` | 0 |
| 6 | `password_salt` | `TEXT` | 1 | `None` | 0 |
| 7 | `creado_por` | `TEXT` | 0 | `NULL` | 0 |
| 8 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 9 | `ultimo_acceso` | `TEXT` | 0 | `NULL` | 0 |
| 10 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `ventas_cabecera`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `client_txn_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `vendedor_id` | `TEXT` | 0 | `NULL` | 0 |
| 4 | `vendedor_nombre` | `TEXT` | 0 | `NULL` | 0 |
| 5 | `metodo_pago` | `TEXT` | 1 | `'efectivo'` | 0 |
| 6 | `total` | `REAL` | 1 | `0` | 0 |
| 7 | `estado` | `TEXT` | 1 | `'confirmada'` | 0 |
| 8 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `ventas_detalle`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `1` | 0 |
| 5 | `precio_unit` | `REAL` | 1 | `0` | 0 |
| 6 | `subtotal` | `REAL` | 1 | `0` | 0 |

## Base: `/data/data/com.termux/files/home/tpv-trabajo/app/src/main/python/tpv_datos.db`

### `app_state`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `clave` | `TEXT` | 1 | `None` | 0 |
| 2 | `valor` | `TEXT` | 1 | `None` | 0 |
| 3 | `actualizado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `auditoria`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `tabla` | `TEXT` | 1 | `None` | 0 |
| 2 | `accion` | `TEXT` | 1 | `None` | 0 |
| 3 | `registro_id` | `TEXT` | 1 | `None` | 0 |
| 4 | `campo` | `TEXT` | 0 | `''` | 0 |
| 5 | `valor_antes` | `TEXT` | 0 | `''` | 0 |
| 6 | `valor_nuevo` | `TEXT` | 0 | `''` | 0 |
| 7 | `usuario_id` | `TEXT` | 1 | `None` | 0 |
| 8 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `cierres_caja`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 3 | `total_costos` | `REAL` | 0 | `0` | 0 |
| 4 | `total_comisiones` | `REAL` | 0 | `0` | 0 |
| 5 | `ganancia_total` | `REAL` | 0 | `0` | 0 |
| 6 | `num_transacciones` | `INTEGER` | 0 | `0` | 0 |
| 7 | `efectivo` | `REAL` | 0 | `0` | 0 |
| 8 | `tarjeta` | `REAL` | 0 | `0` | 0 |
| 9 | `transferencia` | `REAL` | 0 | `0` | 0 |
| 10 | `cerrado_por` | `TEXT` | 0 | `NULL` | 0 |
| 11 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `cierres_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `vendedor_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 3 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 4 | `total_costo` | `REAL` | 0 | `0` | 0 |
| 5 | `ganancia_neta` | `REAL` | 0 | `0` | 0 |
| 6 | `items_json` | `TEXT` | 0 | `'[]'` | 0 |
| 7 | `creado_en` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `clientes`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `cliente_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `telefono` | `TEXT` | 0 | `''` | 0 |
| 4 | `email` | `TEXT` | 0 | `''` | 0 |
| 5 | `puntos` | `INTEGER` | 0 | `0` | 0 |
| 6 | `nivel` | `TEXT` | 0 | `'bronce'` | 0 |
| 7 | `notas` | `TEXT` | 0 | `''` | 0 |
| 8 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 9 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `descuentos_config`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `nombre` | `TEXT` | 1 | `'Descuento'` | 0 |
| 2 | `tipo` | `TEXT` | 1 | `'porcentaje'` | 0 |
| 3 | `valor` | `REAL` | 1 | `0` | 0 |
| 4 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 5 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `entradas_productos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `entrada_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `0` | 0 |
| 5 | `precio_compra` | `REAL` | 0 | `0` | 0 |
| 6 | `proveedor` | `TEXT` | 0 | `''` | 0 |
| 7 | `nota` | `TEXT` | 0 | `''` | 0 |
| 8 | `registrado_por` | `TEXT` | 1 | `None` | 0 |
| 9 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `gastos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `gasto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `descripcion` | `TEXT` | 1 | `None` | 0 |
| 3 | `monto` | `REAL` | 1 | `0` | 0 |
| 4 | `categoria` | `TEXT` | 0 | `'Otros'` | 0 |
| 5 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 6 | `nota` | `TEXT` | 0 | `''` | 0 |
| 7 | `registrado_por` | `TEXT` | 0 | `''` | 0 |
| 8 | `creado_en` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `historial_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `total_ventas` | `REAL` | 0 | `0` | 0 |
| 3 | `num_transacciones` | `INTEGER` | 0 | `0` | 0 |
| 4 | `productos_activos` | `INTEGER` | 0 | `0` | 0 |
| 5 | `inventario_items` | `INTEGER` | 0 | `0` | 0 |
| 6 | `ventas_data` | `TEXT` | 0 | `'[]'` | 0 |
| 7 | `inventario_data` | `TEXT` | 0 | `'[]'` | 0 |
| 8 | `config_snapshot` | `TEXT` | 0 | `'{}'` | 0 |
| 9 | `ts_guardado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `historial_ventas`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `1` | 0 |
| 5 | `precio_unit` | `REAL` | 1 | `0` | 0 |
| 6 | `total` | `REAL` | 1 | `0` | 0 |
| 7 | `metodo_pago` | `TEXT` | 0 | `'efectivo'` | 0 |
| 8 | `vendedor_id` | `TEXT` | 0 | `NULL` | 0 |
| 9 | `vendedor_nombre` | `TEXT` | 0 | `NULL` | 0 |
| 10 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `ia_memory`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `session_id` | `TEXT` | 1 | `'default'` | 0 |
| 2 | `category` | `TEXT` | 1 | `'general'` | 0 |
| 3 | `key` | `TEXT` | 1 | `None` | 0 |
| 4 | `value` | `TEXT` | 1 | `None` | 0 |
| 5 | `metadata` | `TEXT` | 0 | `'{}'` | 0 |
| 6 | `confidence` | `REAL` | 0 | `1.0` | 0 |
| 7 | `access_count` | `INTEGER` | 0 | `0` | 0 |
| 8 | `created_at` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 9 | `updated_at` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |
| 10 | `expires_at` | `TEXT` | 0 | `None` | 0 |

### `inventario_diario`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `vendedor_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 4 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 5 | `cant_asignada` | `REAL` | 1 | `0` | 0 |
| 6 | `cant_vendida` | `REAL` | 0 | `0` | 0 |
| 7 | `cant_devuelta` | `REAL` | 0 | `0` | 0 |
| 8 | `cant_final` | `REAL` | 0 | `0` | 0 |
| 9 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 10 | `precio_costo` | `REAL` | 0 | `0` | 0 |
| 11 | `activo` | `INTEGER` | 0 | `1` | 0 |

### `inventario_general`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `stock_actual` | `REAL` | 1 | `0` | 0 |
| 4 | `stock_minimo` | `REAL` | 0 | `5` | 0 |
| 5 | `precio_compra` | `REAL` | 0 | `0` | 0 |
| 6 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 7 | `categoria` | `TEXT` | 0 | `'General'` | 0 |
| 8 | `unidad_medida` | `TEXT` | 0 | `'C/U'` | 0 |
| 9 | `actualizado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `inventarios`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `fecha` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cant_inicial` | `REAL` | 0 | `0` | 0 |
| 5 | `cant_final` | `REAL` | 0 | `0` | 0 |
| 6 | `vendido` | `REAL` | 0 | `0` | 0 |
| 7 | `precio_venta` | `REAL` | 0 | `0` | 0 |
| 8 | `precio_costo` | `REAL` | 0 | `0` | 0 |
| 9 | `importe` | `REAL` | 0 | `0` | 0 |
| 10 | `comision` | `REAL` | 0 | `0` | 0 |
| 11 | `ganancia_neta` | `REAL` | 0 | `0` | 0 |

### `licencias`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `licencia_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `admin_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `admin_nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `tipo` | `TEXT` | 1 | `'anual'` | 0 |
| 5 | `dias` | `INTEGER` | 1 | `365` | 0 |
| 6 | `fecha_inicio` | `TEXT` | 1 | `None` | 0 |
| 7 | `fecha_expira` | `TEXT` | 1 | `None` | 0 |
| 8 | `activa` | `INTEGER` | 0 | `1` | 0 |
| 9 | `notas` | `TEXT` | 0 | `''` | 0 |
| 10 | `creado_por` | `TEXT` | 1 | `None` | 0 |
| 11 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `login_intentos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `username` | `TEXT` | 1 | `None` | 0 |
| 2 | `ip` | `TEXT` | 0 | `''` | 0 |
| 3 | `exito` | `INTEGER` | 0 | `0` | 0 |
| 4 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `logs_sistema`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `tipo` | `TEXT` | 0 | `'info'` | 0 |
| 2 | `usuario` | `TEXT` | 0 | `NULL` | 0 |
| 3 | `mensaje` | `TEXT` | 1 | `None` | 0 |
| 4 | `timestamp` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `productos`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 3 | `precio` | `REAL` | 1 | `0` | 0 |
| 4 | `costo` | `REAL` | 1 | `0` | 0 |
| 5 | `categoria` | `TEXT` | 0 | `'General'` | 0 |
| 6 | `unidad_medida` | `TEXT` | 0 | `'C/U'` | 0 |
| 7 | `en_oferta` | `INTEGER` | 0 | `0` | 0 |
| 8 | `imagen` | `TEXT` | 0 | `''` | 0 |
| 9 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 10 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `sqlite_sequence`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `name` | `` | 0 | `None` | 0 |
| 1 | `seq` | `` | 0 | `None` | 0 |

### `sqlite_stat1`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `tbl` | `` | 0 | `None` | 0 |
| 1 | `idx` | `` | 0 | `None` | 0 |
| 2 | `stat` | `` | 0 | `None` | 0 |

### `usuarios`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `usuario_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `username` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `rol` | `TEXT` | 1 | `None` | 0 |
| 5 | `password_hash` | `TEXT` | 1 | `None` | 0 |
| 6 | `password_salt` | `TEXT` | 1 | `None` | 0 |
| 7 | `creado_por` | `TEXT` | 0 | `NULL` | 0 |
| 8 | `activo` | `INTEGER` | 0 | `1` | 0 |
| 9 | `ultimo_acceso` | `TEXT` | 0 | `NULL` | 0 |
| 10 | `creado` | `TEXT` | 0 | `datetime('now','localtime')` | 0 |

### `ventas_cabecera`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `client_txn_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `vendedor_id` | `TEXT` | 0 | `NULL` | 0 |
| 4 | `vendedor_nombre` | `TEXT` | 0 | `NULL` | 0 |
| 5 | `metodo_pago` | `TEXT` | 1 | `'efectivo'` | 0 |
| 6 | `total` | `REAL` | 1 | `0` | 0 |
| 7 | `estado` | `TEXT` | 1 | `'confirmada'` | 0 |
| 8 | `fecha` | `TEXT` | 1 | `datetime('now','localtime')` | 0 |

### `ventas_detalle`
| cid | columna | tipo | notnull | default | pk |
|---:|---|---|---:|---|---:|
| 0 | `id` | `INTEGER` | 0 | `None` | 1 |
| 1 | `venta_id` | `TEXT` | 1 | `None` | 0 |
| 2 | `producto_id` | `TEXT` | 1 | `None` | 0 |
| 3 | `nombre` | `TEXT` | 1 | `None` | 0 |
| 4 | `cantidad` | `REAL` | 1 | `1` | 0 |
| 5 | `precio_unit` | `REAL` | 1 | `0` | 0 |
| 6 | `subtotal` | `REAL` | 1 | `0` | 0 |
