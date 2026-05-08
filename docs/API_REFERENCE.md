# Referencia de API v6.9

## Autenticacion
| POST | /api/auth/login     | Publico  | Login usuario/contrasena |
| POST | /api/auth/logout    | Todos    | Cerrar sesion             |
| GET  | /api/auth/usuario   | Todos    | Datos usuario actual      |

## Catalogo
| GET  | /api/catalogo                  | Login    | Productos activos     |
| POST | /api/catalogo/sync             | Admin    | Sincronizar productos |
| POST | /api/catalogo/sync-desde-inv   | Admin    | Catalogo desde inventario |

## Inventario
| POST | /api/inventario/importar-catalogo | Admin,Vend | Catálogo a inventario |
| GET  | /api/inventario/entradas          | Admin       | Historial entradas    |

## Ventas
| GET  | /api/ventas/diarias   | Admin,Vend | Ventas del dia |
| POST | /api/ventas/registrar | Todos      | Nueva venta    |
| GET  | /api/ventas/historial | Admin      | Historial completo |

## Tienda Online
| GET  | /api/tienda/productos | Publico  | Productos tienda |
| POST | /api/tienda/pedido    | Clientes | Nuevo pedido     |
| GET  | /api/tienda/pedidos   | Admin    | Pedidos pendientes|

## IA Assistant
| POST | /api/ia/chat     | Todos | Chat con IA |
| GET  | /api/ia/skills   | Todos | Habilidades |

## Licencias
| POST | /api/licencias/activar | Admin | Activar licencia |
| GET  | /api/licencias/estado  | Todos | Estado licencia  |

## Usuarios
| GET  | /api/usuarios/lista            | Admin | Lista usuarios    |
| POST | /api/usuarios/crear             | Admin | Crear usuario     |
| POST | /api/usuarios/desactivar        | Admin | Desactivar usuario|

## Respuestas

    {ok: true, datos: [...]}
    {ok: false, mensaje: Error...}

HTTP: 200 exito, 400 datos, 401 sin auth, 403 sin permisos.
