# API Reference - TPV Ultra Smart v1.0

## Autenticación
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| POST | /api/auth/login | No | Iniciar sesión |
| POST | /api/auth/logout | No | Cerrar sesión |
| GET | /api/auth/me | No | Usuario actual |

## Productos
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/catalogo | Sí | Listar productos |
| POST | /api/catalogo/sync | Admin | Sincronizar catálogo |

## Ventas
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/reportes/ventas | Sí | Reporte de ventas |
| GET | /api/reportes/resumen | Sí | Resumen ejecutivo |

## Inventario
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/inventario/general | Admin | Inventario general |
| POST | /api/inventario/entrada | Admin | Registrar entrada |

## IA Chat
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| POST | /api/ia/chat | No | Chat con agente IA |
| GET | /api/ia/status | No | Estado del agente |
| GET | /api/ia/alerts | No | Alertas proactivas |

## Seguridad
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/biometric/check | No | Verificar biometría |
| POST | /api/payment/tokenize | Sí | Tokenizar pago |
| GET | /api/health | No | Health check |

## Descuentos
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/descuentos | Sí | Listar descuentos |
| POST | /api/descuentos | Admin | Crear descuento |
| DELETE | /api/descuentos/:id | Admin | Eliminar descuento |

## Supabase
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/supabase/config | Admin | Ver configuración |
| POST | /api/supabase/config | Admin | Guardar configuración |
| POST | /api/supabase/sync-full | Admin | Sincronizar todo |
