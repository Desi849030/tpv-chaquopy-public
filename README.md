# TPV Ultra Smart

[![Android CI](https://github.com/Desi849030/tpv-chaquopy-public/actions/workflows/android-ci.yml/badge.svg)](https://github.com/Desi849030/tpv-chaquopy-public/actions/workflows/android-ci.yml)
![Version](https://img.shields.io/badge/version-6.13.1-blue)
![Coverage](https://img.shields.io/badge/coverage-55.4%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-579%20passed-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.14-blue)
![Android](https://img.shields.io/badge/Android-API%2021%2B-3DDC84)
![License](https://img.shields.io/badge/license-MIT-blue)

Aplicación Android de punto de venta **offline-first** con backend Flask embebido mediante Chaquopy, base de datos SQLite y agente IA por roles. Las operaciones esenciales funcionan localmente; Supabase es una capacidad opcional de sincronización.

> Estado de calidad validado: **579 pruebas superadas, 71 omitidas y 55.43% de cobertura**. El workflow bloquea la compilación del APK si los tests fallan o la cobertura baja del 50%.

## Capacidades principales

- Punto de venta, caja, cierres y métodos de pago.
- Catálogo, precios, inventario general e inventario diario.
- Gastos, reportes, métricas y exportación.
- Usuarios, privilegios, licencias y sesiones por rol.
- Tienda, clientes y lealtad.
- Operación local con SQLite WAL.
- Sincronización Supabase opcional.
- Agente IA offline con intents, handlers por rol, memoria, ReAct, skills, caché y guardrails.
- LLM GGUF opcional mediante `TPV_LLM_MODEL`; no es requisito para el motor modular.
- Documentación técnica sincronizada a SQLite para consulta offline por la IA.
- Diagnóstico telecom por capas: DNS, TCP, TLS, RTT HTTP, variación, fallos, goodput y plano local SQLite.
- Telemetría, logs y auditoría para mantenimiento.

## Arquitectura

```text
Android / WebView
        │ HTTP local
        ▼
Flask + Blueprints
        ├── Dominio: ventas, catálogo, inventario, usuarios, licencias
        ├── IA: intents → rol → handlers → ReAct/memoria → guardrails
        ├── Documentación offline → tabla SQLite documentacion
        └── Integraciones opcionales → Supabase
        │
        ▼
SQLite (WAL)
```

Consulta el detalle en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y el índice documental en [docs/README.md](docs/README.md).

## Matriz de roles

| Rol | Alcance principal |
|---|---|
| Cliente | Catálogo, precios, ofertas, disponibilidad y lealtad |
| Vendedor | Ventas, productos, precios y stock operativo |
| Cajero | Caja, cobros, tickets y arqueo |
| Supervisor | Operación, equipo, inventario, tendencias y reportes |
| Administrador | Gestión integral del negocio, usuarios, finanzas y configuración |
| **Desarrollador** | **Acceso funcional total (`all`) a módulos, herramientas y datos** |

### Desarrollador: acceso funcional sin límites

El rol `desarrollador` es la máxima autoridad funcional. No está restringido por la matriz de permisos de negocio y puede operar todos los módulos, consultar documentación, usar telemetría, auditar, diagnosticar y mantener el sistema.

Acceso total no significa seguridad desactivada: autenticación, sesión válida, sanitización, auditoría, integridad transaccional y protección de secretos siguen siendo obligatorias. Consulta [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).

## IA y documentación offline

Durante la inicialización, todos los documentos de texto disponibles en la raíz y en `docs/` se sincronizan con la tabla SQLite `documentacion`. Los nombres relativos evitan colisiones entre evidencias históricas. La tarea Gradle `syncOfflineDocumentation` empaqueta ese mismo corpus dentro del source set Python del APK; también existen resúmenes esenciales como fallback.

Ejemplos para el rol Desarrollador:

```text
documentación
lee el documento DEVELOPER_GUIDE.md
muéstrame la arquitectura
abre el schema de base de datos
qué puede hacer el desarrollador
```

La IA puede leer documentación técnica, pero nunca debe revelar contraseñas, tokens, claves privadas ni hashes reutilizables.

## Requisitos

### Android / APK

- Android SDK 34
- JDK 17
- Gradle Wrapper incluido
- Chaquopy con Python 3.10
- Android API mínima 21

### Backend y pruebas

- Python 3.10–3.13: stack Flask 2.2 compatible con Chaquopy
- Python 3.14+: stack Flask 3.1 compatible con Termux
- pytest y pytest-cov

Las dependencias condicionales están declaradas en `requirements.txt` y `pyproject.toml`.

## Inicio rápido en Termux

```bash
pkg update
pkg install python git gh

git clone https://github.com/Desi849030/tpv-chaquopy-public.git
cd tpv-chaquopy-public
python -m pip install --upgrade -r requirements.txt pytest pytest-cov
```

Preparar y ejecutar en navegador:

```bash
bash tools/tpv_termux_setup.sh
bash tools/tpv_termux_run.sh
```

Alternativa manual:

```bash
export PYTHONPATH="$PWD/app/src/main/python"
export TPV_FRONTEND_DIR="$PWD/app/src/main/assets/frontend"
export TPV_FILES_DIR="$HOME/.local/share/tpv-ultra-smart"
python app/src/main/python/app.py
```

Abre `http://127.0.0.1:5000`. En una instalación nueva, revisa la consola de inicialización y cambia inmediatamente las credenciales de desarrollo. No publiques contraseñas ni bases de datos.

## Calidad y cobertura

Ejecución oficial:

```bash
python -m pytest \
  --cov=app/src/main/python \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=50
```

Resultado de referencia:

```text
579 passed, 71 skipped
TOTAL 12377 statements, 5516 missing, 55.43% coverage
```

La configuración de cobertura excluye únicamente launchers bloqueantes, scripts de migración y fragmentos sustituidos que no forman parte del runtime registrado. No se excluyen módulos activos para inflar el porcentaje.

## Compilar el APK

```bash
./gradlew clean assembleDebug --no-build-cache
```

Salida esperada:

```text
app/build/outputs/apk/debug/*.apk
```

El workflow de GitHub Actions ejecuta primero tests y cobertura; el APK solo se compila si la validación Python termina correctamente.

## Estructura del repositorio

```text
.
├── .github/                  # CI, plantillas y automatización
├── app/
│   └── src/main/
│       ├── java/             # Capa Android
│       ├── assets/           # Frontend WebView
│       └── python/           # Flask, dominio, IA y SQLite
├── docs/                     # Documentación técnica y operativa
├── scripts/                  # Automatización mantenida
├── tests/
│   ├── unit/                 # Suite soportada y aislada
│   └── ia/                   # Pruebas del agente
├── tools/                    # Utilidades de diagnóstico y Termux
├── CHANGELOG.md
├── SECURITY.md
├── pyproject.toml
└── requirements.txt
```

## Documentación

- [Índice de documentación](docs/README.md)
- [Guía del Desarrollador](docs/DEVELOPER_GUIDE.md)
- [Arquitectura](docs/ARCHITECTURE.md)
- [Referencia API](docs/API_REFERENCE.md)
- [Esquema de base de datos](docs/DATABASE_SCHEMA.md)
- [Contribuir](docs/CONTRIBUTING.md)
- [Checklist de release](docs/CHECKLIST_RELEASE.md)
- [Roadmap APK 10/10](docs/ROADMAP_10_10.md)
- [Ingeniería en Telecomunicaciones](docs/TELECOM_ENGINEERING.md)
- [Diagnóstico Telecom](docs/telecom_diagnostico.md)
- [Organización del repositorio](docs/REPOSITORY_STRUCTURE.md)
- [Política de seguridad](SECURITY.md)
- [Historial de cambios](CHANGELOG.md)

## Seguridad

No subas al repositorio:

- bases de datos o archivos WAL;
- APK/AAB generados;
- keystores;
- tokens, claves API o credenciales;
- archivos `.env` reales;
- reportes que contengan información personal.

Reporta vulnerabilidades siguiendo [SECURITY.md](SECURITY.md).

## Contribución

1. Crea una rama desde `main`.
2. Mantén los cambios pequeños y documentados.
3. Añade o actualiza pruebas.
4. Ejecuta el gate de cobertura.
5. Verifica el APK cuando el cambio afecte Android.
6. Abre un Pull Request usando la plantilla del repositorio.

Consulta [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) para el flujo completo.

## Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](LICENSE).
