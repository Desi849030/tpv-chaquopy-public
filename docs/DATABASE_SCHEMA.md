# Schema de Base de Datos — TPV UltraSmart v6.13.1

## Resumen verificable del esquema SQLite (WAL)

- **20 tablas base** creadas en `database.crear_tablas()` (`24` con `crear_tablas_tienda()`, `26` totales al incluir `documentacion` e `ia_conversations` en el arranque completo de Flask).
- **12 índices explícitos B-Tree** en `database.crear_tablas()` (`14` totales con los índices de historial conversacional IA).
- **6 claves foráneas activas** verificadas con `PRAGMA foreign_keys = ON`.
- **6 perfiles de rol** forzados mediante restricción declarativa `CHECK`.

### Núcleo transaccional e idempotencia (`ventas_atomic_v10`)
| Tabla | Descripción | Clave / Restricción |
|---|---|---|
| `usuarios` | Usuarios del sistema (6 roles RBAC) | `usuario_id` UNIQUE, `username` UNIQUE |
| `productos` | Catálogo maestro de productos | `producto_id` UNIQUE |
| `inventario_general` | Stock disponible en tiempo real | `producto_id` UNIQUE |
| `ventas_cabecera` | Cabecera atómica e idempotente por venta | `venta_id` UNIQUE, `client_txn_id` UNIQUE |
| `ventas_detalle` | Líneas de detalle de cada venta | FK `venta_id -> ventas_cabecera(venta_id)` `ON DELETE CASCADE` |
| `historial_ventas` | Histórico denormalizado por línea vendida (N ítems por `venta_id`) | FK `vendedor_id -> usuarios(usuario_id)` |

### Operaciones de caja, inventario y gastos
| Tabla | Descripción | Clave / Restricción |
|---|---|---|
| `cierres_caja` | Arqueos diarios con desglose por medio de pago | `fecha` UNIQUE |
| `gastos` | Registro de egresos y gastos operativos | `gasto_id` UNIQUE |
| `entradas_productos` | Entradas de mercancía al almacén | `entrada_id` UNIQUE |
| `inventario_diario` | Asignación diaria por vendedor | `UNIQUE(fecha, vendedor_id, producto_id)` + FK `usuarios` |
| `cierres_diario` | Liquidación diaria individual por vendedor | `UNIQUE(vendedor_id, fecha)` + FK `usuarios` |
| `inventarios` | Instantánea consolidada de inventario por fecha | `UNIQUE(fecha, producto_id)` |
| `descuentos_config` | Reglas de descuentos y comisiones | `id` AUTOINCREMENT |
| `historial_diario` | Instantánea JSON consolidada de cierre diario | `fecha` UNIQUE |

### Seguridad, auditoría, licencias y comercio electrónico
| Tabla | Descripción | Clave / Restricción |
|---|---|---|
| `app_state` | Parámetros persistentes de configuración local | `clave` UNIQUE |
| `licencias` | Licencias firmadas de operación offline/online | `licencia_id` UNIQUE |
| `logs_sistema` | Bitácora técnica de eventos | `id` AUTOINCREMENT |
| `login_intentos` | Control de tasa contra fuerza bruta en login | `id` AUTOINCREMENT |
| `auditoria` | Trazabilidad administrativa vinculada a usuario | FK `usuario_id -> usuarios(usuario_id)` |
| `audit_logs` | Bitácora forense transaccional (`registrar_venta`, auth, cambios) | `id` AUTOINCREMENT |
| `tiendas` / `clientes_tienda` / `pedidos_tienda` / `items_pedido` | Subsistema e-commerce integrado (`tienda_routes.py`) | FK `items_pedido.pedido_id -> pedidos_tienda(pedido_id)` |
| `documentacion` / `ia_conversations` | Corpus técnico offline y memoria conversacional IA | Índices `idx_conv_user`, `idx_conv_session` |

## Roles válidos (6)

```sql
CHECK(rol IN ('desarrollador','administrador','supervisor','vendedor','cajero','cliente'))
```

## Claves foráneas activas (6 relaciones verificadas)

| Tabla origen | Columna | Tabla destino | Acción referencial |
|---|---|---|---|
| `ventas_detalle` | `venta_id` | `ventas_cabecera(venta_id)` | `ON DELETE CASCADE` |
| `items_pedido` | `pedido_id` | `pedidos_tienda(pedido_id)` | `NO ACTION` |
| `historial_ventas` | `vendedor_id` | `usuarios(usuario_id)` | `NO ACTION` |
| `inventario_diario` | `vendedor_id` | `usuarios(usuario_id)` | `NO ACTION` |
| `cierres_diario` | `vendedor_id` | `usuarios(usuario_id)` | `NO ACTION` |
| `auditoria` | `usuario_id` | `usuarios(usuario_id)` | `NO ACTION` |

## Concurrencia, atomicidad y seguridad criptográfica
- **Modo WAL**: `PRAGMA journal_mode = WAL`, `PRAGMA synchronous = NORMAL`, `PRAGMA busy_timeout = 5000`, `PRAGMA foreign_keys = ON`.
- **Serialización transaccional**: `BEGIN IMMEDIATE` en `modules/ventas_atomic_v10.py` + verificación de unicidad `client_txn_id` + actualización condicional `WHERE stock_actual >= ?` con `ROLLBACK` total ante faltante en cualquier ítem del carrito.
- **Credenciales**: derivación `scrypt` (`N=16384, r=8, p=1`) con sal aleatoria de 16 bytes por usuario y comparación en tiempo constante (`hmac.compare_digest`).
- **Suite de verificación**: `tests/unit/test_concurrency_security.py` (7 pruebas automatizadas en `pytest`).
