# -*- coding: utf-8 -*-
"""Reproducible telecommunications diagnostics for the developer role.

Measurements are explicitly labelled by layer and method. Network tests use the
configured Supabase endpoint (or explicit probe URL when requested); they never
claim to be ICMP when the sample is an HTTP application RTT. Supports both standard
per-request HTTPS RTT and persistent HTTP Keep-Alive RTT plus RFC 3550 consecutive
inter-packet delay variation (IPDV / jitter).
"""
from __future__ import annotations

import http.client
import math
import os
import socket
import ssl
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


def _supabase_config() -> dict:
    try:
        from sync.config_supabase import SUPABASE_CONFIG

        cfg = dict(SUPABASE_CONFIG or {})
        if cfg.get("url") and "REMOVED" not in str(cfg.get("anon_key", "")):
            return cfg
    except Exception:
        pass
    try:
        import supabase_sync

        cfg = dict(getattr(supabase_sync, "SUPABASE_CONFIG", {}) or {})
        if cfg.get("url") and "REMOVED" not in str(cfg.get("anon_key", "")):
            return cfg
    except Exception:
        pass
    return {}


def _supabase_url() -> str:
    return str(_supabase_config().get("url", "")).strip()


def _percentile(values: list[float], percentile: float) -> float:
    """Linear-interpolated percentile without third-party dependencies."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _jitter_rfc3550(samples: list[float]) -> float:
    """Mean consecutive absolute delay variation |L_i - L_{i-1}| (RFC 3550 / ITU-T)."""
    if len(samples) < 2:
        return 0.0
    diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
    return sum(diffs) / len(diffs)


def evaluar_calidad(latencia_ms: float | None, jitter_ms: float | None, perdida_pct: float | None) -> dict:
    """Classify an interactive data link using documented project thresholds."""
    if latencia_ms is None or jitter_ms is None or perdida_pct is None:
        return {"nivel": "sin_datos", "score": 0, "apta_tpv": False}
    score = 100
    if latencia_ms > 300:
        score -= 45
    elif latencia_ms > 150:
        score -= 25
    elif latencia_ms > 80:
        score -= 10
    if jitter_ms > 50:
        score -= 30
    elif jitter_ms > 25:
        score -= 15
    elif jitter_ms > 10:
        score -= 5
    if perdida_pct > 5:
        score -= 40
    elif perdida_pct > 2:
        score -= 20
    elif perdida_pct > 0:
        score -= 5
    score = max(0, score)
    level = "excelente" if score >= 90 else "buena" if score >= 75 else "degradada" if score >= 50 else "critica"
    return {"nivel": level, "score": score, "apta_tpv": score >= 50}


def medir_latencia_supabase(
    intentos: int = 5,
    timeout: float = 5.0,
    keepalive: bool = False,
) -> dict:
    """Measure application-layer HTTP RTT, RFC 3550 jitter and failed-sample ratio."""
    attempts = max(1, min(int(intentos), 10))
    url = _supabase_url()
    config = _supabase_config()
    api_key = str(config.get("anon_key", ""))
    if not url:
        return {"ok": False, "error": "Supabase no configurado", "modo": "offline", "metodo": "HTTP RTT"}
    if not api_key:
        return {"ok": False, "error": "Supabase API key no disponible", "metodo": "HTTP RTT"}

    test_url = url.rstrip("/") + "/rest/v1/"
    headers = {"apikey": api_key, "Connection": "keep-alive"}
    if api_key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {api_key}"

    samples: list[float] = []
    errors: list[str] = []

    if keepalive:
        parsed = urlparse(test_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        conn_http = None
        try:
            ctx = ssl.create_default_context()
            conn_http = (
                http.client.HTTPSConnection(host, port=port, timeout=timeout, context=ctx)
                if parsed.scheme == "https"
                else http.client.HTTPConnection(host, port=port, timeout=timeout)
            )
            for index in range(attempts):
                started = time.perf_counter()
                try:
                    conn_http.request("GET", path, headers=headers)
                    resp = conn_http.getresponse()
                    resp.read()
                    samples.append((time.perf_counter() - started) * 1000)
                except Exception as exc:
                    errors.append(f"{type(exc).__name__}: {exc}"[:120])
                    try:
                        conn_http.close()
                    except Exception:
                        pass
                if index + 1 < attempts:
                    time.sleep(0.05)
        finally:
            if conn_http is not None:
                try:
                    conn_http.close()
                except Exception:
                    pass
    else:
        for index in range(attempts):
            started = time.perf_counter()
            try:
                request = urllib.request.Request(test_url, method="GET")
                for hk, hv in headers.items():
                    request.add_header(hk, hv)
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    response.read(128)
                samples.append((time.perf_counter() - started) * 1000)
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}"[:120])
            if index + 1 < attempts:
                time.sleep(0.05)

    failed = attempts - len(samples)
    loss = failed / attempts * 100
    if not samples:
        return {
            "ok": False, "error": "Todos los intentos HTTP fallaron",
            "ultimo_error": errors[-1] if errors else "desconocido",
            "intentos": attempts, "exitosos": 0, "perdida_pct": 100.0,
            "metodo": "HTTP application RTT (no ICMP)",
        }

    mean = statistics.mean(samples)
    jitter_sd = statistics.stdev(samples) if len(samples) > 1 else 0.0
    jitter_ipdv = _jitter_rfc3550(samples)
    warm_samples = samples[1:] if len(samples) > 1 else samples
    warm_mean = statistics.mean(warm_samples)
    warm_jitter = statistics.stdev(warm_samples) if len(warm_samples) > 1 else jitter_sd
    return {
        "ok": True,
        "url": test_url,
        "metodo": "HTTP Keep-Alive RTT (no ICMP)" if keepalive else "HTTP application RTT (no ICMP)",
        "unidad": "ms",
        "intentos": attempts,
        "exitosos": len(samples),
        "errores": failed,
        "perdida_pct": round(loss, 2),
        "latencia_min_ms": round(min(samples), 2),
        "latencia_max_ms": round(max(samples), 2),
        "latencia_media_ms": round(mean, 2),
        "latencia_warm_ms": round(warm_mean, 2),
        "latencia_mediana_ms": round(statistics.median(samples), 2),
        "latencia_p95_ms": round(_percentile(samples, 0.95), 2),
        "jitter_ms": round(jitter_sd, 2),
        "jitter_rfc3550_ms": round(jitter_ipdv, 2),
        "muestras_ms": [round(value, 2) for value in samples],
        "calidad": evaluar_calidad(
            warm_mean if keepalive else mean,
            warm_jitter if keepalive else jitter_sd,
            loss,
        ),
    }


def medir_throughput_supabase(bytes_objetivo: int = 100_000, timeout: float = 15.0) -> dict:
    """Measure goodput from a bounded HTTP response sample."""
    target = max(1_024, min(int(bytes_objetivo), 1_000_000))
    config = _supabase_config()
    url = str(config.get("url", ""))
    api_key = str(config.get("anon_key", ""))
    if not url:
        return {"ok": False, "error": "Supabase no configurado", "metodo": "HTTP goodput"}
    if not api_key:
        return {"ok": False, "error": "API key no disponible", "metodo": "HTTP goodput"}

    test_url = url.rstrip("/") + "/rest/v1/productos?limit=1000"
    request = urllib.request.Request(test_url, method="GET")
    request.add_header("apikey", api_key)
    if api_key.startswith("eyJ"):
        request.add_header("Authorization", f"Bearer {api_key}")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(target)
    except Exception as exc:
        return {"ok": False, "error": f"Descarga falló: {type(exc).__name__}: {exc}"[:160], "metodo": "HTTP goodput"}
    elapsed = time.perf_counter() - started
    if elapsed <= 0:
        return {"ok": False, "error": "Tiempo inválido", "metodo": "HTTP goodput"}

    received = len(data)
    bytes_per_second = received / elapsed
    return {
        "ok": True,
        "url": test_url,
        "metodo": "HTTP application goodput",
        "limitacion": "Muestra acotada; no representa capacidad física del enlace",
        "bytes_objetivo": target,
        "bytes_recibidos": received,
        "tiempo_s": round(elapsed, 4),
        "bytes_por_segundo": round(bytes_per_second, 2),
        "throughput_kib_s": round(bytes_per_second / 1024, 2),
        "throughput_kbps": round(bytes_per_second * 8 / 1000, 2),
        "throughput_mbps": round(bytes_per_second * 8 / 1_000_000, 3),
    }


def medir_dns(host: str | None = None) -> dict:
    """Measure resolver time and return unique addresses."""
    if not host:
        host = urlparse(_supabase_url()).hostname or "example.com"
    host = str(host).strip().rstrip(".")
    if not host or len(host) > 253 or any(character in host for character in "/?#@"):
        return {"ok": False, "error": "Host DNS inválido", "host": host}
    started = time.perf_counter()
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
        elapsed = (time.perf_counter() - started) * 1000
        if not addresses:
            raise socket.gaierror("sin direcciones")
        return {
            "ok": True, "host": host, "ip_principal": addresses[0],
            "ips_resueltas": addresses, "tiempo_ms": round(elapsed, 2),
            "metodo": "getaddrinfo", "unidad": "ms",
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "host": host, "metodo": "getaddrinfo"}


def medir_tls_handshake(timeout: float = 5.0, host_override: str | None = None) -> dict:
    """Measure TCP connect plus TLS negotiation to target host."""
    host = (host_override or urlparse(_supabase_url()).hostname or "").strip()
    if not host:
        return {"ok": False, "error": "Supabase no configurado", "metodo": "TCP + TLS"}
    started = time.perf_counter()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as raw_socket:
            tcp_ms = (time.perf_counter() - started) * 1000
            with context.wrap_socket(raw_socket, server_hostname=host) as tls_socket:
                total_ms = (time.perf_counter() - started) * 1000
                certificate = tls_socket.getpeercert()
                cipher = tls_socket.cipher()
                version = tls_socket.version()
        subject = dict(item[0] for item in certificate.get("subject", []))
        issuer = dict(item[0] for item in certificate.get("issuer", []))
        return {
            "ok": True, "host": host, "puerto": 443, "metodo": "TCP connect + TLS handshake",
            "tiempo_tcp_ms": round(tcp_ms, 2), "tiempo_total_ms": round(total_ms, 2),
            "tiempo_tls_ms": round(total_ms - tcp_ms, 2), "tls_version": version,
            "cipher": cipher[0] if cipher else "?", "cipher_bits": cipher[2] if cipher else 0,
            "cert_subject": subject.get("commonName", "?"),
            "cert_issuer": issuer.get("commonName", "?"),
            "cert_not_before": certificate.get("notBefore"), "cert_not_after": certificate.get("notAfter"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "host": host, "metodo": "TCP + TLS"}


def info_red_local() -> dict:
    """Return local endpoint information without requiring Internet access."""
    try:
        hostname = socket.gethostname()
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None)})
    except Exception:
        hostname, addresses = "?", []
    local_ip = next((address for address in addresses if ":" not in address and not address.startswith("127.")), "?")
    probe = None
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.settimeout(0.5)
        probe.connect(("8.8.8.8", 80))
        local_ip = probe.getsockname()[0]
    except Exception:
        pass
    finally:
        if probe is not None:
            probe.close()
    return {
        "ok": True, "hostname": hostname, "ip_local": local_ip,
        "direcciones_locales": addresses, "python": sys.version.split()[0],
        "plataforma": sys.platform, "modo": "información de endpoint local",
    }


def velocidad_sqlite() -> dict:
    """Measure local SQLite read rate and quick integrity check."""
    from db_connection import obtener_conexion

    connection = obtener_conexion()
    try:
        started = time.perf_counter()
        for _ in range(100):
            connection.execute("SELECT 1").fetchone()
        read_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        check_ms = (time.perf_counter() - started) * 1000
        page_count = connection.execute("PRAGMA page_count").fetchone()[0]
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        return {
            "ok": True, "metodo": "100 x SELECT 1 + PRAGMA quick_check",
            "lectura_100_ops_ms": round(read_ms, 2),
            "ops_por_segundo": round(100 / (read_ms / 1000), 0) if read_ms > 0 else 0,
            "quick_check": quick_check, "quick_check_ms": round(check_ms, 2),
            "tamano_kb": round(page_count * page_size / 1024, 2),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        connection.close()


def diagnostico_completo() -> dict:
    """Run the complete layered telecommunications diagnostic (5 RTT attempts)."""
    local = info_red_local()
    dns = medir_dns()
    latency = medir_latencia_supabase(intentos=5)
    throughput = medir_throughput_supabase()
    tls = medir_tls_handshake()
    sqlite = velocidad_sqlite()
    successful = sum(bool(section.get("ok")) for section in (local, dns, latency, throughput, tls, sqlite))
    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metodologia": "mediciones end-to-end por capas; sin afirmar ICMP ni capacidad física",
        "pruebas_exitosas": successful,
        "pruebas_totales": 6,
        "modo_offline": not bool(_supabase_url()),
        "red_local": local, "dns": dns, "latencia": latency,
        "throughput": throughput, "tls": tls, "sqlite": sqlite,
    }


def formato_humano_diagnostico() -> str:
    """Format the complete diagnostic for IA chat and academic demonstrations."""
    result = diagnostico_completo()
    local, dns, latency = result["red_local"], result["dns"], result["latencia"]
    throughput, tls, sqlite = result["throughput"], result["tls"], result["sqlite"]
    lines = [
        "DIAGNÓSTICO TELECOM POR CAPAS",
        f"Fecha UTC: {result['timestamp']}",
        f"Pruebas disponibles: {result['pruebas_exitosas']}/{result['pruebas_totales']}",
        "",
        "CAPA DE RED / ENDPOINT",
        f"  Host: {local.get('hostname', '?')} | IP local: {local.get('ip_local', '?')}",
        "",
        "RESOLUCIÓN DNS",
        f"  {dns.get('host', '?')}: {dns.get('tiempo_ms', 'N/D')} ms | {dns.get('ip_principal', dns.get('error', 'N/D'))}",
        "",
        "SERVICIO HTTP (RTT, NO ICMP)",
    ]
    if latency.get("ok"):
        lines.extend([
            f"  Media: {latency['latencia_media_ms']} ms | P95: {latency['latencia_p95_ms']} ms",
            f"  Jitter σ: {latency['jitter_ms']} ms | Jitter RFC3550: {latency.get('jitter_rfc3550_ms', 0)} ms | Fallos: {latency['perdida_pct']}%",
            f"  Calidad: {latency['calidad']['nivel']} ({latency['calidad']['score']}/100)",
        ])
    else:
        lines.append(f"  No disponible: {latency.get('error', 'error')}")
    lines.extend(["", "GOODPUT HTTP"])
    if throughput.get("ok"):
        lines.append(f"  {throughput['throughput_mbps']} Mbps ({throughput['throughput_kib_s']} KiB/s)")
        lines.append(f"  Nota: {throughput['limitacion']}")
    else:
        lines.append(f"  No disponible: {throughput.get('error', 'error')}")
    lines.extend(["", "SEGURIDAD TLS"])
    if tls.get("ok"):
        lines.append(f"  {tls['tls_version']} | {tls['cipher']} ({tls['cipher_bits']} bits)")
        lines.append(f"  TCP: {tls['tiempo_tcp_ms']} ms | TLS: {tls['tiempo_tls_ms']} ms")
    else:
        lines.append(f"  No disponible: {tls.get('error', 'error')}")
    lines.extend([
        "", "PLANO LOCAL SQLITE",
        f"  Integridad: {str(sqlite.get('quick_check', sqlite.get('error', '?'))).upper()}",
        f"  Lecturas: {sqlite.get('ops_por_segundo', 0)} ops/s | Tamaño: {sqlite.get('tamano_kb', 0)} KiB",
        "", "Metodología: medición end-to-end reproducible; los resultados dependen del servidor, radio, red y carga.",
    ])
    return "\n".join(lines)
