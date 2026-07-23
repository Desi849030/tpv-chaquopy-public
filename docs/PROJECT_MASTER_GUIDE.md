# TPV Ultra Smart — Guía maestra del proyecto

## 1. Qué problema resuelve

Un punto de venta que depende totalmente de Internet puede dejar de vender cuando la red falla. TPV Ultra Smart mantiene la transacción crítica en el dispositivo mediante SQLite y utiliza la conectividad para sincronización, diagnóstico y servicios complementarios.

## 2. Solución en una frase

Una APK Android offline-first que integra WebView, Flask y SQLite mediante Chaquopy, incorpora una IA explicable por roles y mide la conectividad por capas sin confundir métricas de aplicación con magnitudes físicas.

## 3. Flujo principal

```text
Usuario
  → interfaz HTML/CSS/JavaScript
  → WebView Android
  → Flask en loopback
  → autorización y reglas de negocio
  → SQLite local
  → respuesta inmediata
  → sincronización Supabase opcional
```

La venta local no espera a la WAN.

## 4. Capas

### Android

Gestiona ciclo de vida, WebView, biometría, permisos y runtime Chaquopy.

### Frontend

HTML define estructura; CSS aporta responsive y accesibilidad; JavaScript implementa interacción, login, ventas, inventario, debug y estados offline.

### Backend

Flask registra APIs y blueprints. Las entradas se validan, la sesión determina el rol y los errores no exponen detalles internos en producción.

### Dominio y datos

Python implementa ventas, inventario, usuarios, licencias y reportes. SQLite WAL es la fuente transaccional local.

### IA

Combina intents, handlers por rol, ReAct, memoria, skills, caché, guardrails y documentación offline. El LLM GGUF es opcional.

### Telecom

Separa DNS, TCP, TLS y HTTP. Mide RTT de aplicación, P95, variación, solicitudes fallidas y goodput. Declara limitaciones y no presenta HTTP como ICMP.

## 5. Rol Desarrollador

Es la identidad funcional de máximo nivel (`all`). Puede consultar todos los módulos y herramientas, pero no evita autenticación, auditoría o protección de secretos.

Su usuario, rol y contraseña son exclusivos. La contraseña se configura localmente una vez, se guarda hasheada y no puede reutilizarse en otra cuenta.

## 6. Por qué es Ingeniería en Telecomunicaciones

- Analiza continuidad bajo WAN variable.
- Relaciona servicio comercial con QoS end-to-end.
- Aplica OSI/TCP-IP con límites claros.
- Diferencia RTT HTTP, jitter observado, fallos y goodput.
- Mantiene el edge operativo cuando la nube no está disponible.
- Propone extensiones radio con APIs Android nativas.

## 7. Por qué es IA

No es únicamente un chat. El agente:

1. normaliza la consulta;
2. detecta intención;
3. valida rol;
4. selecciona handler/herramienta;
5. consulta SQLite, APIs o documentos;
6. aplica guardrails;
7. construye una respuesta con fuente y limitación;
8. conserva memoria contextual.

## 8. Calidad

- Suite pytest.
- Cobertura con gate >= 50%.
- CI antes del APK.
- ResourceWarning tratado como error.
- Smoke test de backend y frontend.
- Artefactos y checksums.
- Documentación indexada en SQLite.

## 9. Seguridad

- onboarding local;
- contraseña Desarrollador exclusiva;
- token de sesión;
- cookies HttpOnly/SameSite;
- detección SQLi/XSS;
- secrets en almacenamiento escribible;
- headers de seguridad;
- API sin caché;
- auditoría;
- límites de tamaño.

## 10. UI/UX

- responsive móvil/tablet/escritorio;
- objetivos táctiles de 44 px;
- foco visible;
- contraste y movimiento reducido;
- tablas desplazables;
- safe-area;
- banner offline/reconexión;
- debugger con mensajes deduplicados.

## 11. Limitaciones honestas

- La APK de CI es debug si no se configura firma release.
- No mide actualmente RSRP, RSRQ o SINR.
- El goodput no equivale a capacidad física.
- Un LLM no viene incluido por defecto.
- La accesibilidad requiere validación manual TalkBack.
- La bibliografía del estado del arte debe verificarse externamente.

## 12. Mejoras futuras

- release firmada;
- experimentos Wi-Fi/celular/modo avión;
- dashboard temporal Telecom;
- TelephonyManager/NetworkCallback;
- exportación anonimizada;
- cobertura >= 60%;
- migraciones versionadas;
- SBOM y análisis de dependencias;
- evaluación cuantitativa de la IA.

## 13. Comandos de IA para la defensa

```text
defensa completa
capas OSI
Chaquopy
estado del arte
diagramas
estructura de carpetas
módulos y funciones telecom
frontend CSS
todos los documentos
explica el documento PROJECT_MASTER_GUIDE.md
```

## 14. Documentos recomendados

1. `PROJECT_MASTER_GUIDE.md` — visión integral.
2. `THESIS_DEFENSE_GUIDE.md` — guion de defensa.
3. `TELECOM_ENGINEERING.md` — método experimental.
4. `SYSTEM_LAYERS_AND_OSI.md` — capas.
5. `CHAQUOPY_INTEGRATION.md` — integración Android/Python.
6. `STATE_OF_THE_ART.md` — comparación.
7. `UI_UX_AND_SECURITY_FINAL.md` — pulido y hardening.
8. `ROADMAP_10_10.md` — pendientes.
