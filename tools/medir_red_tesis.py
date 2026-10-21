#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Herramienta reproducible de telemetría por capas para Termux / Android.

Ejecuta N repeticiones por capa (DNS, TCP connect, handshake TLS 1.3, RTT HTTPS
en frío vs. RTT HTTPS persistente Keep-Alive, jitter desviación estándar y
jitter consecutivo RFC 3550 / IPDV, más plano local SQLite) y genera tablas
listas en Markdown + JSON auditable para incorporar directamente al Capítulo 3
del Trabajo de Grado (IEEE).

Uso en Termux (primero conectado a Wi-Fi, luego en Datos Móviles 4G/LTE):
    python tools/medir_red_tesis.py --etiqueta wifi_wlan0 --muestras 20
    python tools/medir_red_tesis.py --etiqueta lte_datos_moviles --muestras 20
    python tools/medir_red_tesis.py --comparar
"""
from __future__ import annotations

import argparse
import http.client
import json
import math
import os
import socket
import ssl
import statistics
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_APP_DIR = os.path.join(ROOT_DIR, "app", "src", "main", "python")
if PY_APP_DIR not in sys.path:
    sys.path.insert(0, PY_APP_DIR)

OUT_DIR = os.path.join(ROOT_DIR, "docs", "mediciones_campo")


def _pct(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _ipdv_rfc3550(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    return sum(abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))) / (len(vals) - 1)


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0, "media_ms": 0.0, "mediana_ms": 0.0, "sd_ms": 0.0, "ipdv_ms": 0.0, "p95_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    n = len(vals)
    ci95 = 1.96 * (sd / math.sqrt(n)) if n > 1 else 0.0
    return {
        "n": n,
        "media_ms": round(statistics.mean(vals), 2),
        "ic95_pm_ms": round(ci95, 2),
        "mediana_ms": round(statistics.median(vals), 2),
        "sd_ms": round(sd, 2),
        "ipdv_rfc3550_ms": round(_ipdv_rfc3550(vals), 2),
        "p95_ms": round(_pct(vals, 0.95), 2),
        "min_ms": round(min(vals), 2),
        "max_ms": round(max(vals), 2),
    }


def ejecutar_campana(etiqueta: str, endpoint_url: str, muestras: int = 20, timeout: float = 6.0) -> dict:
    parsed = urlparse(endpoint_url)
    host = parsed.hostname or "cloudflare.com"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/cdn-cgi/trace"

    dns_ms: list[float] = []
    tcp_ms: list[float] = []
    tls_ms: list[float] = []
    cold_https_ms: list[float] = []
    warm_keepalive_ms: list[float] = []
    errores_red = 0
    tls_proto = "N/D"
    tls_cipher = "N/D"
    resolved_ip = "N/D"

    # 1. Resolución DNS (N muestras)
    for _ in range(muestras):
        t0 = time.perf_counter()
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            dns_ms.append((time.perf_counter() - t0) * 1000)
            if infos:
                resolved_ip = infos[0][4][0]
        except Exception:
            errores_red += 1
        time.sleep(0.03)

    # 2. Handshake TCP + TLS separado y petición HTTPS en frío (conexión nueva por muestra)
    ctx = ssl.create_default_context()
    for _ in range(muestras):
        t_start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout) as raw_sock:
                t_tcp = (time.perf_counter() - t_start) * 1000
                with ctx.wrap_socket(raw_sock, server_hostname=host) as tls_sock:
                    t_tls_done = (time.perf_counter() - t_start) * 1000
                    tls_proto = tls_sock.version() or tls_proto
                    cinfo = tls_sock.cipher()
                    if cinfo:
                        tls_cipher = f"{cinfo[0]} ({cinfo[2]} bits)"
                    req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\nUser-Agent: TPV-Thesis-Audit/1.0\r\n\r\n".encode("ascii")
                    tls_sock.sendall(req)
                    tls_sock.recv(512)
                    t_http_done = (time.perf_counter() - t_start) * 1000
                tcp_ms.append(t_tcp)
                tls_ms.append(t_tls_done - t_tcp)
                cold_https_ms.append(t_http_done)
        except Exception:
            errores_red += 1
        time.sleep(0.05)

    # 3. Sesión persistente HTTP/1.1 Keep-Alive (1 warm-up + N muestras estables de 1 RTT)
    conn = http.client.HTTPSConnection(host, port=port, timeout=timeout, context=ctx)
    try:
        conn.request("GET", path, headers={"Connection": "keep-alive", "User-Agent": "TPV-Thesis-Audit/1.0"})
        conn.getresponse().read()
        for _ in range(muestras):
            t0 = time.perf_counter()
            try:
                conn.request("GET", path, headers={"Connection": "keep-alive", "User-Agent": "TPV-Thesis-Audit/1.0"})
                conn.getresponse().read()
                warm_keepalive_ms.append((time.perf_counter() - t0) * 1000)
            except Exception:
                errores_red += 1
                conn.close()
            time.sleep(0.04)
    except Exception:
        errores_red += 1
    finally:
        conn.close()

    # 4. Plano local SQLite (desacoplamiento offline-first en directorio aislado)
    import tempfile
    _tmp_dir_ctx = None
    if not os.environ.get("TPV_FILES_DIR"):
        _tmp_dir_ctx = tempfile.TemporaryDirectory(prefix="tpv_bench_")
        os.environ["TPV_FILES_DIR"] = _tmp_dir_ctx.name

    try:
        from modules.telecom_diag import evaluar_calidad, info_red_local, velocidad_sqlite
        import database

        database.crear_tablas()
        sqlite_res = velocidad_sqlite()
        local_info = info_red_local()
    finally:
        if _tmp_dir_ctx is not None:
            _tmp_dir_ctx.cleanup()
    warm_stats = _stats(warm_keepalive_ms)
    cold_stats = _stats(cold_https_ms)
    perdida_pct = round((errores_red / max(1, muestras * 3)) * 100, 2)

    ahorro_pct = 0.0
    if cold_stats["media_ms"] > 0 and warm_stats["media_ms"] > 0:
        ahorro_pct = round((1.0 - warm_stats["media_ms"] / cold_stats["media_ms"]) * 100, 1)

    report = {
        "etiqueta": etiqueta,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint_url,
        "host": host,
        "ip_resuelta": resolved_ip,
        "muestras_por_capa": muestras,
        "endpoint_local": local_info,
        "tls_negociado": {"protocolo": tls_proto, "cipher": tls_cipher},
        "capas": {
            "dns_getaddrinfo": _stats(dns_ms),
            "tcp_handshake_syn_ack": _stats(tcp_ms),
            "tls_handshake": _stats(tls_ms),
            "https_frio_sin_reuso": cold_stats,
            "https_keepalive_1rtt": warm_stats,
        },
        "reduccion_latencia_keepalive_pct": ahorro_pct,
        "perdida_muestral_pct": perdida_pct,
        "calidad_enlace_keepalive": evaluar_calidad(
            warm_stats["media_ms"], warm_stats["sd_ms"], perdida_pct
        ),
        "plano_local_sqlite": sqlite_res,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    json_path = os.path.join(OUT_DIR, f"medicion_{etiqueta}.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    return report


def formatear_tabla_markdown(rep: dict) -> str:
    c = rep["capas"]
    sq = rep["plano_local_sqlite"]
    cal = rep["calidad_enlace_keepalive"]
    lines = [
        f"### Campaña experimental: `{rep['etiqueta']}` ({rep['timestamp_utc']})",
        f"- **Endpoint medido**: `{rep['endpoint']}` (`{rep['ip_resuelta']}`)",
        f"- **Seguridad negociada**: `{rep['tls_negociado']['protocolo']}` — `{rep['tls_negociado']['cipher']}`",
        f"- **Reducción de RTT por reutilización TLS Keep-Alive**: **{rep['reduccion_latencia_keepalive_pct']}%**",
        f"- **Calificación enlace (criterio TPV)**: **{cal['nivel'].upper()} ({cal['score']}/100)** | Pérdida muestral: `{rep['perdida_muestral_pct']}%`",
        f"- **Plano local SQLite (WAL)**: `{sq.get('lectura_100_ops_ms', 0)} ms` por 100 lecturas (`{sq.get('ops_por_segundo', 0):.0f} ops/s`), `quick_check={sq.get('quick_check')}`",
        "",
        "| Capa / Métrica experimental | N | Media ± IC95% (ms) | Mediana (ms) | P95 (ms) | Desv. Est. σ (ms) | Jitter RFC 3550 (ms) | Mín–Máx (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    nombres = [
        ("Resolución DNS (`getaddrinfo`)", "dns_getaddrinfo"),
        ("Transporte TCP (`SYN/SYN-ACK`)", "tcp_handshake_syn_ack"),
        ("Negociación criptográfica TLS", "tls_handshake"),
        ("Petición HTTPS en frío (TCP+TLS+HTTP)", "https_frio_sin_reuso"),
        ("Petición HTTPS Keep-Alive (1 RTT)", "https_keepalive_1rtt"),
    ]
    for label, key in nombres:
        s = c[key]
        lines.append(
            f"| {label} | {s['n']} | {s['media_ms']:.2f} ± {s.get('ic95_pm_ms', 0):.2f} | "
            f"{s['mediana_ms']:.2f} | {s['p95_ms']:.2f} | {s['sd_ms']:.2f} | "
            f"{s.get('ipdv_rfc3550_ms', 0):.2f} | {s['min_ms']:.2f}–{s['max_ms']:.2f} |"
        )
    return "\n".join(lines) + "\n"


def comparar_campanas() -> str:
    if not os.path.isdir(OUT_DIR):
        return "No hay campañas guardadas aún en docs/mediciones_campo/."
    archivos = sorted(f for f in os.listdir(OUT_DIR) if f.startswith("medicion_") and f.endswith(".json"))
    bloques = ["# Comparativa Experimental Multi-Escenario (Wi-Fi vs Datos Móviles / Referencia)\n"]
    resumen_rows = [
        "| Escenario | Host / IP | TCP (ms) | TLS (ms) | HTTPS Frío (ms) | HTTPS Keep-Alive (ms) | Jitter RFC3550 (ms) | Mejora Keep-Alive | SQLite Local (ops/s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fn in archivos:
        with open(os.path.join(OUT_DIR, fn), "r", encoding="utf-8") as fh:
            r = json.load(fh)
        bloques.append(formatear_tabla_markdown(r))
        c = r["capas"]
        resumen_rows.append(
            f"| `{r['etiqueta']}` | `{r['ip_resuelta']}` | "
            f"{c['tcp_handshake_syn_ack']['media_ms']:.2f} | "
            f"{c['tls_handshake']['media_ms']:.2f} | "
            f"{c['https_frio_sin_reuso']['media_ms']:.2f} | "
            f"{c['https_keepalive_1rtt']['media_ms']:.2f} | "
            f"{c['https_keepalive_1rtt']['ipdv_rfc3550_ms']:.2f} | "
            f"-{r['reduccion_latencia_keepalive_pct']:.1f}% | "
            f"{r['plano_local_sqlite'].get('ops_por_segundo', 0):.0f} |"
        )
    salida = "\n".join([bloques[0], "\n".join(resumen_rows), ""] + bloques[1:])
    md_path = os.path.join(OUT_DIR, "RESUMEN_COMPARATIVO_TESIS.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(salida)
    return salida


def main() -> int:
    parser = argparse.ArgumentParser(description=" Campaña experimental de telemetría TPV Ultra Smart")
    parser.add_argument("--etiqueta", default="referencia_actual", help="Nombre del escenario (ej. wifi_wlan0, lte_4g)")
    parser.add_argument("--url", default="https://cloudflare.com/cdn-cgi/trace", help="Endpoint HTTPS de referencia")
    parser.add_argument("--muestras", type=int, default=15, help="Muestras por capa (por defecto 15)")
    parser.add_argument("--comparar", action="store_true", help="Genera tabla comparativa de todas las campañas guardadas")
    args = parser.parse_args()

    if args.comparar:
        print(comparar_campanas())
        return 0

    rep = ejecutar_campana(args.etiqueta, args.url, muestras=max(3, min(args.muestras, 50)))
    md = formatear_tabla_markdown(rep)
    print(md)
    comparar_campanas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
