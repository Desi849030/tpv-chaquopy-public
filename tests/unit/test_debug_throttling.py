"""Regression checks for non-repetitive offline developer diagnostics."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEBUG_JS = ROOT / "app/src/main/assets/frontend/static/js/app_8.js"


def test_debugger_groups_repeated_messages_and_bounds_memory():
    source = DEBUG_JS.read_text(encoding="utf-8")
    assert "dedupe:     new Map()" in source
    assert "maxBuffer:  200" in source
    assert "windowMs = isConnectivity ? 120000 : 10000" in source
    assert "se agruparon" in source
    assert "while (window._DBG.buffer.length > maxBuffer)" in source


def test_offline_mode_pauses_cloud_checks_and_reduces_polling():
    source = DEBUG_JS.read_text(encoding="utf-8")
    assert "SUPABASE_OFFLINE_PAUSED" in source
    assert "Modo offline: se agrupan los fallos de red" in source
    assert "navigator.onLine ? 6000 : 15000" in source
    assert "setInterval(_dbgRenderRed, 3000)" not in source


def test_debug_clear_resets_deduplication_state():
    source = DEBUG_JS.read_text(encoding="utf-8")
    assert "window._DBG.suprimidos = 0" in source
    assert "window._DBG.dedupe?.clear()" in source
