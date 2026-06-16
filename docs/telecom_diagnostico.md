# 📡 Diagnóstico Telecom (v8.2)

Herramientas de diagnóstico REAL de red y telecomunicaciones para el rol **desarrollador**.

## Acceso

Solo el rol `desarrollador` puede invocar estas herramientas, tanto desde:
- Chat IA (preguntando en lenguaje natural)
- Menú: **Herramientas → Desarrollador → Diagnóstico Telecom**
- API REST: `/api/dev/telecom/*`

## Comandos del Chat

Desde el chat IA, el desarrollador puede preguntar:

| Pregunta | Acción |
|----------|--------|
| "diagnóstico completo" | Ejecuta TODOS los tests y muestra reporte |
| "mide la latencia" | 5 pings HTTP a Supabase + jitter |
| "throughput" | Mide velocidad de descarga real |
| "dns lookup" | Tiempo de resolución DNS |
| "tls handshake" | Tiempo handshake + certificado + cipher |
| "mi ip" | IP local, hostname, plataforma |
| "velocidad bd" | IOPS de SQLite local |

## API REST

Todos los endpoints requieren rol `desarrollador` (sesión activa).
