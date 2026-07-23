# Guía para explicar el proyecto a un jurado no técnico

## Regla principal

Primero explica el problema y el beneficio. Después muestra la evidencia. Solo al final utiliza el término técnico.

## Proyecto

**Sencillo:** es una caja y sistema de inventario que sigue funcionando sin Internet.

**Evidencia:** registrar una venta en modo avión y mostrar que permanece guardada.

**Técnico:** arquitectura edge/offline-first con SQLite y sincronización opcional.

## Inteligencia artificial

**Sencillo:** es un asistente que entiende la pregunta, respeta quién pregunta y busca la información correcta.

**Evidencia:** hacer la misma pregunta con roles distintos y mostrar respuestas/permisos diferentes.

**Técnico:** intents, handlers, ReAct, memoria, tools, guardrails y documentación local.

## Telecomunicaciones

**Sencillo:** revisa paso a paso cómo está funcionando la conexión.

**Evidencia:** ejecutar diagnóstico online y en modo avión.

**Técnico:** DNS, TCP, TLS, RTT HTTP, P95, variación, fallos y goodput.

## Chaquopy

**Sencillo:** es el puente que permite usar Python dentro de Android.

**Evidencia:** la APK levanta Flask y SQLite dentro del teléfono sin servidor externo.

**Técnico:** runtime Python 3.10 embebido, ABI Android y loopback WebView–Flask.

## OSI

**Sencillo:** organiza la comunicación en siete niveles, como pisos de un edificio.

**Evidencia:** señalar qué observa el proyecto en cada nivel y qué no mide.

**Técnico:** aplicación, presentación, sesión, transporte, red, enlace y física.

## Seguridad

**Sencillo:** cada persona entra con su identidad y solo ve lo que corresponde a su función.

**Evidencia:** intentar entrar a una API de Desarrollador con otro rol.

**Técnico:** autorización, token de sesión, hashing, auditoría, SQLi/XSS y secretos fuera del código.

## Calidad

**Sencillo:** ningún cambio puede generar la APK hasta pasar la inspección automática.

**Evidencia:** workflow verde, tests, cobertura y checksum.

**Técnico:** pytest, coverage gate, smoke test y CI Android.

## Comandos IA

```text
explica fácil el proyecto
explica fácil la IA
explica telecom para el jurado
explica OSI sin tecnicismos
explica Chaquopy en palabras sencillas
explica seguridad para no ingenieros
explica las pruebas para el jurado
```

## Qué evitar

- listas interminables sin explicar el beneficio;
- siglas sin definir;
- presentar HTTP como ICMP;
- afirmar mediciones de radio no implementadas;
- decir que hay un LLM cuando es opcional;
- ocultar limitaciones;
- mostrar contraseñas o datos reales.
