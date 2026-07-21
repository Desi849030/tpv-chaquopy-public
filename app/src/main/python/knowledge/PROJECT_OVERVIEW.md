# TPV Ultra Smart — Resumen offline

TPV Ultra Smart es una aplicación Android offline-first para punto de venta. Integra WebView, un backend Flask embebido mediante Chaquopy, SQLite en modo WAL y un agente IA por roles.

## Capas

1. Android: actividad, WebView, biometría y ciclo de vida.
2. Flask: API local y blueprints.
3. Dominio: ventas, catálogo, inventario, usuarios, licencias y reportes.
4. IA: intents, handlers por rol, ReAct, memoria, skills, caché y guardrails.
5. Datos: SQLite local y sincronización Supabase opcional.

## Roles

Cliente, vendedor, cajero, supervisor, administrador y desarrollador. El Desarrollador tiene acceso funcional `all`; los demás roles siguen el principio de menor privilegio.

## Calidad

La suite automatizada mantiene más de 500 pruebas y un gate de cobertura real igual o superior al 50%. El workflow de GitHub Actions valida Python antes de compilar el APK.

Esta documentación está empaquetada para que la IA pueda consultarla sin conexión.
