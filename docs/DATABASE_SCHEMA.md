# Schema de Base de Datos — TPV UltraSmart v8.0

## 18 Tablas

### Core

| Tabla | Descripción | Clave |
|-------|-------------|-------|
| `usuarios` | Usuarios del sistema (5 roles) | `usuario_id` UNIQUE |
| `productos` | Catálogo de productos | `producto_id` UNIQUE |
| `inventario_general` | Stock actual de cada producto | `producto_id` UNIQUE |
| `historial_ventas` | Cada ítem vendido (N items por venta) | `venta_id` (no unique) |
| `clientes` | Clientes registrados | `cliente_id` UNIQUE |

### Operaciones

| Tabla | Descripción | Clave |
|-------|-------------|-------|
| `cierres_caja` | Cierres diarios con desglose | `fecha` UNIQUE |
| `gastos` | Gastos operativos | `gasto_id` UNIQUE |
| `entradas_productos` | Entradas al almacén | `entrada_id` UNIQUE |
| `inventario_diario` | Asignación diaria por vendedor | `(fecha, vendedor_id, producto_id)` |
| `cierres_diario` | Cierre individual por vendedor | `(vendedor_id, fecha)` |
| `inventarios` | Snapshot de inventario por fecha | `(fecha, producto_id)` |
| `descuentos_config` | Configuración de descuentos | `id` AUTO |

### Sistema

| Tabla | Descripción | Clave |
|-------|-------------|-------|
| `app_state` | Estado persistente de la app | `clave` UNIQUE |
| `licencias` | Licencias de uso | `licencia_id` UNIQUE |
| `logs_sistema` | Logs de operación | `id` AUTO |
| `login_intentos` | Intentos de login (anti-brute force) | `id` AUTO |
| `auditoria` | Cambios auditados | `id` AUTO |
| `historial_diario` | Snapshot diario completo | `fecha` UNIQUE |

## Roles válidos

```sql
CHECK(rol IN ('desarrollador','administrador','supervisor','vendedor','cajero'))
```

## Seguridad de contraseñas

- Algoritmo: **scrypt** (N=16384, r=8, p=1)
- Salt: 16 bytes aleatorios por usuario
- Almacenamiento: `password_hash` + `password_salt`

## Notas importantes

- `historial_ventas.venta_id` NO es UNIQUE: una venta puede tener múltiples ítems
  con el mismo `venta_id` (uno por producto)
- `cierres_caja` incluye columnas `efectivo`, `tarjeta`, `transferencia`
- Modo WAL activado para concurrencia
- Foreign keys activadas por defecto
