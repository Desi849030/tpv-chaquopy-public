# Esquema de Base de Datos - TPV Ultra Smart

## Tablas principales (15)

### productos
| Columna | Tipo | Descripción |
|---------|------|-------------|
| producto_id | TEXT PK | ID único del producto |
| nombre | TEXT | Nombre del producto |
| precio | REAL | Precio de venta |
| costo | REAL | Costo de compra |
| categoria | TEXT | Categoría |
| stock_actual | REAL | Stock disponible |
| activo | INTEGER | 1=activo, 0=inactivo |

### historial_ventas
| Columna | Tipo | Descripción |
|---------|------|-------------|
| venta_id | TEXT PK | ID único de venta |
| producto_id | TEXT | Producto vendido |
| nombre | TEXT | Nombre al momento de venta |
| cantidad | REAL | Unidades vendidas |
| total | REAL | Monto total |
| metodo_pago | TEXT | Efectivo, tarjeta, etc |
| fecha | TEXT | Fecha de la transacción |

### inventario_general
| Columna | Tipo | Descripción |
|---------|------|-------------|
| producto_id | TEXT PK | ID del producto |
| stock_actual | REAL | Stock en almacén |
| stock_minimo | REAL | Punto de reorden |
| precio_compra | REAL | Último precio de compra |
| precio_venta | REAL | Precio de venta actual |

### usuarios
| Columna | Tipo | Descripción |
|---------|------|-------------|
| usuario_id | TEXT PK | ID único |
| username | TEXT UNIQUE | Nombre de usuario |
| rol | TEXT | desarrollador/admin/supervisor/vendedor |
| password_hash | TEXT | Hash SHA-256 |
| activo | INTEGER | 1=activo |

### licencias
| Columna | Tipo | Descripción |
|---------|------|-------------|
| licencia_id | TEXT PK | ID único |
| admin_id | TEXT | Administrador asociado |
| tipo | TEXT | diaria/mensual/anual/ilimitada |
| fecha_expira | TEXT | Fecha de vencimiento |

### loyalty_clients
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER PK | ID autoincremental |
| phone | TEXT UNIQUE | Teléfono del cliente |
| name | TEXT | Nombre |
| points | INTEGER | Puntos acumulados |
| tier | TEXT | bronze/silver/gold/platinum |
