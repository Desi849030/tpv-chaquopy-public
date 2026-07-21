"""Contract tests for versioning, browser frontend, and writable secrets."""
from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

import app as app_module
from version import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_public_version_is_consistent():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    gradle = (ROOT / "app" / "build.gradle").read_text(encoding="utf-8")
    assert pyproject["project"]["version"] == __version__
    match = re.search(r'versionName\s+"([^"]+)"', gradle)
    assert match and match.group(1) == __version__


def test_browser_frontend_resolves_without_symlinks():
    frontend = Path(app_module._CARPETA)
    assert frontend.samefile(ROOT / "app" / "src" / "main" / "assets" / "frontend")
    assert (frontend / "templates" / "index.html").is_file()
    client = app_module.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert len(response.get_data()) > 10_000


def test_runtime_secret_uses_writable_data_directory():
    expected = Path(os.environ["TPV_FILES_DIR"]).resolve()
    assert app_module._KEY_FILE.parent.resolve() == expected
    assert app_module._KEY_FILE.is_file()
    assert not (ROOT / "app" / "src" / "main" / "python" / ".tpv_secret_key").exists()


def test_server_host_and_port_are_configurable(monkeypatch):
    monkeypatch.setenv("TPV_HOST", "127.0.0.1")
    monkeypatch.setenv("TPV_PORT", "5099")
    assert app_module._server_settings() == ("127.0.0.1", 5099)
    monkeypatch.setenv("TPV_PORT", "invalid")
    assert app_module._server_settings()[1] == 5000
