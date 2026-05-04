# API TPV Ultra Smart - Documentación Interactiva

## Autenticación
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| POST | /api/auth/login | No | Iniciar sesión |
| GET | /api/auth/me | No | Datos del usuario |

## Productos
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/catalogo | Sí | Listar productos |
| POST | /api/catalogo/sync | Admin | Sincronizar |

## Ventas
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/reportes/ventas | Sí | Reporte de ventas |

## IA Chat
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| POST | /api/ia/chat | No | Chat con agente IA |
| GET | /api/ia/status | No | Estado del agente |

## Seguridad
| Método | Ruta | Auth | Descripción |
|--------|------|:---:|-------------|
| GET | /api/biometric/check | No | Verificar biometría |
| POST | /api/payment/tokenize | Sí | Tokenizar pago |
