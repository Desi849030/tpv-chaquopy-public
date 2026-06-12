"""test_sync_backoff.py — Backoff exponencial en reintentos de sync con Supabase (#15)."""
import os, sys, time
import urllib.error, urllib.request
import pytest

os.environ.setdefault("TPV_TESTING", "1")
os.environ.setdefault("SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "sb_publishable_test")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestBackoff:
    def test_reintenta_en_error_de_red(self, monkeypatch):
        import sync.config_supabase as cfg
        esperas = []
        monkeypatch.setattr(time, "sleep", lambda s: esperas.append(s))
        intentos = {"n": 0}
        def fake(*a, **k):
            intentos["n"] += 1
            raise urllib.error.URLError("rechazada")
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        res = cfg._peticion("https://x.supabase.co/rest/v1/t", reintentos=3, backoff_base=0.01)
        assert res is None
        assert intentos["n"] == 4
        assert len(esperas) == 3
        assert esperas[0] < esperas[-1]

    def test_no_reintenta_error_4xx(self, monkeypatch):
        import sync.config_supabase as cfg
        esperas = []
        monkeypatch.setattr(time, "sleep", lambda s: esperas.append(s))
        intentos = {"n": 0}
        def fake(*a, **k):
            intentos["n"] += 1
            raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        res = cfg._peticion("https://x.supabase.co/rest/v1/t", reintentos=3)
        assert res is None
        assert intentos["n"] == 1
        assert len(esperas) == 0
