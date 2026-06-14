# Demo 3 minutos — TPV Ultra Smart v8.0

## Objetivo
Mostrar estabilidad, seguridad, flujo de venta e integración general en una demostración breve y controlada.

## Guion recomendado

### 1. Inicio del sistema
- Abrir la aplicación
- Mostrar login
- Explicar que corre localmente con backend Flask embebido y SQLite

### 2. Autenticación
- Entrar con usuario de prueba
- Mencionar control por roles y endurecimiento de sesión

### 3. Catálogo
- Mostrar productos
- Buscar un producto
- Añadir al carrito

### 4. Venta correcta
- Registrar una venta válida
- Mostrar total calculado
- Confirmar respuesta exitosa

### 5. Validación de seguridad/negocio
- Explicar que el endpoint de ventas exige autenticación
- Explicar que la venta es atómica y valida stock antes de confirmar

### 6. Consulta operativa
- Mostrar ventas del día
- Mostrar totales del día/mes
- Mostrar cierre o healthcheck

### 7. Estado técnico
- Abrir `/health` o `/api/health`
- Explicar CI en GitHub Actions
- Mencionar tests críticos automatizados

## Mensaje técnico clave
Se priorizó robustez, seguridad y mantenibilidad sobre complejidad experimental, reforzando primero los flujos críticos del TPV.

## Frases útiles para defender
- “El registro de ventas ahora es transaccional y valida stock antes de confirmar.”
- “Los endpoints críticos quedaron protegidos con autenticación y pruebas de regresión.”
- “El sistema incorpora healthcheck, CI y documentación OpenAPI mínima para facilitar operación y evolución.”
