# Defensa técnica — TPV Ultra Smart v8.0

## Resumen
TPV Ultra Smart v8.0 es un sistema de punto de venta orientado a ejecución local/offline-first, con backend Flask embebido, almacenamiento SQLite y frontend servido localmente. El proyecto está preparado para ejecutarse en entorno móvil/Android mediante Chaquopy y también en entorno de desarrollo desde Termux.

## Objetivos del proyecto
- Registrar ventas de forma rápida y segura
- Gestionar inventario y stock
- Mantener operación local incluso con conectividad limitada
- Proveer trazabilidad, seguridad básica y pruebas automatizadas
- Permitir evolución modular mediante blueprints

## Arquitectura
### Backend
- Flask
- Blueprints modulares
- SQLite como base de datos local
- Endpoints API bajo `/api/*`

### Frontend
- HTML/CSS/JS servido localmente
- Integración con backend por HTTP local
- Preparado para empaquetado Android

### Persistencia
- SQLite
- PRAGMA activados:
  - `foreign_keys = ON`
  - `journal_mode = WAL`
  - `synchronous = NORMAL`
  - `busy_timeout = 5000`

## Mejoras implementadas en esta iteración
### 1. Seguridad
- Endpoints críticos de ventas protegidos con autenticación
- Headers de seguridad:
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
- Cookies de sesión endurecidas:
  - `HTTPOnly`
  - `SameSite=Lax`
  - `SESSION_COOKIE_SECURE` configurable
- Comparación segura de hashes con `hmac.compare_digest`

### 2. Integridad de negocio
- Registro de ventas con transacción atómica
- Validación de stock antes de confirmar la venta
- Rechazo explícito por stock insuficiente
- El vendedor se toma de la sesión, no del cliente

### 3. Observabilidad y estado
- Endpoint `/health`
- Endpoint `/api/health`
- Verificación rápida de la BD con `PRAGMA quick_check`
- Logging de eventos relevantes
- Auditoría básica de ventas

### 4. Calidad
- Tests críticos automatizados
- GitHub Actions para ejecución continua
- Cobertura funcional en:
  - seguridad
  - ventas
  - autenticación
  - healthcheck

## Endpoints relevantes
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/ventas/registrar`
- `GET /api/ventas/hoy`
- `GET /api/ventas/totales`
- `POST /api/ventas/cierre`
- `GET /health`
- `GET /api/health`

## Decisiones de diseño
### Por qué SQLite
- Ligero
- Adecuado para ejecución local/offline
- Simple de desplegar en móvil

### Por qué blueprints
- Separación modular
- Mantenibilidad
- Facilidad para pruebas

### Por qué no se añadieron tecnologías más pesadas en este sprint
Se priorizó fiabilidad, seguridad y demostrabilidad sobre complejidad experimental. Antes de incorporar componentes como sincronización avanzada o IA pesada, se reforzaron primero las operaciones críticas del TPV.

## Riesgos mitigados
- Venta sin autenticación
- Venta con stock insuficiente
- Confianza indebida en datos enviados por cliente
- Ausencia de healthcheck
- Falta de validación continua en CI

## Estado actual
El proyecto se encuentra en una fase estable y defendible, con foco en:
- robustez operativa
- seguridad razonable
- mantenibilidad
- preparación para demostración académica

## Trabajo futuro
- devoluciones y notas de crédito
- documentación OpenAPI más amplia
- mayor cobertura E2E
- sincronización remota más avanzada
- panel administrativo de auditoría
