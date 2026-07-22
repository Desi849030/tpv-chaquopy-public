"""Developer-only telecommunications diagnostic API."""
from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request, session

from modules import telecom_diag

telecom_bp = Blueprint("telecom_dev", __name__)


def _dev_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = session.get("usuario") or {}
        if user.get("rol") != "desarrollador":
            return jsonify({"ok": False, "error": "Solo desarrollador"}), 403
        return function(*args, **kwargs)
    return wrapper


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


@telecom_bp.get("/api/dev/telecom/latencia")
@_dev_required
def api_latencia():
    return jsonify(telecom_diag.medir_latencia_supabase(
        intentos=_bounded_int("intentos", 5, 1, 10)
    ))


@telecom_bp.get("/api/dev/telecom/throughput")
@_dev_required
def api_throughput():
    return jsonify(telecom_diag.medir_throughput_supabase(
        bytes_objetivo=_bounded_int("bytes", 100_000, 1_024, 1_000_000)
    ))


@telecom_bp.get("/api/dev/telecom/dns")
@_dev_required
def api_dns():
    return jsonify(telecom_diag.medir_dns(host=request.args.get("host")))


@telecom_bp.get("/api/dev/telecom/tls")
@_dev_required
def api_tls():
    return jsonify(telecom_diag.medir_tls_handshake())


@telecom_bp.get("/api/dev/telecom/red")
@_dev_required
def api_red():
    return jsonify(telecom_diag.info_red_local())


@telecom_bp.get("/api/dev/telecom/sqlite")
@_dev_required
def api_sqlite():
    return jsonify(telecom_diag.velocidad_sqlite())


@telecom_bp.get("/api/dev/telecom/full")
@_dev_required
def api_full():
    return jsonify(telecom_diag.diagnostico_completo())


@telecom_bp.get("/api/dev/telecom/metodologia")
@_dev_required
def api_metodologia():
    return jsonify({
        "ok": True,
        "disciplina": "Ingeniería en Telecomunicaciones",
        "capas": {
            "endpoint": "IP local, hostname y plataforma",
            "dns": "tiempo de getaddrinfo y direcciones resueltas",
            "transporte_seguridad": "conexión TCP y negociación TLS",
            "aplicacion": "RTT HTTP, variación, fallos y goodput HTTP",
            "plano_local": "rendimiento e integridad SQLite",
        },
        "unidades": {
            "latencia_jitter": "ms",
            "perdida": "% de solicitudes HTTP fallidas",
            "goodput": "Mbps y KiB/s",
            "sqlite": "operaciones/s",
        },
        "limitaciones": [
            "RTT HTTP no equivale a eco ICMP",
            "fallos HTTP no equivalen exactamente a pérdida física de paquetes",
            "goodput de muestra no equivale a capacidad física del enlace",
            "resultados incluyen radio, red, servidor, TLS y carga del dispositivo",
        ],
    })
