# Schema de Base de Datos — TPV UltraSmart v6.13.1

## 17 Tablas
### Core
| Tabla | Descripcion | Clave |
|-------|-------------|-------|
| `usuarios` | Usuarios del sistema (6 roles) | `usuario_id` UNIQUE |
| `productos` | Catalogo de productos | `producto_id` UNIQUE |
| `inventario_general` | Stock actual de cada producto | `producto_id` UNIQUE |
| `historial_ventas` | Cada item vendido (N items por venta) | `venta_id` (no unique) |

### Operaciones
| Tabla | Descripcion | Clave |
|-------|-------------|-------|
| `cierres_caja` | Cierres diarios con desglose | `fecha` UNIQUE |
| `gastos` | Gastos operativos | `gasto_id` UNIQUE |
| `entradas_productos` | Entradas al almacen | `entrada_id` UNIQUE |
| `inventario_diario` | Asignacion diaria por vendedor | `(fecha, vendedor_id, producto_id)` |
| `cierres_diario` | Cierre individual por vendedor | `(vendedor_id, fecha)` |
| `inventarios` | Snapshot de inventario por fecha | `(fecha, producto_id)` |
| `descuentos_config` | Configuracion de descuentos | `id` AUTO |

### Sistema
| Tabla | Descripcion | Clave |
|-------|-------------|-------|
| `app_state` | Estado persistente de la app | `clave` UNIQUE |
| `licencias` | Licencias de uso | `licencia_id` UNIQUE |
| `logs_sistema` | Logs de operacion | `id` AUTO |
| `login_intentos` | Intentos de login (anti-brute force) | `id` AUTO |
| `auditoria` | Cambios auditados | `id` AUTO |
| `historial_diario` | Snapshot diario completo | `fecha` UNIQUE |

## Roles validos (6)

CHECK(rol IN ('desarrollador','administrador','supervisor','vendedor','cajero','cliente'))

## Foreign Keys (4 total, todas a usuarios)

| Tabla | Columna | Referencia |
|-------|---------|------------|
| `historial_ventas` | `vendedor_id` | `usuarios(usuario_id)` |
| `inventario_diario` | `vendedor_id` | `usuarios(usuario_id)` |
| `cierres_diario` | `vendedor_id` | `usuarios(usuario_id)` |
| `auditoria` | `usuario_id` | `usuarios(usuario_id)` |

## Concurrencia
- Modo WAL activado (PRAGMA journal_mode = WAL)
- Foreign keys activadas (PRAGMA foreign_keys = ON)
- Transacciones con BEGIN IMMEDIATE para serializacion estricta
- Tests: tests/unit/test_concurrency_security.py (5 tests)

## Seguridad de contrasenas
- Algoritmo: scrypt (N=16384, r=8, p=1)
- Salt: 16 bytes aleatorios por usuario

## Notas
- historial_ventas.venta_id NO es UNIQUE: una venta puede tener multiples items
- Las FKs a productos fueron removidas para permitir ventas/entradas de productos no catalogados
- PRAGMA synchronous = NORMAL, temp_store = MEMORY, cache_size = -8000
