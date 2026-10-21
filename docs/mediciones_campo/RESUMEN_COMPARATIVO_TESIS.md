# Comparativa Experimental Multi-Escenario (Wi-Fi vs Datos Móviles / Referencia)

| Escenario | Host / IP | TCP (ms) | TLS (ms) | HTTPS Frío (ms) | HTTPS Keep-Alive (ms) | Jitter RFC3550 (ms) | Mejora Keep-Alive | SQLite Local (ops/s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `lte_datos_moviles` | `104.16.132.229` | 7.52 | 492.38 | 835.22 | 222.14 | 14.17 | -73.4% | 32734 |
| `servidor_referencia_https` | `104.16.133.229` | 2.09 | 19.69 | 73.91 | 11.81 | 0.67 | -84.0% | 352922 |
| `wifi_wlan0` | `104.16.133.229` | 7.71 | 482.21 | 866.48 | 239.98 | 34.26 | -72.3% | 34946 |

### Campaña experimental: `lte_datos_moviles` (2026-10-21T08:27:46.151980+00:00)
- **Endpoint medido**: `https://cloudflare.com/cdn-cgi/trace` (`104.16.132.229`)
- **Seguridad negociada**: `TLSv1.3` — `TLS_AES_256_GCM_SHA384 (256 bits)`
- **Reducción de RTT por reutilización TLS Keep-Alive**: **73.4%**
- **Calificación enlace (criterio TPV)**: **DEGRADADA (70/100)** | Pérdida muestral: `0.0%`
- **Plano local SQLite (WAL)**: `3.05 ms` por 100 lecturas (`32734 ops/s`), `quick_check=ok`

| Capa / Métrica experimental | N | Media ± IC95% (ms) | Mediana (ms) | P95 (ms) | Desv. Est. σ (ms) | Jitter RFC 3550 (ms) | Mín–Máx (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Resolución DNS (`getaddrinfo`) | 20 | 16.88 ± 20.63 | 6.43 | 18.56 | 47.08 | 12.27 | 4.96–216.85 |
| Transporte TCP (`SYN/SYN-ACK`) | 20 | 7.52 ± 0.91 | 7.21 | 9.64 | 2.07 | 1.89 | 5.03–15.09 |
| Negociación criptográfica TLS | 20 | 492.38 ± 20.32 | 476.55 | 589.44 | 46.37 | 48.96 | 448.33–611.18 |
| Petición HTTPS en frío (TCP+TLS+HTTP) | 20 | 835.22 ± 47.22 | 894.64 | 952.51 | 107.74 | 173.71 | 680.20–968.15 |
| Petición HTTPS Keep-Alive (1 RTT) | 20 | 222.14 ± 5.32 | 219.49 | 240.81 | 12.14 | 14.17 | 204.45–242.87 |

### Campaña experimental: `servidor_referencia_https` (2026-10-21T08:05:25.012253+00:00)
- **Endpoint medido**: `https://cloudflare.com/cdn-cgi/trace` (`104.16.133.229`)
- **Seguridad negociada**: `TLSv1.3` — `TLS_AES_256_GCM_SHA384 (256 bits)`
- **Reducción de RTT por reutilización TLS Keep-Alive**: **84.0%**
- **Calificación enlace (criterio TPV)**: **EXCELENTE (100/100)** | Pérdida muestral: `0.0%`
- **Plano local SQLite (WAL)**: `0.28 ms` por 100 lecturas (`352922 ops/s`), `quick_check=ok`

| Capa / Métrica experimental | N | Media ± IC95% (ms) | Mediana (ms) | P95 (ms) | Desv. Est. σ (ms) | Jitter RFC 3550 (ms) | Mín–Máx (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Resolución DNS (`getaddrinfo`) | 15 | 5.22 ± 2.20 | 1.95 | 11.46 | 4.34 | 1.95 | 1.52–11.73 |
| Transporte TCP (`SYN/SYN-ACK`) | 15 | 2.09 ± 0.17 | 2.05 | 2.69 | 0.34 | 0.44 | 1.67–2.97 |
| Negociación criptográfica TLS | 15 | 19.69 ± 1.08 | 19.39 | 23.60 | 2.14 | 2.28 | 16.88–23.78 |
| Petición HTTPS en frío (TCP+TLS+HTTP) | 15 | 73.91 ± 1.66 | 73.39 | 79.36 | 3.28 | 3.58 | 69.49–80.75 |
| Petición HTTPS Keep-Alive (1 RTT) | 15 | 11.81 ± 0.35 | 11.56 | 12.90 | 0.69 | 0.67 | 11.06–13.17 |

### Campaña experimental: `wifi_wlan0` (2026-10-21T08:26:17.501785+00:00)
- **Endpoint medido**: `https://cloudflare.com/cdn-cgi/trace` (`104.16.133.229`)
- **Seguridad negociada**: `TLSv1.3` — `TLS_AES_256_GCM_SHA384 (256 bits)`
- **Reducción de RTT por reutilización TLS Keep-Alive**: **72.3%**
- **Calificación enlace (criterio TPV)**: **DEGRADADA (60/100)** | Pérdida muestral: `0.0%`
- **Plano local SQLite (WAL)**: `2.86 ms` por 100 lecturas (`34946 ops/s`), `quick_check=ok`

| Capa / Métrica experimental | N | Media ± IC95% (ms) | Mediana (ms) | P95 (ms) | Desv. Est. σ (ms) | Jitter RFC 3550 (ms) | Mín–Máx (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Resolución DNS (`getaddrinfo`) | 20 | 17.56 ± 22.86 | 6.07 | 18.65 | 52.16 | 12.89 | 4.60–239.16 |
| Transporte TCP (`SYN/SYN-ACK`) | 20 | 7.71 ± 1.17 | 7.16 | 13.37 | 2.67 | 1.51 | 4.50–16.67 |
| Negociación criptográfica TLS | 20 | 482.21 ± 8.01 | 480.24 | 510.67 | 18.27 | 17.40 | 449.49–513.76 |
| Petición HTTPS en frío (TCP+TLS+HTTP) | 20 | 866.48 ± 48.98 | 921.81 | 960.59 | 111.76 | 134.46 | 695.50–1098.70 |
| Petición HTTPS Keep-Alive (1 RTT) | 20 | 239.98 ± 16.09 | 229.74 | 331.58 | 36.72 | 34.26 | 206.49–342.38 |
