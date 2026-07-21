# Arquitectura de TPV Ultra Smart

## Objetivos

- Operación local aunque no exista conexión a Internet.
- Backend Python compartido entre Android, Termux y pruebas CI.
- Persistencia SQLite con sincronización remota opcional.
- Separación por roles y mínimo privilegio, excepto Desarrollador con capacidad funcional `all`.
- IA útil sin depender obligatoriamente de un modelo o API externa.

## Vista de contexto

```text
┌──────────────── Android ────────────────┐
│ MainActivity + WebView + biometría      │
│ Chaquopy Python 3.10                    │
└──────────────────┬──────────────────────┘
                   │ HTTP 127.0.0.1
┌──────────────────▼──────────────────────┐
│ Flask                                      │
│ app.py + blueprints registrados            │
│ auth · ventas · inventario · tienda · IA   │
└──────┬───────────────────┬──────────────┘
       │                   │
┌──────▼────────┐   ┌──────▼──────────────┐
│ SQLite / WAL  │   │ IA offline-first     │
│ datos + docs  │   │ intents + handlers  │
│ + auditoría   │   │ ReAct + memoria     │
└──────┬────────┘   └─────────────────────┘
       │ opcional
┌──────▼────────┐
│ Supabase      │
│ sincronización│
└───────────────┘
```

## Capas

### 1. Android

Ubicación: `app/src/main/java` y `app/src/main/assets`.

Responsabilidades:

- ciclo de vida de la aplicación;
- WebView y puente nativo;
- biometría;
- arranque del backend local;
- empaquetado y permisos Android.

### 2. Aplicación Flask

Entrada principal: `app/src/main/python/app.py`.

Responsabilidades:

- creación y configuración de Flask;
- registro de blueprints activos;
- endpoints de compatibilidad aún alojados en el monolito;
- sesión, errores HTTP y middleware;
- coordinación con dominio, SQLite e IA.

El repositorio conserva algunos módulos históricos o sustituidos para compatibilidad y migración. `.coveragerc` documenta cuáles no forman parte del runtime registrado.

### 3. Dominio y persistencia

Componentes principales:

- `database.py`: esquema y operaciones heredadas aún activas;
- `db_connection.py`: conexión SQLite y auditoría;
- `db/`: DAOs modulares;
- `models/`: contratos tipados;
- `license/`: licencias locales;
- `security/`: criptografía, validación y auditoría;
- `response_validators/`: validación de respuestas.

SQLite usa `TPV_FILES_DIR` como directorio escribible en Android y pruebas. Las conexiones deben cerrarse de forma determinista.

### 4. Agente IA

Flujo principal:

```text
mensaje
  → identidad y rol
  → normalización/guardrails
  → intent router
  → caché o memoria
  → handler por rol
  → ReAct/skills cuando aplica
  → validación y presupuesto de respuesta
  → respuesta + auditoría
```

Roles soportados:

- cliente;
- vendedor;
- cajero;
- supervisor;
- administrador;
- desarrollador.

El Desarrollador tiene capacidad `all`. Los controles técnicos de autenticación, auditoría y protección de secretos permanecen activos.

### 5. Documentación offline

`documentation_loader.py` sincroniza documentos curados con la tabla `documentacion`.

En Termux/desktop se leen directamente los archivos del checkout. Antes de compilar Android, la tarea Gradle `syncOfflineDocumentation` copia todos los documentos soportados al source set Python generado. El APK conserva además resúmenes esenciales en `app/src/main/python/knowledge/` como fallback.

La sincronización es idempotente y ocurre al crear/inicializar las tablas.

### 6. Sincronización remota

`supabase_sync.py` proporciona integración opcional. La falta de red no debe impedir ventas, inventario, login local ni lectura de documentación empaquetada.

## Flujo de una petición

1. La interfaz ejecuta `fetch()` contra el backend local.
2. Flask resuelve la ruta y valida sesión/rol.
3. El handler valida la entrada.
4. El dominio ejecuta la operación SQLite.
5. Se registra auditoría cuando corresponde.
6. Se serializa una respuesta JSON estable.
7. La UI actualiza el estado visible.

## Inicialización

1. Determinar `TPV_FILES_DIR`.
2. Abrir SQLite y activar pragmas.
3. Crear/migrar tablas e índices de forma idempotente.
4. Crear identidad inicial de desarrollo cuando la instalación está vacía.
5. Sincronizar documentación offline.
6. Registrar blueprints y arrancar Flask.

## Calidad

- pytest como runner único;
- bases temporales por sesión de pruebas;
- cobertura con gate mínimo del 50%;
- CI en Python 3.11;
- pruebas adicionales en Termux/Python 3.14;
- build Android condicionado al éxito de tests.

## Decisiones y deuda técnica

- `app.py` y `database.py` todavía concentran responsabilidades; deben reducirse gradualmente, nunca mediante copias paralelas.
- Existen facades y módulos históricos; deben inventariarse antes de eliminarse.
- Los `ResourceWarning` de SQLite deben tratarse como deuda prioritaria.
- La credencial inicial de una instalación nueva debe rotarse antes de uso real.
- La cobertura debe subir mediante pruebas de comportamiento de módulos activos.
