# -*- coding: utf-8 -*-
"""telecom_diag.py v8.2 - Diagnostico REAL de telecomunicaciones para la APK.

Herramientas que el desarrollador puede invocar desde el chat:
- Latencia real al servidor Supabase
- Throughput real de descarga
- Jitter (variacion de pings sucesivos)
- DNS lookup time
- TLS handshake time
- Informacion de red local (IP, gateway, DNS)
- Velocidad de la BD SQLite local (IOPS)
"""

import time
import socket
import statistics
import os
import sys
from urllib.parse import urlparse


def _supabase_url():
    """Obtiene la URL de Supabase configurada."""
    try:
        from sync.config_supabase import SUPABASE_CONFIG
        return SUPABASE_CONFIG.get("url", "")
    except Exception:
        return ""


def medir_latencia_supabase(intentos=5):
    """Mide latencia HTTP GET al endpoint /rest/v1/ de Supabase con API key."""
    url = _supabase_url()
    if not url:
        return {"ok": False, "error": "Supabase no configurado", "modo": "offline"}

    try:
        from sync.config_supabase import SUPABASE_CONFIG
        api_key = SUPABASE_CONFIG.get("anon_key", "")
    except Exception:
        api_key = ""

    if not api_key:
        return {"ok": False, "error": "Supabase API key no disponible"}

    try:
        import urllib.request
        test_url = url.rstrip('/') + "/rest/v1/"
        latencias = []
        errores = 0
        ultimo_error = ""
        for i in range(intentos):
            t0 = time.perf_counter()
            try:
                req = urllib.request.Request(test_url, method='GET')
                req.add_header('apikey', api_key)
                # Solo enviar Bearer si es JWT clasica (empieza con 'eyJ')
                if api_key.startswith('eyJ'):
                    req.add_header('Authorization', f'Bearer {api_key}')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read(100)  # leer poquito para medir RTT
                latencias.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                errores += 1
                ultimo_error = str(e)[:80]
            time.sleep(0.15)

        if not latencias:
            return {"ok": False,
                    "error": f"Todos los intentos fallaron. Ultimo: {ultimo_error}",
                    "intentos": intentos}

        return {
            "ok": True,
            "url": test_url,
            "intentos": intentos,
            "exitosos": len(latencias),
            "errores": errores,
            "latencia_min_ms": round(min(latencias), 2),
            "latencia_max_ms": round(max(latencias), 2),
            "latencia_media_ms": round(statistics.mean(latencias), 2),
            "latencia_mediana_ms": round(statistics.median(latencias), 2),
            "jitter_ms": round(statistics.stdev(latencias), 2) if len(latencias) > 1 else 0,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def medir_throughput_supabase(bytes_objetivo=100000):
    """Descarga del endpoint con API key y mide bytes/seg."""
    url = _supabase_url()
    if not url:
        return {"ok": False, "error": "Supabase no configurado"}

    try:
        from sync.config_supabase import SUPABASE_CONFIG
        api_key = SUPABASE_CONFIG.get("anon_key", "")
    except Exception:
        api_key = ""

    if not api_key:
        return {"ok": False, "error": "API key no disponible"}

    try:
        import urllib.request
        # Pedir lista de productos (con limit alto)
        test_url = url.rstrip('/') + "/rest/v1/productos?limit=1000"
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(test_url, method='GET')
            req.add_header('apikey', api_key)
            if api_key.startswith('eyJ'):
                req.add_header('Authorization', f'Bearer {api_key}')
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read(bytes_objetivo)
                elapsed = time.perf_counter() - t0
                bytes_recv = len(data)
        except Exception as e:
            return {"ok": False, "error": f"Descarga fallo: {str(e)[:100]}"}

        if elapsed <= 0:
            return {"ok": False, "error": "Tiempo invalido"}

        bps = bytes_recv / elapsed
        return {
            "ok": True,
            "url": test_url,
            "bytes_recibidos": bytes_recv,
            "tiempo_s": round(elapsed, 3),
            "throughput_bps": round(bps, 0),
            "throughput_kbps": round(bps / 1024, 2),
            "throughput_mbps": round(bps * 8 / 1_000_000, 3),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def medir_dns(host=None):
    """Mide tiempo de resolucion DNS."""
    if not host:
        url = _supabase_url()
        if url:
            host = urlparse(url).hostname
        else:
            host = "google.com"

    try:
        t0 = time.perf_counter()
        ip = socket.gethostbyname(host)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Obtener todas las IPs
        try:
            ips = list(set(addr[4][0] for addr in socket.getaddrinfo(host, None)))
        except Exception:
            ips = [ip]

        return {
            "ok": True,
            "host": host,
            "ip_principal": ip,
            "ips_resueltas": ips,
            "tiempo_ms": round(elapsed_ms, 2),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "host": host}


def medir_tls_handshake():
    """Mide tiempo de handshake TLS al servidor Supabase."""
    url = _supabase_url()
    if not url:
        return {"ok": False, "error": "Supabase no configurado"}

    try:
        import ssl
        host = urlparse(url).hostname
        port = 443

        t0 = time.perf_counter()
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            t_tcp = (time.perf_counter() - t0) * 1000
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                t_total = (time.perf_counter() - t0) * 1000
                cert = ssock.getpeercert()
                version = ssock.version()
                cipher = ssock.cipher()

        return {
            "ok": True,
            "host": host,
            "tiempo_tcp_ms": round(t_tcp, 2),
            "tiempo_total_ms": round(t_total, 2),
            "tiempo_tls_ms": round(t_total - t_tcp, 2),
            "tls_version": version,
            "cipher": cipher[0] if cipher else "?",
            "cipher_bits": cipher[2] if cipher else 0,
            "cert_subject": dict(x[0] for x in cert.get('subject', [])).get('commonName', '?'),
            "cert_issuer": dict(x[0] for x in cert.get('issuer', [])).get('commonName', '?'),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def info_red_local():
    """Obtiene IP local, hostname, interfaces."""
    try:
        hostname = socket.gethostname()
        # IP local (truco: conectar a 8.8.8.8 sin enviar nada)
        ip_local = "?"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            ip_local = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        return {
            "ok": True,
            "hostname": hostname,
            "ip_local": ip_local,
            "python": sys.version.split()[0],
            "plataforma": sys.platform,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def velocidad_sqlite():
    """Mide IOPS de la BD SQLite local."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()

        # Test de lectura: 100 SELECT 1
        t0 = time.perf_counter()
        for _ in range(100):
            conn.execute("SELECT 1").fetchone()
        t_read = (time.perf_counter() - t0) * 1000  # ms para 100 ops

        # Test de PRAGMA quick_check
        t0 = time.perf_counter()
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        t_check = (time.perf_counter() - t0) * 1000

        # Tamaño BD
        try:
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            size_kb = (page_count * page_size) / 1024
        except Exception:
            size_kb = 0

        conn.close()

        return {
            "ok": True,
            "lectura_100_ops_ms": round(t_read, 2),
            "ops_por_segundo": round(100 / (t_read / 1000), 0) if t_read > 0 else 0,
            "quick_check": quick,
            "quick_check_ms": round(t_check, 2),
            "tamano_kb": round(size_kb, 2),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def diagnostico_completo():
    """Ejecuta TODOS los diagnosticos y devuelve resumen."""
    return {
        "ok": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "red_local": info_red_local(),
        "dns": medir_dns(),
        "latencia": medir_latencia_supabase(intentos=3),
        "throughput": medir_throughput_supabase(),
        "tls": medir_tls_handshake(),
        "sqlite": velocidad_sqlite(),
    }


def formato_humano_diagnostico():
    """Devuelve string formateado del diagnostico completo."""
    d = diagnostico_completo()

    msg = "📡 **DIAGNÓSTICO TELECOM COMPLETO**\n\n"

    # Red local
    rl = d.get("red_local", {})
    if rl.get("ok"):
        msg += f"🖥️ **Dispositivo:**\n"
        msg += f"  • Hostname: {rl.get('hostname', '?')}\n"
        msg += f"  • IP local: {rl.get('ip_local', '?')}\n"
        msg += f"  • Plataforma: {rl.get('plataforma', '?')}\n\n"

    # DNS
    dns = d.get("dns", {})
    if dns.get("ok"):
        msg += f"🌐 **DNS:**\n"
        msg += f"  • Host: {dns.get('host', '?')}\n"
        msg += f"  • IP: {dns.get('ip_principal', '?')}\n"
        msg += f"  • Tiempo resolucion: {dns.get('tiempo_ms', 0)} ms\n\n"
    else:
        msg += f"🌐 **DNS:** ❌ {dns.get('error', 'error')}\n\n"

    # Latencia
    lat = d.get("latencia", {})
    if lat.get("ok"):
        msg += f"⚡ **Latencia Supabase:**\n"
        msg += f"  • Media: {lat.get('latencia_media_ms', 0)} ms\n"
        msg += f"  • Min/Max: {lat.get('latencia_min_ms', 0)} / {lat.get('latencia_max_ms', 0)} ms\n"
        msg += f"  • Jitter: {lat.get('jitter_ms', 0)} ms\n"
        msg += f"  • Exitosos: {lat.get('exitosos', 0)}/{lat.get('intentos', 0)}\n\n"
    else:
        msg += f"⚡ **Latencia:** ❌ {lat.get('error', 'error')}\n\n"

    # Throughput
    th = d.get("throughput", {})
    if th.get("ok"):
        msg += f"📥 **Throughput:**\n"
        msg += f"  • {th.get('throughput_kbps', 0)} KB/s\n"
        msg += f"  • {th.get('throughput_mbps', 0)} Mbps\n\n"
    else:
        msg += f"📥 **Throughput:** ❌ {th.get('error', 'error')}\n\n"

    # TLS
    tls = d.get("tls", {})
    if tls.get("ok"):
        msg += f"🔒 **TLS Handshake:**\n"
        msg += f"  • Version: {tls.get('tls_version', '?')}\n"
        msg += f"  • Cipher: {tls.get('cipher', '?')} ({tls.get('cipher_bits', 0)} bits)\n"
        msg += f"  • TCP: {tls.get('tiempo_tcp_ms', 0)} ms | TLS: {tls.get('tiempo_tls_ms', 0)} ms\n"
        msg += f"  • Cert: {tls.get('cert_subject', '?')} (CA: {tls.get('cert_issuer', '?')})\n\n"
    else:
        msg += f"🔒 **TLS:** ❌ {tls.get('error', 'error')}\n\n"

    # SQLite
    sq = d.get("sqlite", {})
    if sq.get("ok"):
        msg += f"💾 **SQLite Local:**\n"
        msg += f"  • Integridad: {sq.get('quick_check', '?').upper()}\n"
        msg += f"  • Lectura: {sq.get('ops_por_segundo', 0)} ops/s\n"
        msg += f"  • Tamaño: {sq.get('tamano_kb', 0)} KB\n\n"

    msg += f"⏱️ {d.get('timestamp', '?')}"
    return msg
