"""Deterministic tests for the telecommunications engineering module."""
from __future__ import annotations

import socket

import pytest

from modules import telecom_diag as diag


class FakeHTTPResponse:
    def __init__(self, data=b"x" * 4096):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.data if size < 0 else self.data[:size]


def test_percentile_and_quality_thresholds():
    assert diag._percentile([], 0.95) == 0
    assert diag._percentile([10], 0.95) == 10
    assert diag._percentile([10, 20, 30], 0.5) == 20
    assert diag.evaluar_calidad(None, None, None)["nivel"] == "sin_datos"
    assert diag.evaluar_calidad(20, 2, 0)["nivel"] == "excelente"
    assert diag.evaluar_calidad(120, 15, 1)["nivel"] == "buena"
    assert diag.evaluar_calidad(180, 20, 1)["nivel"] == "degradada"
    assert diag.evaluar_calidad(500, 80, 10)["nivel"] == "critica"


def test_latency_http_metrics(monkeypatch):
    monkeypatch.setattr(diag, "_supabase_url", lambda: "https://example.supabase.co")
    monkeypatch.setattr(diag, "_supabase_config", lambda: {
        "url": "https://example.supabase.co", "anon_key": "eyJ-test"
    })
    times = iter([0.000, 0.050, 0.100, 0.180, 0.200, 0.310])
    monkeypatch.setattr(diag.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(diag.time, "sleep", lambda *_: None)
    monkeypatch.setattr(diag.urllib.request, "urlopen", lambda *a, **k: FakeHTTPResponse())

    result = diag.medir_latencia_supabase(intentos=3)
    assert result["ok"]
    assert result["metodo"] == "HTTP application RTT (no ICMP)"
    assert result["intentos"] == 3
    assert result["exitosos"] == 3
    assert result["perdida_pct"] == 0
    assert result["latencia_p95_ms"] >= result["latencia_mediana_ms"]
    assert len(result["muestras_ms"]) == 3
    assert "calidad" in result


def test_latency_offline_missing_key_and_failure(monkeypatch):
    monkeypatch.setattr(diag, "_supabase_url", lambda: "")
    assert diag.medir_latencia_supabase()["modo"] == "offline"

    monkeypatch.setattr(diag, "_supabase_url", lambda: "https://example.test")
    monkeypatch.setattr(diag, "_supabase_config", lambda: {"url": "https://example.test"})
    assert "key" in diag.medir_latencia_supabase()["error"].lower()

    monkeypatch.setattr(diag, "_supabase_config", lambda: {
        "url": "https://example.test", "anon_key": "public"
    })
    monkeypatch.setattr(diag.time, "sleep", lambda *_: None)
    monkeypatch.setattr(diag.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    failed = diag.medir_latencia_supabase(intentos=99)
    assert not failed["ok"]
    assert failed["intentos"] == 10
    assert failed["perdida_pct"] == 100


def test_http_goodput_units_and_limits(monkeypatch):
    monkeypatch.setattr(diag, "_supabase_config", lambda: {
        "url": "https://example.test", "anon_key": "public"
    })
    times = iter([10.0, 10.5])
    monkeypatch.setattr(diag.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(diag.urllib.request, "urlopen", lambda *a, **k: FakeHTTPResponse(b"x" * 2048))
    result = diag.medir_throughput_supabase(bytes_objetivo=10)
    assert result["ok"]
    assert result["bytes_objetivo"] == 1024
    assert result["bytes_recibidos"] == 1024
    assert result["throughput_kib_s"] == 2.0
    assert result["throughput_kbps"] > 0
    assert "capacidad física" in result["limitacion"]


def test_dns_success_validation_and_failure(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 0)),
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 0, 0, 0)),
    ])
    times = iter([1.0, 1.025])
    monkeypatch.setattr(diag.time, "perf_counter", lambda: next(times))
    result = diag.medir_dns("example.com")
    assert result["ok"] and len(result["ips_resueltas"]) == 2
    assert result["tiempo_ms"] == 25.0
    assert not diag.medir_dns("https://example.com/path")["ok"]

    monkeypatch.setattr(diag.time, "perf_counter", lambda: 2.0)
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: (_ for _ in ()).throw(socket.gaierror("NXDOMAIN")))
    assert not diag.medir_dns("invalid.example")["ok"]


def test_sqlite_and_complete_offline(monkeypatch):
    sqlite = diag.velocidad_sqlite()
    assert sqlite["ok"]
    assert sqlite["quick_check"] == "ok"
    assert sqlite["ops_por_segundo"] > 0

    monkeypatch.setattr(diag, "_supabase_url", lambda: "")
    monkeypatch.setattr(diag, "info_red_local", lambda: {"ok": True, "hostname": "phone", "ip_local": "10.0.0.2"})
    monkeypatch.setattr(diag, "medir_dns", lambda: {"ok": True, "host": "example", "tiempo_ms": 4, "ip_principal": "1.1.1.1"})
    monkeypatch.setattr(diag, "medir_latencia_supabase", lambda intentos=3: {"ok": False, "error": "offline"})
    monkeypatch.setattr(diag, "medir_throughput_supabase", lambda: {"ok": False, "error": "offline"})
    monkeypatch.setattr(diag, "medir_tls_handshake", lambda: {"ok": False, "error": "offline"})
    monkeypatch.setattr(diag, "velocidad_sqlite", lambda: {"ok": True, "quick_check": "ok", "ops_por_segundo": 5000, "tamano_kb": 50})
    complete = diag.diagnostico_completo()
    assert complete["modo_offline"]
    assert complete["pruebas_totales"] == 6
    text = diag.formato_humano_diagnostico()
    assert "RTT, NO ICMP" in text
    assert "GOODPUT HTTP" in text
    assert "PLANO LOCAL SQLITE" in text


def _developer_client():
    from app import app

    app.config.update(TESTING=True, SECRET_KEY="telecom-test")
    client = app.test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"usuario_id": "dev", "rol": "desarrollador"}
    return client


def test_telecom_blueprint_registered_and_protected():
    from app import app

    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/api/dev/telecom/full" in rules
    assert "/api/dev/telecom/metodologia" in rules
    anonymous = app.test_client()
    assert anonymous.get("/api/dev/telecom/red").status_code == 403


def test_telecom_api_bounds_and_methodology(monkeypatch):
    client = _developer_client()
    captured = {}

    def fake_latency(intentos=5):
        captured["intentos"] = intentos
        return {"ok": True, "intentos": intentos}

    def fake_throughput(bytes_objetivo=100_000):
        captured["bytes"] = bytes_objetivo
        return {"ok": True, "bytes_objetivo": bytes_objetivo}

    monkeypatch.setattr(diag, "medir_latencia_supabase", fake_latency)
    monkeypatch.setattr(diag, "medir_throughput_supabase", fake_throughput)
    assert client.get("/api/dev/telecom/latencia?intentos=999").status_code == 200
    assert captured["intentos"] == 10
    assert client.get("/api/dev/telecom/throughput?bytes=99999999").status_code == 200
    assert captured["bytes"] == 1_000_000
    methodology = client.get("/api/dev/telecom/metodologia").get_json()
    assert methodology["disciplina"] == "Ingeniería en Telecomunicaciones"
    assert any("ICMP" in item for item in methodology["limitaciones"])


def test_developer_ia_dispatches_real_telecom(monkeypatch):
    from ia.handlers_staff import handle_dev

    monkeypatch.setattr(diag, "formato_humano_diagnostico", lambda: "DIAGNOSTICO TELECOM REAL")
    assert handle_dev(None, "diagnostico completo", "Dev") == "DIAGNOSTICO TELECOM REAL"
