"""Synchronize curated project documentation into SQLite for offline IA use."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

_LOG = logging.getLogger(__name__)
_MODULE_DIR = Path(__file__).resolve().parent
_PACKAGED_DIR = _MODULE_DIR / "knowledge"
_REPOSITORY_ROOT = _MODULE_DIR.parents[3]

# Public name -> candidates in priority order. Repository files are richer in
# Termux/desktop; packaged copies guarantee a useful offline baseline in APK.
_DOCUMENTS = {
    "README.md": (_REPOSITORY_ROOT / "README.md", _PACKAGED_DIR / "PROJECT_OVERVIEW.md"),
    "DEVELOPER_GUIDE.md": (
        _REPOSITORY_ROOT / "docs" / "DEVELOPER_GUIDE.md",
        _PACKAGED_DIR / "DEVELOPER_GUIDE.md",
    ),
    "ROADMAP_10_10.md": (
        _REPOSITORY_ROOT / "docs" / "ROADMAP_10_10.md",
        _PACKAGED_DIR / "ROADMAP_10_10.md",
    ),
    "ARCHITECTURE.md": (_REPOSITORY_ROOT / "docs" / "ARCHITECTURE.md",),
    "API_REFERENCE.md": (_REPOSITORY_ROOT / "docs" / "API_REFERENCE.md",),
    "BACKEND_MAP.md": (_REPOSITORY_ROOT / "docs" / "BACKEND_MAP.md",),
    "DATABASE_SCHEMA.md": (_REPOSITORY_ROOT / "docs" / "DATABASE_SCHEMA.md",),
    "CONTRIBUTING.md": (_REPOSITORY_ROOT / "docs" / "CONTRIBUTING.md",),
    "CHECKLIST_RELEASE.md": (_REPOSITORY_ROOT / "docs" / "CHECKLIST_RELEASE.md",),
    "CHANGELOG.md": (_REPOSITORY_ROOT / "CHANGELOG.md",),
    "LICENSE": (_REPOSITORY_ROOT / "LICENSE",),
}


def _first_readable(candidates: Iterable[Path]) -> str | None:
    for path in candidates:
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            _LOG.warning("Could not read documentation file %s", path, exc_info=True)
    return None


def sync_documentation(connection) -> int:
    """Create/update the offline documentation table using one DB transaction.

    Returns the number of synchronized documents. Missing optional repository
    documents are ignored because only packaged files are guaranteed in Android.
    """
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS documentacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            contenido TEXT NOT NULL,
            lineas INTEGER NOT NULL DEFAULT 0,
            actualizado TEXT DEFAULT (datetime('now','localtime'))
        )
        """
    )
    synchronized = 0
    for name, candidates in _DOCUMENTS.items():
        content = _first_readable(candidates)
        if content is None:
            continue
        connection.execute(
            """
            INSERT INTO documentacion (nombre, contenido, lineas, actualizado)
            VALUES (?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(nombre) DO UPDATE SET
                contenido=excluded.contenido,
                lineas=excluded.lineas,
                actualizado=excluded.actualizado
            """,
            (name, content, len(content.splitlines())),
        )
        synchronized += 1
    connection.commit()
    return synchronized


def available_document_names(connection) -> list[str]:
    """Return synchronized document names in display order."""
    rows = connection.execute(
        "SELECT nombre FROM documentacion ORDER BY nombre"
    ).fetchall()
    return [row[0] for row in rows]
